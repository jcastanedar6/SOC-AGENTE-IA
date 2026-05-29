from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.agent.core import get_agent
from app.auth.dependencies import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post("/run", summary="Trigger a manual agent analysis cycle")
async def run_agent(db: Session = Depends(get_db)):
    agent = get_agent()
    result = await agent.run_cycle(db)
    return result


@router.get("/status", summary="Get current agent state")
def agent_status():
    agent = get_agent()
    return agent.state.to_dict()


@router.get("/llm/health", summary="Check LLM (Open Code) connectivity")
async def llm_health():
    agent = get_agent()
    is_healthy = await agent.llm.health()
    return {"llm_online": is_healthy, "model": agent.llm.model, "url": agent.llm.base_url}


@router.post("/seed", summary="Seed sample servers and events for testing")
def seed_data(db: Session = Depends(get_db)):
    agent = get_agent()
    result = agent.seed_sample_data(db)
    return result


# ── Endpoints sin auth para el simulador (solo dev) ──

simulator = APIRouter()


@simulator.post("/simulate", summary="Generate random events for simulation (no auth)")
def simulate_events(count: int = Query(5, ge=1, le=20), db: Session = Depends(get_db)):
    agent = get_agent()
    return agent.simulate_random_events(db, count=count)
