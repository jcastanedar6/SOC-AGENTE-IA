# Arquitectura del Agente SOC

## Visión General

Sistema monolítico moderno por capas: Backend Python (FastAPI) como núcleo del agente, Frontend web para visualización, e integración con LLM open-source vía API para razonamiento contextual.

## Diagrama Lógico

```
┌─────────────────────────────────────┐
│  Frontend Web SOC                   │
│  • Dashboard                        │
│  • Gestión de Incidentes            │
│  • Estado de Servidores             │
│  • Visor de Eventos                 │
└──────────────┬──────────────────────┘
               │ HTTP (REST)
┌──────────────▼──────────────────────┐
│  Backend Python (FastAPI)           │
│  ───────────────────────────────    │
│  SOCAgent (orquestador)             │
│  ├── EventCorrelationSkill          │
│  ├── AnomalyDetectionSkill          │
│  ├── IncidentClassificationSkill    │
│  ├── ServerStateSkill               │
│  ├── RecommendationSkill            │
│  └── NotificationSkill              │
│                                      │
│  RAG Engine                          │
│  ├── Embedder (sentence-transformers)│
│  ├── Vector Store (ChromaDB)         │
│  └── Retriever (context builder)     │
└──────────────┬──────────────────────┘
               │ HTTP
┌──────────────▼──────────────────────┐
│  LLM (Ollama / Open Code)           │
│  • Razonamiento contextual          │
│  • Clasificación de incidentes      │
│  • Mejora de recomendaciones        │
└─────────────────────────────────────┘
```

## Stack Tecnológico

| Capa | Tecnología | Propósito |
|------|-----------|-----------|
| **API** | FastAPI | Framework REST |
| **ORM** | SQLAlchemy 2.x | Acceso a datos |
| **BD** | PostgreSQL / SQLite | Persistencia |
| **LLM** | Ollama + Open Code | Razonamiento |
| **Vectores** | ChromaDB + all-MiniLM-L6-v2 | Memoria RAG |
| **Frontend** | React 19 + Vite + Tailwind | Dashboard |
| **Notificaciones** | Telegram Bot API | Alertas |

## Flujo del Agente (run_cycle)

```
1. Fetch eventos sin procesar (BD)
2. Fetch servidores (BD)
3. ServerStateSkill → evaluar estado actual
4. EventCorrelationSkill → correlacionar por IP/tipo
5. AnomalyDetectionSkill → detectar por firmas + patrones
6. Si hay anomalías:
   a. Consultar RAG (ChromaDB) → contexto histórico
   b. IncidentClassificationSkill → LLM clasifica + fallback rule-based
   c. ServerStateSkill → re-evaluación
   d. RecommendationSkill → playbooks + LLM enhancement
   e. Crear Incident (BD)
   f. Indexar incidente en RAG (ChromaDB)
   g. NotificationSkill → Telegram si severity critical/high
7. Marcar eventos como procesados
```

## Estructura de Directorios

```
backend/
├── app/
│   ├── main.py                 # Entry point FastAPI
│   ├── config.py               # Pydantic Settings
│   ├── api/routes/             # Endpoints REST
│   │   ├── events.py
│   │   ├── incidents.py
│   │   ├── servers.py
│   │   └── agent.py
│   ├── agent/
│   │   ├── core.py             # SOCAgent (orquestador)
│   │   ├── state.py            # Estado del agente
│   │   └── skills/             # 6 skills modulares
│   ├── llm/
│   │   └── opencode_client.py  # Cliente Ollama API
│   ├── rag/                    # RAG engine
│   │   ├── embedder.py
│   │   ├── store.py
│   │   └── retriever.py
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic schemas
│   ├── services/               # Capa de servicios
│   └── db/                     # Conexión + sesión
├── tests/                      # Tests TDD/BDD
├── Dockerfile
└── requirements.txt

frontend/
├── src/
│   ├── api/client.js           # Cliente HTTP
│   ├── pages/                  # Dashboard, Incidents, Servers, Events
│   └── components/             # UI reutilizable
├── Dockerfile
└── nginx.conf

simulator/
└── event_generator.py          # Generador de eventos SOC
```

## Principios de Diseño

- **Modularidad**: Cada skill es independiente, intercambiable, testeable
- **Desacoplamiento del LLM**: El agente funciona sin LLM (fallback rule-based)
- **RAG como memoria**: ChromaDB almacena incidentes históricos para contexto futuro
- **El agente decide, el LLM razona**: La decisión final es del backend Python
