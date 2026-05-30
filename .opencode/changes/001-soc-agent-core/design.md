# Design: Agente Inteligente SOC

## Arquitectura General

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (React + Vite)                  │
│  Dashboard │ Incidentes │ Servidores │ Eventos │ Login       │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP (JSON) :5175
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                   NGINX (proxy reverso)                       │
│  /api/* → backend:8002  │  /* → frontend estático            │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                BACKEND (FastAPI + Uvicorn)                    │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
│  │  Routes   │  │  Auth     │  │  Agent   │  │    RAG       │ │
│  │  (API)    │  │  (JWT)   │  │  (Core)  │  │  ChromaDB    │ │
│  └────┬─────┘  └──────────┘  └────┬─────┘  └──────────────┘ │
│       │                           │                          │
│       ▼                           ▼                          │
│  ┌──────────┐              ┌──────────────┐                  │
│  │  Models   │              │    Skills    │                  │
│  │  (SQLAlc) │              │  (Strategy)  │                  │
│  └──────────┘              └──────────────┘                  │
└──────────────────────────┬───────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         PostgreSQL    Ollama       ChromaDB
         (:5432)      (:11434)     (./chroma_db)
```

## Patrón de Skills (Strategy)

Cada skill implementa la interfaz `AgentSkill` y se ejecuta secuencialmente:

```
class AgentSkill(ABC):
    name: str
    async def execute(context: dict) -> dict

SOCAgent.run_cycle():
    1. ServerStateSkill      → estado de servidores
    2. EventCorrelationSkill → patrones (brute-force, port-scan)
    3. AnomalyDetectionSkill → anomalías (SQLi, XSS, resource)
    4. IncidentClassificationSkill → clasificación vía LLM + RAG
    5. RecommendationSkill   → recomendaciones vía LLM + playbooks
    6. NotificationSkill     → Telegram
```

## Flujo del Agente (Ciclo)

```
Scheduler (60s)
  │
  ▼
┌─────────────────────────────┐
│ Fetch unprocessed events     │  ← DB query: processed=false
│ Fetch servers                │
└────────────┬────────────────┘
             ▼
┌─────────────────────────────┐
│ ServerStateSkill             │  ← tracking de servidores
│   → server_alerts            │
└────────────┬────────────────┘
             ▼
┌─────────────────────────────┐
│ EventCorrelationSkill        │  ← ventana de 60s
│   → patterns (brute_force)   │
└────────────┬────────────────┘
             ▼
┌─────────────────────────────┐
│ AnomalyDetectionSkill        │  ← firmas en raw_data
│   → anomalies                │  ← CPU/mem > 90%
└────────────┬────────────────┘
             ▼
┌─────────────────────────────┐
│ IncidentClassificationSkill  │  ← LLM batch (1 call)
│   → classifications          │  ← fallback rule-based
│   (con RAG context)          │
└────────────┬────────────────┘
             ▼
┌─────────────────────────────┐
│ RecommendationSkill          │  ← LLM batch (1 call)
│   → recommendations          │  ← fallback playbook
└────────────┬────────────────┘
             ▼
┌─────────────────────────────┐
│ Create Incident + RAG store  │
│ NotificationSkill (Telegram) │
│ Mark events as processed     │
└─────────────────────────────┘
```

## Modelo de Datos

```sql
-- Evento de seguridad
Event:
  id            SERIAL PK
  event_type    VARCHAR(50)    -- auth_failed, sql_injection, xss, port_scan, access
  source_ip     VARCHAR(45)
  target_server VARCHAR(100)
  severity      VARCHAR(20)    -- low, medium, high, critical
  raw_data      JSON
  processed     BOOLEAN (default false)
  created_at    TIMESTAMP

-- Incidente
Incident:
  id              SERIAL PK
  title           VARCHAR(200)
  description     TEXT
  severity        VARCHAR(20)
  status          VARCHAR(20)      -- open, investigating, resolved
  attack_type     VARCHAR(50)
  affected_servers TEXT[] (JSON)
  source_ips      TEXT[] (JSON)
  event_ids       INTEGER[] (JSON)
  recommendation  TEXT
  llm_analysis    TEXT
  notified        CHAR(1) (default 'N')
  created_at      TIMESTAMP
  updated_at      TIMESTAMP
  resolved_at     TIMESTAMP

-- Servidor
Server:
  id            SERIAL PK
  hostname      VARCHAR(100) UNIQUE
  ip_address    VARCHAR(45)
  role          VARCHAR(50)
  os            VARCHAR(100)
  status        VARCHAR(20)       -- online, offline, warning
  cpu_usage     FLOAT
  memory_usage  FLOAT
  disk_usage    FLOAT
  services      JSON
  last_seen     TIMESTAMP
  created_at    TIMESTAMP
```

## Autenticación

```
POST /auth/login          → riddle → {question}
POST /auth/verify         → answer + phone → envía código Telegram
POST /auth/confirm        → session_id + code → {token, user}
```

- JWT con expiración de 480 minutos
- Secret key configurable vía .env
- Endpoints protegidos por dependencia `get_current_user`

## RAG

- Embeddings con `all-MiniLM-L6-v2` (SentenceTransformer)
- Vector store: ChromaDB (persistente en disco)
- Colección: `incidentes_soc`
- Top-K: 5 documentos por consulta
- Se indexan incidentes al crearlos (título, descripción, recomendación)

## LLM

- Endpoint: `http://host.docker.internal:11434/api/generate`
- Modelo: `llama3:latest`
- Timeout: 120s por llamada
- Estrategia: batch (todas las anomalías en un solo prompt)
- Fallback: reglas deterministicas si el LLM falla

## Decisiones Técnicas

| Decisión | Opción elegida | Alternativa | Motivo |
|----------|---------------|-------------|--------|
| LLM | Ollama local | OpenAI API | Privacidad, sin costo recurrente |
| Vector store | ChromaDB | Pinecone, Qdrant | Open source, embedding local, sin dependencias cloud |
| Framework frontend | React + Vite | Next.js, Svelte | Simple, SPA sin SSR necesario |
| Estilo frontend | CSS puro + clases utilitarias | Tailwind, Material UI | Sin dependencias pesadas, control total |
| Pruebas | pytest + behave | unittest, nosetests | pytest es estándar en Python, behave para BDD |
| Base de datos | PostgreSQL | SQLite, MySQL | Madurez, JSONB, full-text search |
| Patrón agente | Skills (Strategy) | Pipeline, Chain | Modular, fácil de extender, testable |

## Estructura del Proyecto

```
backend/
├── app/
│   ├── main.py              ← FastAPI app, scheduler, startup
│   ├── config.py            ← Settings con Pydantic
│   ├── api/routes/          ← Endpoints HTTP
│   │   ├── auth.py
│   │   ├── events.py
│   │   ├── incidents.py
│   │   ├── servers.py
│   │   └── agent.py
│   ├── agent/               ← Lógica del agente
│   │   ├── core.py          ← SOCAgent (orquestador)
│   │   ├── state.py         ← AgentState
│   │   └── skills/          ← Strategy Pattern
│   │       ├── base.py
│   │       ├── event_correlation.py
│   │       ├── anomaly_detection.py
│   │       ├── incident_classification.py
│   │       ├── server_state.py
│   │       ├── recommendation.py
│   │       └── notification.py
│   ├── auth/                ← Telegram, JWT
│   ├── db/session.py        ← SQLAlchemy engine
│   ├── llm/                 ← Cliente Ollama
│   ├── models/              ← SQLAlchemy models
│   ├── rag/                 ← ChromaDB, embedders
│   └── schemas/             ← Pydantic DTOs
├── tests/
│   ├── unit/                ← Tests unitarios
│   ├── features/            ← BDD feature files
│   └── conftest.py          ← Fixtures compartidos
└── docker-compose.yml       ← postgres + backend + frontend

frontend/
├── src/
│   ├── api/client.js        ← Cliente HTTP
│   ├── pages/               ← Dashboard, Login, Incidents, etc.
│   ├── components/          ← StatCards, ServerCard, AgentPanel
│   └── App.jsx              ← Router + Layout
└── nginx.conf               ← Proxy reverso
```
