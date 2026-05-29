# Skills del Agente SOC

Todos los skills heredan de `AgentSkill` (clase abstracta con método `execute(context)`) y son completamente modulares, testeables e intercambiables.

---

## 1. EventCorrelationSkill

Correlaciona eventos en ventanas temporales para detectar patrones.

**Input:** `{"events": [lista de eventos]}`

**Lógica:**
- Filtra eventos dentro de `correlation_window_seconds` (default 60s)
- Agrupa por IP origen y tipo de evento
- Detecta **brute_force**: ≥5 `auth_failed` desde misma IP
- Detecta **port_scan_campaign**: ≥3 `port_scan` events

**Output:**
```json
{
  "patterns": [
    {"pattern": "brute_force", "source_ip": "10.0.0.1", "count": 5, "severity": "high"},
    {"pattern": "port_scan_campaign", "source_ips": ["10.0.0.2"], "count": 3, "severity": "medium"}
  ]
}
```

---

## 2. AnomalyDetectionSkill

Detecta anomalías mediante firmas de ataque y reglas.

**Input:** `{"events": [...], "patterns": [...], "servers": [...]}`

**Firmas de ataque:**
| Tipo | Detonantes |
|------|-----------|
| `sql_injection` | `' OR`, `UNION SELECT`, `DROP TABLE`, `1=1`, `--`, `xp_cmdshell` |
| `xss` | `<script>`, `javascript:`, `onerror=`, `alert(` |
| `path_traversal` | `../`, `..\\`, `%2e%2e`, `etc/passwd` |
| `command_injection` | `; cat`, `\| ls`, `` `id` ``, `$(whoami)` |

**Reglas adicionales:**
- `resource_exhaustion`: CPU > 90% o MEM > 90%
- Patrones de correlación se convierten en anomalías (brute_force)

**Output:**
```json
{
  "anomalies": [
    {"attack_type": "sql_injection", "severity": "critical", "source_ip": "10.0.0.3"}
  ]
}
```

---

## 3. IncidentClassificationSkill

Clasifica anomalías usando LLM + fallback rule-based.

**Input:** `{"anomalies": [...], "rag_context": "..."}`

**Flujo:**
1. Construye prompt en español con contexto RAG y datos de la anomalía
2. Llama al LLM (Open Code vía Ollama)
3. Si el LLM responde válidamente → parsea JSON con severity, confidence, summary
4. Si falla → fallback rule-based por tipo de ataque

**Fallback rule-based:**
| Ataque | Severidad |
|--------|-----------|
| sql_injection | critical |
| command_injection | critical |
| brute_force | high |
| xss | high |
| resource_exhaustion | high |
| port_scan | medium |
| path_traversal | medium |

**Output:** `{"classifications": [{"severity", "attack_category", "confidence", "summary", "recommended_action", "anomaly"}]}`

---

## 4. ServerStateSkill

Mantiene el estado de servidores en memoria y genera alertas.

**Input:** `{"servers": [lista de servidores]}`

**Alertas por threshold:**
| Condición | Alerta | Severidad |
|-----------|--------|-----------|
| `status == "offline"` | server_offline | critical |
| CPU > 85% | high_cpu | high |
| MEM > 85% | high_memory | high |
| DISK > 90% | disk_full | medium |

**Output:**
```json
{
  "server_alerts": [
    {"hostname": "db-01", "issue": "high_cpu", "severity": "high", "value": 95.0}
  ]
}
```

---

## 5. RecommendationSkill

Genera recomendaciones basadas en playbooks predefinidos + LLM.

**Playbooks disponibles:** `brute_force`, `sql_injection`, `port_scan`, `resource_exhaustion`

**Flujo:**
1. Para cada clasificación, selecciona playbook según `attack_type`
2. Llama al LLM para mejorar la recomendación con lenguaje natural
3. Si el LLM falla, usa los pasos del playbook textualmente
4. También genera recomendaciones para alertas de servidores

**Output:**
```json
{
  "recommendations": [
    {
      "playbook_steps": ["Bloquear IP", "Revisar logs", ...],
      "enhanced_recommendation": "Recomendación generada por LLM...",
      "priority": "critical"
    }
  ]
}
```

---

## 6. NotificationSkill

Envía notificaciones vía Telegram para incidentes críticos/altos.

**Input:** `{"recommendations": [...], "incident_id": 1}`

**Comportamiento:**
- Solo notifica si hay recomendaciones de prioridad `critical` o `high`
- Formatea mensaje en Markdown con severidad, resumen y link al dashboard
- Envía a múltiples chat IDs (configurados en `telegram_chat_ids`)
- Si Telegram no está configurado, loguea warning y devuelve preview

**Output:**
```json
{
  "notified": true,
  "message": "🚨 ALERTA SOC — Incidente Detectado..."
}
```
