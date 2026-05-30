# Tasks: Agente Inteligente SOC

## Backend

### Configuración Inicial
- [x] Crear proyecto FastAPI con estructura de carpetas
- [x] Configurar Pydantic Settings con variables de entorno
- [x] Configurar SQLAlchemy + PostgreSQL (con SQLite para tests)
- [x] Dockerizar backend con docker-compose

### Modelos de Datos
- [x] Crear modelo Event (event_type, source_ip, target_server, severity, raw_data, processed)
- [x] Crear modelo Incident (title, description, severity, status, attack_type, etc.)
- [x] Crear modelo Server (hostname, ip_address, role, os, status, métricas)
- [x] Crear schemas Pydantic (EventCreate, EventOut, IncidentCreate, etc.)

### Autenticación
- [x] Implementar riddle + verificación por Telegram
- [x] Generar y validar JWT
- [x] Proteger endpoints con dependencia get_current_user
- [x] Manejar sesión expirada con redirect en frontend

### API Endpoints
- [x] CRUD de eventos: GET/POST /events, GET /events/stats, GET/DELETE /events/{id}
- [x] CRUD de incidentes: GET/POST /incidents, PATCH/DELETE /incidents/{id}
- [x] CRUD de servidores: GET/POST /servers, PATCH /servers/{id}
- [x] Endpoints del agente: POST /run, GET /status, GET /llm/health
- [x] Endpoints de simulación: POST /simulate, POST /seed

### Skills del Agente
- [x] Skill base: clase abstracta AgentSkill con logging
- [x] ServerStateSkill: monitoreo de servidores (offline, CPU, MEM, DISK)
- [x] EventCorrelationSkill: detección de patrones (brute-force, port-scan)
- [x] AnomalyDetectionSkill: detección por firmas (SQLi, XSS, path traversal)
- [x] IncidentClassificationSkill: clasificación con LLM + fallback rule-based
- [x] RecommendationSkill: recomendaciones con LLM + fallback playbook
- [x] NotificationSkill: notificaciones por Telegram

### Agente Core (Orquestador)
- [x] Implementar SOCAgent con ciclo de ejecución secuencial
- [x] Scheduler background cada 60s con asyncio
- [x] Timeout de ciclo (300s)
- [x] Manejo de errores y logging
- [x] Singleton pattern para instancia del agente

### RAG (Retrieval Augmented Generation)
- [x] Configurar ChromaDB con persistencia en disco
- [x] Configurar SentenceTransformer (all-MiniLM-L6-v2)
- [x] Función de retrieval con contexto de incidentes históricos
- [x] Indexar incidentes nuevos en ChromaDB al crearlos

### LLM (Ollama)
- [x] Cliente HTTP asíncrono para Ollama
- [x] Timeout configurable (120s)
- [x] Estrategia batch para reducir llamadas
- [x] Fallback determinístico cuando el LLM falla
- [x] Health check endpoint

## Frontend

### Configuración
- [x] Crear proyecto React + Vite
- [x] Configurar React Router (login, dashboard, incidents, servers, events)
- [x] Configurar api.client.js con manejo de autenticación
- [x] Dockerizar frontend con Nginx

### Autenticación
- [x] Página de login con riddle
- [x] Flujo: riddle → respuesta → código Telegram → JWT
- [x] Almacenar token en localStorage
- [x] Redirigir a login si token expira (401)

### Dashboard
- [x] StatCards: eventos totales, procesados, incidentes, servidores
- [x] Sección de servidores con métricas (CPU, MEM, DISK)
- [x] AgentPanel: estado del agente, salud del LLM, botón Run Cycle
- [x] Polling cada 10s para estado del agente

### Páginas CRUD
- [x] Lista de incidentes con filtros y badges de severidad
- [x] Vista detalle de incidente con recomendación
- [x] Lista de servidores con estado y métricas
- [x] Lista de eventos con filtros

## Tests

### Unitarios
- [x] Tests de AnomalyDetectionSkill (SQLi, XSS, path traversal, command injection, resource)
- [x] Tests de EventCorrelationSkill (brute-force threshold, port-scan, ventana tiempo)
- [x] Tests de IncidentClassificationSkill (LLM success, LLM fallback, parsing)
- [x] Tests de RecommendationSkill (playbooks, server alerts)
- [x] Tests de NotificationSkill (Telegram, token vacío)
- [x] Tests de ServerStateSkill (offline, CPU, MEM, DISK)
- [x] Tests de AgentState (reset_cycle, to_dict)

### BDD
- [ ] Feature: Detección de anomalías (SQLi, XSS, resource exhaustion)
- [ ] Feature: Correlación de eventos (brute-force, port-scan)
- [ ] Feature: Clasificación de incidentes (LLM, fallback)
- [ ] Feature: Notificaciones (Telegram, token vacío)
- [ ] Feature: Server state (offline, alerts)

## DevOps
- [x] Docker Compose con todos los servicios
- [x] Nginx como proxy reverso con timeouts ajustados
- [x] Volúmenes persistentes para ChromaDB
- [x] .gitignore configurado (env, db, cache, node_modules)
- [x] Hot-reload en desarrollo (volume mount + --reload)

## Optimizaciones
- [x] Batch LLM calls (classification: 1 call, recommendation: 1 call)
- [x] Timeout de ciclo aumentado a 300s
- [x] Redirect slashes deshabilitado en FastAPI
- [x] Proxy timeouts en Nginx (180s read, 10s connect)
