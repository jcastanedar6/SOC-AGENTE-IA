# API Reference — Agente SOC

Base URL: `http://localhost:8002/api/v1`

## Eventos (`/events`)

### GET /events
Lista eventos con filtros y paginación.

**Query params:** `severity`, `event_type`, `processed` (bool), `skip`, `limit`

```bash
curl "http://localhost:8002/api/v1/events/?severity=high&processed=false&limit=10"
```

### GET /events/{id}
Obtener un evento por ID.

### GET /events/stats
Estadísticas globales de eventos.

```json
{
  "total": 150,
  "by_severity": {"low": 80, "medium": 40, "high": 20, "critical": 10},
  "by_type": {"auth_failed": 50, "access": 70, "port_scan": 30},
  "unprocessed": 12
}
```

### POST /events
Crear un nuevo evento.

```json
{
  "event_type": "auth_failed",
  "source_ip": "10.0.0.100",
  "target_server": "web-01",
  "severity": "high",
  "raw_data": {"message": "SSH brute force detected"}
}
```

### DELETE /events/{id}
Eliminar un evento.

---

## Incidentes (`/incidents`)

### GET /incidents
Lista incidentes. Filtros: `status` (open|investigating|resolved), `severity`.

### GET /incidents/{id}
Obtener detalle de incidente.

### POST /incidents
Crear incidente manualmente.

### PATCH /incidents/{id}
Actualizar incidente (status, severity, description, recommendation).

```json
{
  "status": "resolved",
  "recommendation": "IP bloqueada en firewall"
}
```

### DELETE /incidents/{id}
Eliminar un incidente.

---

## Servidores (`/servers`)

### GET /servers
Lista todos los servidores registrados.

### POST /servers
Registrar un nuevo servidor.

```json
{
  "hostname": "web-02",
  "ip_address": "192.168.1.15",
  "role": "web",
  "os": "Ubuntu 22.04",
  "status": "online",
  "cpu_usage": 45.0,
  "memory_usage": 60.0,
  "disk_usage": 50.0
}
```

### PATCH /servers/{id}
Actualizar métricas o estado de un servidor.

```json
{
  "cpu_usage": 92.0,
  "status": "online"
}
```

### DELETE /servers/{id}
Eliminar un servidor.

---

## Agente (`/agent`)

### POST /agent/run
Ejecutar el ciclo de análisis completo del agente SOC.

```json
// Respuesta:
{
  "status": "completed",
  "events_analyzed": 25,
  "anomalies_found": 3,
  "incidents_created": 1
}
```

### GET /agent/status
Estado actual del agente.

```json
{
  "is_running": false,
  "last_run": "2026-05-26T03:54:01",
  "events_processed": 150,
  "incidents_created": 12,
  "notifications_sent": 5,
  "errors": []
}
```

### GET /agent/llm/health
Health check del LLM (Ollama).

---

## Sistema

### GET /health
Health check del backend.

```json
{"status": "online", "agent": "Agente SOC", "version": "1.0.0"}
```

### Swagger UI
`http://localhost:8002/api/docs`

### ReDoc
`http://localhost:8002/api/redoc`
