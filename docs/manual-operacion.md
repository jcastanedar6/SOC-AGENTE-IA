# Manual de Operación — Agente SOC

## Índice

1. [Primeros pasos](#1-primeros-pasos)
2. [Arranque y parada del sistema](#2-arranque-y-parada)
3. [Interfaz web — tour guiado](#3-interfaz-web)
4. [Autenticación y acceso](#4-autenticación)
5. [Operación del agente](#5-operación-del-agente)
6. [Monitoreo y lectura de resultados](#6-monitoreo)
7. [Simulador y datos de prueba](#7-simulador)
8. [API REST — referencia rápida](#8-api-rest)
9. [Mantenimiento y recuperación](#9-mantenimiento)
10. [Resolución de problemas comunes](#10-troubleshooting)

---

## 1. Primeros pasos

### Requisitos

| Recurso | Mínimo |
|---------|--------|
| CPU | 4 vCPU |
| RAM | 8 GB |
| Disco | 50 GB SSD |
| Software | Docker + Ollama + llama3 |

### Instalación rápida

```bash
# 1. Clonar
git clone https://github.com/jcastanedar6/SOC-AGENTE-IA.git
cd SOC-AGENTE-IA

# 2. Configurar credenciales
cp .env.example backend/.env
# Editar backend/.env con el token de Telegram y otros valores

# 3. Asegurar que Ollama tenga el modelo
ollama pull llama3

# 4. Levantar todo
docker compose up -d

# 5. Esperar a que el backend termine de cargar (~20s la primera vez)
docker compose logs -f backend
# Deberías ver: "Agent scheduler started (interval=60s)"
# y luego logs de ciclos procesando eventos
```

### Verificar que funciona

```bash
# Health check
curl http://localhost:5175/api/v1/health

# Estado del agente
curl -X POST http://localhost:5175/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"socIA"}'

# Frontend
open http://localhost:5175
```

---

## 2. Arranque y parada del sistema

### Iniciar todo

```bash
docker compose up -d
```

Esto levanta 4 contenedores:

| Contenedor | Rol | Puerto |
|-----------|-----|--------|
| `soc-postgres` | Base de datos | — |
| `soc-backend` | API + Agente | 8002 |
| `soc-frontend` | Interfaz web (Nginx) | **5175** |
| `soc-simulator` | Genera eventos de prueba | — |

### Detener todo

```bash
docker compose down
```

Los volúmenes persistentes (PostgreSQL, ChromaDB, modelos) **se conservan**.

### Detener y borrar datos

```bash
docker compose down -v
# ⚠️ BORRA: eventos, incidentes, servidores, historial RAG
```

### Ver estado de los servicios

```bash
docker compose ps
# Name                 Status
# soc-backend          Up About a minute
# soc-frontend         Up About a minute
# soc-postgres         Up About a minute (healthy)
# soc-simulator        Up About a minute
```

### Ver logs

```bash
# Todos
docker compose logs -f

# Solo backend (lo más útil)
docker compose logs -f backend

# Filtrar ciclos del agente
docker compose logs backend | grep -E "Scheduler:|skill|anomaly|incident|classification"
```

---

## 3. Interfaz web — Tour guiado

Abrí **http://localhost:5175** en el navegador.

### Login

```
┌──────────────────────────────┐
│  █ Usuario: socIA            │
│  █ Pregunta: ¿Qué rolén?     │
│  █ Respuesta: las chelas     │
│  █ Teléfono: +50232244536    │
│                              │
│  [Verificar]                 │
│                              │
│  Te llega un código de 6     │
│  dígitos a Telegram →        │
│                              │
│  █ Código: _ _ _ _ _ _      │
│  [Ingresar]                  │
└──────────────────────────────┘
```

El login es de **doble factor**:
1. **Paso 1**: Usuario + respuesta secreta + teléfono autorizado
2. **Paso 2**: Código de 6 dígitos que llega por Telegram

Si no tenés Telegram configurado, los códigos se pueden ver en los logs del backend (modo dev):

```bash
docker compose logs backend | grep "Verification code"
# Verification code for 8749742380: 806712
```

### Dashboard

```
┌─────────────────────────────────────────────────────┐
│ > DASHBOARD                                         │
│ Vista general del sistema SOC                       │
│                                                     │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│
│ │ Total    │ │Incidentes│ │Servidores│ │Sin       ││
│ │ Eventos  │ │          │ │          │ │Procesar  ││
│ │   512    │ │    3     │ │    4     │ │    5     ││
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘│
│                                                     │
│ ┌─────────────────────────────────────────────────┐ │
│ │ ⚡ AGENTE SOC                                   │ │
│ │                               LLM ● conectado   │ │
│ │                               Estado ● Inactivo │ │
│ │                                                 │ │
│ │ Procesados: 12  Incidentes: 3  Notif.: 1       │ │
│ │ Últ. ciclo: 14:32:05                            │ │
│ │                                                 │ │
│ │ [▶ Run Cycle]  [↻ Recargar]                     │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ ┌──────────┐ ┌─────────────────────────────────────┐│
│ │Eventos x │ │ Incidentes recientes               ││
│ │severidad │ │ • SQL Injection en api-01 (CRITICAL)││
│ │  [gráf.] │ │ • Port Scan desde 103.21.244.0     ││
│ └──────────┘ └─────────────────────────────────────┘│
│                                                     │
│ Servidores monitoreados                             │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐               │
│ │web-01│ │db-01 │ │cache │ │api-01│               │
│ │🟢 on │ │🔴 95%│ │⚫ off│ │🟢 on │               │
│ └──────┘ └──────┘ └──────┘ └──────┘               │
└─────────────────────────────────────────────────────┘
```

**El panel del agente** (el bloque con ⚡) es tu herramienta principal:
- **LLM ●** — verde = conectado a Ollama, rojo = caído
- **Estado ●** — verde = procesando, gris = inactivo, rojo = error
- **Run Cycle** — dispara un ciclo manual de análisis
- **Recargar** — refresca el estado del agente

### Páginas disponibles

| Página | Ruta | Qué muestra |
|--------|------|-------------|
| **Dashboard** | `/` | Resumen general + control del agente |
| **Incidents** | `/incidents` | Todos los incidentes, filtro por severidad/estado |
| **Servers** | `/servers` | Servidores monitoreados con métricas |
| **Events** | `/events` | Eventos crudos recibidos |

---

## 4. Autenticación

### Usuarios y credenciales

Todo está configurado vía variables de entorno:

```
AUTH_USERNAME=socIA
AUTH_SECRET_QUESTION=¿Qué rolén?
AUTH_SECRET_ANSWER=las chelas
AUTH_ALLOWED_PHONE_LIST=50232244536,50241707813
```

El sistema usa **JWT** con expiración. Si el token expira, el frontend redirige automáticamente al login.

### Si no funciona el login por Telegram

En desarrollo, podés obtener el código de los logs:

```bash
docker compose logs backend | grep "Verification code"
# Verification code for 8749742380: 560409
```

O directamente desde el contenedor:

```bash
# No recomendado en producción, útil en dev
docker compose exec backend python -c "
from app.auth.codes import _sessions
import json
print(json.dumps({k: {**v, 'code': '***'} for k,v in _sessions.items()}, indent=2, default=str))
"
```

---

## 5. Operación del agente

### El ciclo automático

El agente tiene un **scheduler** que ejecuta `run_cycle` cada **60 segundos**. No necesitás hacer nada — corre solo.

Cada ciclo:

```
1. Fetch eventos sin procesar (hasta 100)
2. Fetch servidores
3. ServerStateSkill → evalúa CPU/memoria/disco
4. EventCorrelationSkill → busca patrones (misma IP, ventana 60s)
5. AnomalyDetectionSkill → detecta:
   - Brute force: >5 auth_failed en ventana
   - Port scan: múltiples puertos desde misma IP
   - SQL Injection: payloads maliciosos
   - XSS: scripts en payloads
6. Si hay anomalías → consulta RAG + clasifica con LLM
7. Si se confirma incidente → crea + notifica por Telegram
8. Marca eventos como procesados
```

### Ciclo manual

Desde el Dashboard, click en **▶ Run Cycle**. O vía API:

```bash
# Con autenticación
curl -X POST http://localhost:5175/api/v1/agent/run \
  -H "Authorization: Bearer <TOKEN>"

# Respuesta:
# {"status":"completed","events_analyzed":12,"anomalies_found":3,"incidents_created":1}
```

### Interpretar el estado del agente

```json
{
  "is_running": false,
  "last_run": "2026-05-27T23:02:32.752615+00:00",
  "events_processed": 512,
  "incidents_created": 8,
  "notifications_sent": 3,
  "errors": []
}
```

| Campo | Significado |
|-------|-------------|
| `is_running` | `true` = el agente está ejecutando un ciclo ahora |
| `last_run` | Timestamp del último ciclo completado |
| `events_processed` | Total de eventos procesados desde que arrancó el contenedor |
| `incidents_created` | Incidentes generados |
| `notifications_sent` | Alertas enviadas por Telegram |
| `errors` | Lista de errores recientes (máx. 50) |

### Si el agente se queda colgado

El ciclo tiene un **timeout global de 120 segundos**. Si excede, se cancela y queda registrado como error. Podés forzar un reinicio:

```bash
docker compose restart backend
```

### Salud del LLM

El indicador en el Dashboard te muestra si el LLM está respondiendo. Si está en rojo, verificá:

```bash
# Ollama está vivo?
curl http://localhost:11434/api/tags

# El backend puede llegar a Ollama?
docker compose exec backend curl -s http://host.docker.internal:11434/api/generate \
  -d '{"model":"llama3","prompt":"ping"}'
```

---

## 6. Monitoreo

### Qué mirar en el Dashboard

1. **LLM indicator** — si está rojo, el agente funciona pero sin razonamiento LLM (usa fallback rule-based)
2. **Estado del agente** — si queda en "Procesando..." por más de 2 minutos, algo anda mal
3. **Eventos sin procesar** — si este número crece sin parar, el agente no está al día
4. **Servidores offline** — si hay servidores en rojo, revisar estado

### Logs útiles

```bash
# Ver el último ciclo completo
docker compose logs backend | grep -E "Scheduler:" | tail -5
# Scheduler: 12 events, 3 anomalies, 1 incidents

# Ver anomalías detectadas
docker compose logs backend | grep "anomaly" | tail -10

# Ver errores
docker compose logs backend | grep -i "error\|exception\|traceback" | tail -10

# Ver notificaciones enviadas
docker compose logs backend | grep "Telegram\|notification" | tail -5
```

### Telegram

Cuando el agente crea un incidente de severidad **critical** o **high**, envía un mensaje como este al chat de Telegram:

```
🚨 INCIDENTE CREADO
Título: SQL Injection en api-01
Severidad: CRITICAL
Tipo: sql_injection
IPs: 185.220.101.47
Recomendación: Bloquear IP y revisar logs de base de datos
```

---

## 7. Simulador y datos de prueba

### El simulador automático

El servicio `soc-simulator` genera **5 eventos aleatorios** cada **120 segundos**. No requiere intervención.

### Inyectar eventos manualmente

```bash
# Sin autenticación (solo para desarrollo)
curl -X POST "http://localhost:5175/api/v1/agent/simulate?count=10"

# Con autenticación
curl -X POST "http://localhost:5175/api/v1/simulator/events/batch?count=5" \
  -H "Authorization: Bearer <TOKEN>"
```

### Sembrar datos iniciales

Si querés empezar con servidores y eventos de ejemplo:

```bash
curl -X POST http://localhost:5175/api/v1/agent/seed \
  -H "Authorization: Bearer <TOKEN>"

# Respuesta:
# {"servers_created":4,"events_created":14,"message":"Seeded 4 servers and 14 events"}
```

Esto crea:
- **4 servidores**: web-01, db-01, cache-01, api-01
- **14 eventos**: brute force, port scan, SQL injection, XSS

### Tipos de ataque simulados

| Tipo | Severidad | Descripción |
|------|-----------|-------------|
| `auth_failed` | medium | Intentos de login fallidos (brute force) |
| `port_scan` | low | Escaneo de puertos |
| `sql_injection` | critical | Inyección SQL en endpoints |
| `xss` | high | Cross-site scripting |
| `access` | low | Accesos internos |

---

## 8. API REST — Referencia rápida

Todas las rutas van contra `http://localhost:5175/api/v1/`. Las rutas marcadas con 🔒 requieren autenticación (Bearer token).

### Autenticación

```bash
# Paso 1: login
POST /auth/login
{"username":"socIA"}
→ {"question":"¿Qué rolén?"}

# Paso 2: verificar (envía código por Telegram)
POST /auth/verify
{"answer":"las chelas","phone":"50232244536"}
→ {"session_id":"abc...","message":"Código enviado"}

# Paso 3: confirmar (recibe JWT)
POST /auth/confirm
{"session_id":"abc...","code":"123456"}
→ {"token":"eyJ...","user":"socIA"}
```

### Agente 🔒

```bash
GET  /agent/status        # Estado actual del agente
POST /agent/run           # Ejecutar ciclo manual
GET  /agent/llm/health    # Salud del LLM
POST /agent/seed          # Sembrar datos de prueba
```

### Eventos 🔒

```bash
GET  /events              # Listar eventos (?limit=10, ?status=open)
GET  /events/:id          # Ver evento
GET  /events/stats        # Estadísticas (total, por severidad, por tipo)
POST /events              # Crear evento manual
DELETE /events/:id        # Eliminar evento
```

### Incidentes 🔒

```bash
GET  /incidents           # Listar (?limit=10, ?severity=critical)
GET  /incidents/:id       # Ver detalle
PATCH /incidents/:id      # Actualizar (cambiar status, severidad)
DELETE /incidents/:id     # Eliminar
```

### Servidores 🔒

```bash
GET  /servers             # Listar todos
POST /servers             # Registrar servidor manual
PATCH /servers/:id        # Actualizar métricas
```

### Simulador (sin auth, solo dev)

```bash
POST /agent/simulate?count=5     # Generar eventos aleatorios
POST /simulator/events/batch?count=5  # Batch de eventos
```

### Health (sin auth)

```bash
GET /health
→ {"status":"online","agent":"Agente SOC","version":"1.0.0"}
```

---

## 9. Mantenimiento y recuperación

### Backup de la base de datos

```bash
docker compose exec postgres pg_dump -U soc_user -d soc_agent > backup_$(date +%Y%m%d).sql
```

### Restaurar base de datos

```bash
cat backup_20260529.sql | docker compose exec -T postgres psql -U soc_user -d soc_agent
```

### Limpiar eventos viejos

```bash
docker compose exec backend python -c "
from app.db.session import SessionLocal
from app.models.event import Event
from datetime import datetime, timedelta, UTC
db = SessionLocal()
deleted = db.query(Event).filter(Event.created_at < datetime.now(UTC) - timedelta(days=7)).delete()
db.commit()
db.close()
print(f'Deleted {deleted} old events')
"
```

### Reconstruir ChromaDB desde cero

```bash
docker compose down
docker volume rm agente-soc_chroma_data agente-soc_chroma_onnx_cache
docker compose up -d
# Los incidentes se re-indexan cuando el agente los procese de nuevo
```

### Actualizar el modelo LLM

```bash
# En docker-compose.yml, cambiar OPENCODE_MODEL
# Ej: OPENCODE_MODEL=llama3.1
# Luego reiniciar
docker compose up -d --build backend
```

---

## 10. Troubleshooting

### "Token inválido" en todas las requests

El JWT expiró. Hacé login de nuevo desde el frontend.

### El frontend carga pero todo dice "Sin datos"

El backend puede estar arrancando todavía (modelos de embedding tardan ~20s la primera vez). Esperá y recargá.

### Error "502 Bad Gateway" en el frontend

El backend no está listo. Verificá:

```bash
docker compose logs backend | tail -20
```

### El agente no procesa eventos

Verificá que el scheduler esté corriendo:

```bash
docker compose logs backend | grep "scheduler"
# Deberías ver "Agent scheduler started (interval=60s)"
```

Si no aparece, revisá `main.py` -> `startup_event()`.

### El LLM no responde

```bash
# 1. Ollama está vivo?
curl http://localhost:11434/api/tags

# 2. El modelo está descargado?
ollama list

# 3. El backend puede alcanzarlo?
docker compose exec backend curl -s http://host.docker.internal:11434/api/generate \
  -d '{"model":"llama3","prompt":"ping"}' | head -c 200
```

### El simulador no genera eventos

```bash
docker compose logs simulator
# Si ves errores de conexión, puede que el backend no esté listo
# Si no ves nada, el scheduler del simulador está esperando
```

### Error "ChromaDB telemetry" en logs

Es un warning conocido de ChromaDB 0.5.23 con Python 3.14. No afecta el funcionamiento.

### Se llenó el disco

Los volúmenes más grandes son:

| Volumen | Tamaño típico | Limpieza |
|---------|--------------|----------|
| `pgdata` | Variable | `docker compose down -v` |
| `chroma_data` | ~100 MB | `docker compose down -v` |
| `chroma_onnx_cache` | ~79 MB (modelo ONNX) | `docker compose down -v` |
| `huggingface_cache` | ~90 MB (modelo embeddings) | `docker compose down -v` |

### Resumen de comandos de emergencia

```bash
# 1. Ver qué está pasando
docker compose ps
docker compose logs --tail=50 backend

# 2. Reiniciar un servicio
docker compose restart backend

# 3. Reconstruir desde cero (sin borrar datos)
docker compose up -d --build

# 4. Reset total (borra TODO)
docker compose down -v

# 5. Entrar al backend
docker compose exec backend bash
```
