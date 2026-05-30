# Agente SOC — Spec de Cumplimiento y Stack Tecnológico

**Proyecto:** Agente Inteligente SOC para Detección de Anomalías y Gestión de Incidentes usando Open Code y RAG
**Autor:** Juan Pablo Castañeda
**Metodología:** SDD + BDD + TDD

---

## 1. Resumen del Proyecto

Sistema inteligente que automatiza el razonamiento cognitivo de un analista SOC (Security Operations Center): correlaciona eventos, detecta anomalías, clasifica incidentes con ayuda de un LLM open-source, genera recomendaciones y notifica al analista vía Telegram. Todo orquestado desde un backend Python con FastAPI y visualizado en un dashboard web.

El agente NO es el modelo LLM. El agente es la aplicación Python. El LLM (Open Code) es solo el motor de razonamiento vía API.

---

## 2. Stack Tecnológico — Detalle

### Backend

| Componente | Tecnología | Versión | Propósito |
|------------|-----------|---------|-----------|
| Lenguaje | Python | 3.13 | Runtime principal |
| API Framework | FastAPI | latest | Endpoints REST para frontend y skills |
| ASGI Server | Uvicorn | latest | Servidor ASGI con hot-reload en dev |
| ORM | SQLAlchemy | 2.x | Persistencia de incidentes, eventos, estado |
| Base de datos | PostgreSQL 16 (prod) / SQLite (dev) | — | Almacenamiento relacional |
| Migraciones | Alembic | latest | Control de versiones de esquema BD |
| Validación | Pydantic v2 | latest | Schemas, settings, serialización |
| Tests unitarios | pytest + AsyncMock | latest | 51 tests — TDD por skill |
| Tests BDD | behave | 1.2.6 | 28 escenarios, 5 features |
| Cliente LLM | httpx (AsyncClient) | latest | Comunicación con Open Code vía API |
| Embeddings | sentence-transformers | latest | Vectorización para RAG |
| Vector store | ChromaDB | latest | Búsqueda semántica de incidentes históricos |
| Logging | structlog + logging | stdlib | Logging estructurado |

### Frontend

| Componente | Tecnología | Propósito |
|------------|-----------|-----------|
| Framework | React 18 + Vite | SPA moderna con hot-reload |
| UI Components | Material UI (MUI) | Componentes profesionales |
| Charts | Recharts | Dashboard con gráficos de incidentes |
| HTTP Client | Axios | Comunicación con backend |
| Container | Nginx (multi-stage build) | Static file serving en producción |

### IA y RAG

| Componente | Tecnología | Propósito |
|------------|-----------|-----------|
| LLM | Open Code / Ollama (llama3.2) | Razonamiento y clasificación |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 | Vectorización de texto |
| Vector store | ChromaDB (persistente en `chroma_db/`) | Almacenamiento y búsqueda de incidentes |
| RAG | Implementación propia (retriever + embedder) | Contexto histórico para el LLM |

### Infraestructura

| Componente | Tecnología | Propósito |
|------------|-----------|-----------|
| Contenedores | Docker + Docker Compose | Entorno reproducible |
| Proxy reverso | Nginx | Frontend serving + API proxy |
| Notificaciones | Telegram Bot API | Alertas al analista |
| Simulador | Script Python propio | Generación de eventos SOC sintéticos |

### Pipeline CI

| Componente | Tecnología |
|------------|-----------|
| Control de versiones | Git + GitHub |
| BDD | behave (escenarios Gherkin) |
| TDD | pytest + unittest.mock |
| SDD | OpenSpec / Engram (persistencia de diseño) |

---

## 3. Mapa de Cumplimiento vs. Requisitos

### 3.1 Arquitectura y Diseño

| Requisito | Implementación | Estado |
|-----------|---------------|--------|
| Arquitectura monolítica moderna por capas | FastAPI分层 → API → Service → Skills → DB/LLM | ✅ |
| Skills modulares y desacoplados | 6 skills independientes heredando de `BaseSkill` | ✅ |
| LLM intercambiable | Cliente abstracto vía httpx, configurable por URL | ✅ |
| RAG para contexto histórico | ChromaDB + sentence-transformers + retriever propio | ✅ |
| Separación agente vs. modelo | Backend Python controla flujo; LLM solo razona | ✅ |
| Base de datos relacional | PostgreSQL 16 / SQLite con SQLAlchemy + Alembic | ✅ |
| Contenedorización completa | Docker Compose con backend, frontend, PostgreSQL | ✅ |

### 3.2 Skills del Agente (6 módulos)

| Skill | Función | Tests BDD | Tests TDD |
|-------|---------|-----------|-----------|
| `EventCorrelationSkill` | Correlaciona eventos en ventanas temporales, detecta brute force, port scan | 5 escenarios | ✅ |
| `AnomalyDetectionSkill` | Detecta patrones anómalos (SQLi, XSS, path traversal, command injection, resource exhaustion) | 8 escenarios | ✅ |
| `IncidentClassificationSkill` | Clasifica criticidad vía LLM con fallback rule-based. Usa RAG para contexto histórico | 5 escenarios | ✅ |
| `ServerStateSkill` | Monitorea servidores (CPU, memoria, disco, online/offline) | 6 escenarios | ✅ |
| `RecommendationSkill` | Genera recomendaciones con apoyo de LLM + RAG | — | ✅ |
| `NotificationSkill` | Envía alertas vía Telegram (multi-chat, manejo de errores) | 4 escenarios | ✅ |

