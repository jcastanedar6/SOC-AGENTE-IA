import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import events, incidents, servers, agent, auth, simulator
from app.db.session import create_tables, SessionLocal
from app.agent.core import get_agent
from app.config import settings

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Agente Inteligente SOC — Detección de Anomalías y Gestión de Incidentes",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router, prefix="/api/v1/events", tags=["events"])
app.include_router(incidents.router, prefix="/api/v1/incidents", tags=["incidents"])
app.include_router(servers.router, prefix="/api/v1/servers", tags=["servers"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(agent.router, prefix="/api/v1/agent", tags=["agent"])
app.include_router(agent.simulator, prefix="/api/v1/agent", tags=["simulator"])
app.include_router(simulator.router, prefix="/api/v1/simulator", tags=["simulator"])


async def preload_models():
    """Preload slow models at startup so agent cycles don't hang."""
    logger.info("Preloading embedder model...")
    try:
        from app.rag.embedder import get_embedder
        import time
        start = time.time()
        get_embedder()
        logger.info(f"Embedder model loaded in {time.time()-start:.1f}s")
    except Exception as e:
        logger.warning(f"Embedder preload failed: {e}")

    logger.info("Preloading ChromaDB...")
    try:
        from app.rag.store import get_collection
        get_collection()
        logger.info("ChromaDB initialized")
    except Exception as e:
        logger.warning(f"ChromaDB preload failed: {e}")


async def agent_scheduler():
    """Background task: runs agent analysis cycle periodically."""
    interval = settings.agent_cycle_interval_seconds
    logger.info(f"Agent scheduler started (interval={interval}s)")

    # First run: wait for models to preload first
    await asyncio.sleep(10)

    while True:
        try:
            db = SessionLocal()
            try:
                agent_instance = get_agent()
                result = await agent_instance.run_cycle(db)
                if result.get("status") == "completed" and result.get("events_analyzed", 0) > 0:
                    logger.info(f"Scheduler: {result['events_analyzed']} events, {result.get('anomalies_found', 0)} anomalies, {result.get('incidents_created', 0)} incidents")
                elif result.get("status") == "error":
                    logger.warning(f"Scheduler cycle error: {result.get('error')}")
            finally:
                db.close()
        except Exception as e:
            logger.exception(f"Scheduler error: {e}")
        await asyncio.sleep(interval)


@app.on_event("startup")
async def startup_event():
    create_tables()
    asyncio.create_task(preload_models())
    asyncio.create_task(agent_scheduler())


@app.get("/health", tags=["system"])
def health_check():
    return {"status": "online", "agent": settings.app_name, "version": settings.app_version}
