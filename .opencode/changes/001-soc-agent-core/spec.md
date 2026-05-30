# Spec: Agente Inteligente SOC

## Historias de Usuario

### US-01: Autenticación por riddle + Telegram
- **Como** analista SOC
- **Quiero** autenticarme con un riddle y verificación por Telegram
- **Para** acceder al sistema de forma segura sin contraseñas tradicionales

**Escenarios:**

```
DADO que el usuario envía sus credenciales (usuario + respuesta al riddle)
CUANDO la respuesta es correcta
ENTONCES el sistema envía un código de verificación por Telegram al número autorizado
Y el usuario ingresa el código para obtener un JWT

DADO que el usuario ingresa un código de verificación incorrecto
CUANDO el código no coincide
ENTONCES el sistema rechaza la autenticación con error 401

DADO que el usuario tiene un JWT expirado
CUANDO intenta acceder a un endpoint protegido
ENTONCES el sistema responde con 401 y el frontend redirige al login
```

### US-02: Ingesta de eventos de seguridad
- **Como** analista SOC
- **Quiero** recibir eventos de seguridad de múltiples fuentes
- **Para** centralizar el monitoreo

**Escenarios:**

```
DADO que un sistema externo envía un evento POST a /api/v1/events
CUANDO el payload es válido (event_type, source_ip, target_server, severity, raw_data)
ENTONCES el evento se almacena en PostgreSQL con processed=false

DADO que el simulador genera eventos aleatorios
CUANDO se invoca POST /api/v1/agent/simulate?count=N
ENTONCES se crean N eventos con tipos y severidades variadas

DADO que existen eventos sin procesar
CUANDO se consulta GET /api/v1/events/stats
ENTONCES se retorna el total, la distribución por severidad y tipo, y el conteo de no procesados
```

### US-03: Correlación de eventos
- **Como** agente SOC
- **Quiero** correlacionar eventos por IP origen y tipo
- **Para** detectar patrones de ataque (brute-force, port-scan campaigns)

**Escenarios:**

```
DADO que hay N eventos de auth_failed desde la misma IP en la ventana de tiempo
CUANDO N >= brute_force_threshold (configurable)
ENTONCES se genera un patrón "brute_force" con severidad high

DADO que hay 3+ eventos de port_scan
CUANDO se analizan en la ventana de correlación
ENTONCES se genera un patrón "port_scan_campaign" con severidad medium

DADO que los eventos están fuera de la ventana de correlación
CUANDO se ejecuta el skill
ENTONCES no se generan patrones
```

### US-04: Detección de anomalías
- **Como** agente SOC
- **Quiero** detectar anomalías en eventos y servidores
- **Para** identificar ataques activos y problemas de infraestructura

**Escenarios:**

```
DADO un evento con raw_data que contiene firmas SQL injection ("' OR ", "UNION SELECT", etc.)
CUANDO el skill AnomalyDetection analiza el evento
ENTONCES lo clasifica como sql_injection con severidad critical

DADO un evento con raw_data que contiene "<script>" o "javascript:"
CUANDO el skill analiza el evento
ENTONCES lo clasifica como xss con severidad high

DADO un servidor con cpu_usage > 90%
CUANDO el skill analiza los servidores
ENTONCES genera una anomalía resource_exhaustion para ese servidor

DADO un patrón brute_force de la correlación de eventos
CUANDO el skill procesa los patrones
ENTONCES genera una anomalía brute_force con la IP origen
```

### US-05: Clasificación de incidentes con LLM
- **Como** agente SOC
- **Quiero** clasificar las anomalías usando un LLM con contexto RAG
- **Para** obtener análisis inteligente basado en incidentes históricos

**Escenarios:**

```
DADO que hay anomalías detectadas
CUANDO el skill IncidentClassification procesa las anomalías
ENTONCES intenta clasificarlas con el LLM en un batch
Y si el LLM responde, asigna severidad, categoría y resumen

DADO que el LLM no está disponible o falla
CUANDO el skill no obtiene respuesta del LLM
ENTONCES usa clasificación basada en reglas (fallback deterministico)

DADO que hay incidentes históricos en ChromaDB
CUANDO se detectan anomalías
ENTONCES se recupera contexto RAG de incidentes similares
Y se incluye en el prompt del LLM
```

### US-06: Generación de recomendaciones
- **Como** agente SOC
- **Quiero** obtener recomendaciones accionables para cada incidente
- **Para** saber exactamente qué pasos seguir

**Escenarios:**

```
DADO que hay clasificaciones de incidentes
CUANDO el skill Recommendation procesa las clasificaciones
ENTONCES genera recomendaciones usando el LLM con base en playbooks predefinidos

DADO que hay alertas de servidor (offline, CPU alto)
CUANDO el skill procesa las alertas
ENTONCES genera recomendaciones con los pasos del playbook correspondiente

DADO que el LLM falla al generar recomendaciones
CUANDO ocurre un timeout o error
ENTONCES se usa el playbook estático como fallback
```

### US-07: Notificaciones por Telegram
- **Como** analista SOC
- **Quiero** recibir notificaciones de incidentes críticos por Telegram
- **Para** actuar rápidamente sin estar frente al dashboard

**Escenarios:**

```
DADO que se ha creado un incidente nuevo
CUANDO el skill Notification procesa el incidente
ENTONCES envía un mensaje por Telegram al chat configurado
Y marca el incidente como notificado

DADO que el bot de Telegram no está configurado (token vacío)
CUANDO el skill intenta notificar
ENTONCES omite el envío sin errores
```

### US-08: Dashboard en tiempo real
- **Como** analista SOC
- **Quiero** ver el estado del sistema en un dashboard
- **Para** monitorear eventos, incidentes y servidores de un vistazo

**Escenarios:**

```
DADO que el analista inicia sesión
CUANDO accede al dashboard
ENTONCES ve tarjetas con total de eventos, procesados, incidentes y servidores

DADO que hay servidores monitoreados
CUANDO el dashboard carga
ENTONCES se muestran con su estado (online/offline) y métricas (CPU, MEM, DISK)

DADO que el agente está ejecutando un ciclo
CUANDO se consulta el estado
ENTONCES el panel del agente muestra "running" y los indicadores de salud del LLM
```

## Restricciones Técnicas
- Stack: Python 3.13+, FastAPI, React 19, PostgreSQL 16
- LLM local vía Ollama (llama3) para evitar dependencias externas
- RAG con ChromaDB + SentenceTransformer (all-MiniLM-L6-v2)
- Sin WebSockets: polling cada 10s para estado del agente
- Base de datos SQLite para tests, PostgreSQL para producción