### 3.3 Metodologías

| Metodología | Implementación | Métrica |
|-------------|---------------|---------|
| **SDD** (Spec-Driven Development) | Diseño documentado antes de implementar: proposal → spec → design → tasks → apply → verify → archive | Flujo completo por cambio |
| **BDD** (Behavior-Driven Development) | 5 feature files Gherkin con 28 escenarios, ejecutados con behave | 28/28 escenarios pasando, 147 steps |
| **TDD** (Test-Driven Development) | Tests escritos antes de la implementación de cada skill. LLM mockeado con AsyncMock | 51 tests unitarios |

### 3.4 Seguridad

| Requisito | Implementación |
|-----------|---------------|
| Autenticación | JWT con preguntas secretas, 2FA vía Telegram |
| MFA | Código de 6 dígitos por Telegram al login |
| CORS | Configurado en FastAPI para frontend |
| Secrets | Token de Telegram en `.env`, excluido de git |
| Rate limiting | Configurable por endpoint |

### 3.5 Automatización

| Componente | Detalle |
|-----------|---------|
| Ciclo del agente | Automático cada 60s (configurable). Orquesta los 6 skills secuencialmente |
| Simulador de eventos | Genera eventos sintéticos cada 120s. Auto-seed al iniciar |
| Dashboard en vivo | Frontend React con estado del agente, health del LLM, Run Cycle manual |
| Notificaciones automáticas | Telegram al detectar incidentes críticos |

---

## 4. Cobertura de Pruebas

```
BDD (behave) — 28 escenarios, 147 steps
├── anomaly_detection.feature:     8 escenarios (SQLi, XSS, path traversal, 
│                                   command injection, resource exhaustion, 
│                                   limpios, patrones, raw string)
├── event_correlation.feature:     5 escenarios (brute force, threshold, 
│                                   port scan, ventana expirada, multi-IP)
├── incident_classification.feature: 5 escenarios (LLM batch, fallback, 
│                                     sin anomalías, RAG, JSON mal formado)
├── notification.feature:          4 escenarios (envío, sin token, 
│                                   multi-chat, error API)
└── server_state.feature:          6 escenarios (offline, CPU, memoria, 
                                    disco, multi-servidor, tracking)

TDD (pytest) — 51 tests
├── EventCorrelationSkill:    10 tests
├── AnomalyDetectionSkill:    12 tests
├── IncidentClassification:    8 tests
├── ServerStateSkill:          8 tests
├── RecommendationSkill:       5 tests
├── NotificationSkill:         4 tests
└── AgentState:                4 tests
```

---

## 5. Flujo del Sistema

```
[Simulador] → Eventos SOC sintéticos cada 120s
       ↓
[Backend] → Ciclo del agente cada 60s
       ↓
   1. EventCorrelationSkill → Correlaciona eventos en ventanas
   2. AnomalyDetectionSkill → Detecta patrones y anomalías
   3. RAG Retriever → Busca incidentes históricos similares
   4. IncidentClassificationSkill → LLM clasifica con contexto RAG
   5. RecommendationSkill → Genera recomendaciones
   6. NotificationSkill → Telegram si es crítico
       ↓
[Dashboard React] → Estado en vivo, historial, Run Cycle manual
       ↓
[PostgreSQL] → Incidentes, eventos, servidores persistidos
[ChromaDB] → Vectores de incidentes para búsqueda semántica
```

---

## 6. Estructura del Proyecto

```
agente-soc/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI + scheduler
│   │   ├── config.py              # Settings Pydantic
│   │   ├── api/routes/            # Endpoints REST
│   │   ├── agent/
│   │   │   ├── core.py            # Orquestador del agente
│   │   │   ├── state.py           # Estado del agente
│   │   │   └── skills/            # 6 skills modulares
│   │   ├── llm/                   # Cliente Open Code
│   │   ├── rag/                   # ChromaDB + embeddings
│   │   ├── models/                # SQLAlchemy
│   │   ├── schemas/               # Pydantic
│   │   ├── services/              # Lógica de negocio
│   │   └── db/                    # Sesión, migraciones
│   ├── tests/
│   │   ├── unit/                  # 51 tests TDD
│   │   └── features/              # 5 features BDD
│   └── requirements.txt
├── frontend/                      # React + Vite + MUI
├── simulator/                     # Generador de eventos
├── docker-compose.yml
└── docs/
```

---

## 7. Comandos Clave

```bash
# Iniciar todo el sistema
docker compose up --build

# Correr BDD (tests de comportamiento)
cd backend && .venv313/bin/python3 -m behave tests/features/

# Correr TDD (tests unitarios)
cd backend && .venv313/bin/python3 -m pytest tests/unit/ -v

# Ciclo manual del agente vía API
curl -X POST http://localhost:8000/api/agent/cycle

# Ver estado del agente
curl http://localhost:8000/api/agent/state
```

---

## 8. Resultados Actuales

| Métrica | Valor |
|---------|-------|
| Escenarios BDD | 28/28 pasando ✅ |
| Steps BDD | 147/147 pasando ✅ |
| Tests unitarios | 51/51 pasando ✅ |
| Skills implementados | 6/6 |
| Features BDD | 5 |
| Canales de notificación | 1 (Telegram) |
| LLM integrado | Open Code / Ollama |
| RAG funcional | ChromaDB + sentence-transformers |
| Autenticación | JWT + 2FA Telegram |
| Dashboard web | React + MUI |
| Contenedorización | Docker Compose completo |
