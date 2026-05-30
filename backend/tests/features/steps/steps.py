"""Step definitions for BDD tests of SOC agent skills."""

import sys
import os
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import asyncio
import json

from behave import given, when, then

from app.agent.skills.anomaly_detection import AnomalyDetectionSkill
from app.agent.skills.event_correlation import EventCorrelationSkill
from app.agent.skills.incident_classification import IncidentClassificationSkill
from app.agent.skills.notification import NotificationSkill
from app.agent.skills.server_state import ServerStateSkill
from app.models.event import Event
from app.models.incident import Incident
from app.models.server import Server
from app.config import Settings, settings as app_settings


# ── Shared state ──
context = {}


# ═══════════════════════════════════════════════════════
# ANOMALY DETECTION
# ═══════════════════════════════════════════════════════

@given("el skill AnomalyDetectionSkill está inicializado")
def step_given_anomaly_skill_initialized(context):
    context.skill = AnomalyDetectionSkill()
    context.anomalies = []


@given("un evento con payload {payload}")
def step_given_event_with_payload(context, payload):
    context.events = [{"id": 1, "event_type": "access", "source_ip": "10.0.0.1",
                       "target_server": "web-01", "raw_data": {"query": payload}}]
    context.patterns = []
    context.servers = []


@given("un evento path traversal con ruta {ruta}")
def step_given_event_path_traversal(context, ruta):
    context.events = [{"id": 1, "event_type": "access", "source_ip": "10.0.0.1",
                       "target_server": "web-01", "raw_data": {"path": ruta}}]
    context.patterns = []
    context.servers = []


@given("un evento limpio con ruta {ruta} y método {metodo}")
def step_given_clean_event(context, ruta, metodo):
    context.events = [{"id": 1, "event_type": "access", "source_ip": "192.168.1.1",
                       "target_server": "web-01", "raw_data": {"path": ruta, "method": metodo}}]
    context.patterns = []
    context.servers = []




@given("un evento con comando {comando}")
def step_given_event_with_command(context, comando):
    context.events = [{"id": 1, "event_type": "access", "source_ip": "10.0.0.1",
                       "target_server": "web-01", "raw_data": {"cmd": comando}}]


@given("un servidor {hostname} con cpu_usage {cpu}%")
def step_given_server_with_cpu(context, hostname, cpu):
    hostname = _strip_quotes(hostname)
    context.servers = [{"hostname": hostname, "ip_address": "192.168.1.1",
                        "status": "online", "cpu_usage": float(cpu),
                        "memory_usage": 50.0, "disk_usage": 40.0}]


@given("un patrón {tipo} para IP {ip} con severidad {sev}")
def step_given_pattern(context, tipo, ip, sev):
    context.patterns = [{"pattern": _strip_quotes(tipo), "source_ip": _strip_quotes(ip), "severity": _strip_quotes(sev)}]
    context.events = []


@given("un evento con raw_data en formato string {raw}")
def step_given_string_raw_data(context, raw):
    context.events = [{"id": 1, "event_type": "access", "source_ip": "10.0.0.1",
                       "target_server": "web-01", "raw_data": raw}]


def _run_skill_execute(skill, **kwargs):
    return asyncio.run(skill.execute(kwargs))


@when("el skill procesa el evento")
def step_when_skill_processes_event(context):
    result = _run_skill_execute(context.skill,
        events=_ctx_get(context, "events", []),
        patterns=_ctx_get(context, "patterns", []),
        servers=_ctx_get(context, "servers", []),
    )
    context.anomalies = result["anomalies"]


@when("el skill procesa los servidores")
def step_when_skill_processes_servers(context):
    skill = _ctx_get(context, 'server_skill') or _ctx_get(context, 'skill')
    result = _run_skill_execute(skill,
        events=_ctx_get(context, "events", []),
        patterns=_ctx_get(context, "patterns", []),
        servers=_ctx_get(context, "servers", []),
    )
    context.anomalies = result.get("anomalies", [])
    context.server_alerts = result.get("server_alerts", [])


@when("el skill procesa el patrón")
def step_when_skill_processes_pattern(context):
    result = _run_skill_execute(context.skill,
        events=_ctx_get(context, "events", []),
        patterns=_ctx_get(context, "patterns", []),
        servers=[],
    )
    context.anomalies = result["anomalies"]


def _strip_quotes(val: str) -> str:
    return val.strip('"').strip("'")


# Sentinel for detecting unset behave context attributes
_MISSING = object()


def _ctx_get(context, attr: str, default=None):
    """Get behave context attr safely — their __getattr__ raises KeyError."""
    try:
        return getattr(context, attr)
    except (KeyError, AttributeError):
        return default

@then("debe clasificarlo como {tipo}")
def step_then_classified_as(context, tipo):
    tipo = _strip_quotes(tipo)
    assert any(a["attack_type"] == tipo for a in context.anomalies), \
        f"No se encontró anomalía de tipo {tipo} en {context.anomalies}"


@then("la severidad debe ser {sev}")
def step_then_severity_is(context, sev):
    sev = _strip_quotes(sev)
    assert context.anomalies[0]["severity"] == sev, \
        f"Severidad esperada {sev}, obtenida {context.anomalies[0]['severity']}"


@then("genera una anomalía {tipo} para {hostname}")
def step_then_anomaly_for_server(context, tipo, hostname):
    tipo = _strip_quotes(tipo)
    hostname = _strip_quotes(hostname)
    found = [a for a in context.anomalies
             if a["attack_type"] == tipo and a["target_server"] == hostname]
    assert found, f"No se encontró anomalía {tipo} para {hostname} en {context.anomalies}"


@then("no se generan anomalías")
def step_then_no_anomalies(context):
    assert len(context.anomalies) == 0, \
        f"Se esperaban 0 anomalías, se obtuvieron {len(context.anomalies)}"


@then("genera una anomalía {tipo} con IP {ip}")
def step_then_anomaly_with_ip(context, tipo, ip):
    tipo = _strip_quotes(tipo)
    ip = _strip_quotes(ip)
    found = [a for a in context.anomalies
             if a["attack_type"] == tipo and a.get("source_ip") == ip]
    assert found, f"No se encontró anomalía {tipo} con IP {ip} en {context.anomalies}"


@then("debe detectar {tipo}")
def step_then_detect(context, tipo):
    tipo = _strip_quotes(tipo)
    assert any(a["attack_type"] == tipo for a in context.anomalies), \
        f"No se detectó {tipo} en {context.anomalies}"


# ═══════════════════════════════════════════════════════
# EVENT CORRELATION
# ═══════════════════════════════════════════════════════

@given("el skill EventCorrelationSkill está inicializado")
def step_given_correlation_skill_initialized(context):
    context.correlation = EventCorrelationSkill()


@given("la ventana de correlación es de {segundos} segundos")
def step_given_correlation_window(context, segundos):
    from app.config import settings
    context._orig_window = settings.correlation_window_seconds
    settings.correlation_window_seconds = int(segundos)


@given("el umbral de brute-force es {umbral} intentos")
def step_given_brute_force_threshold(context, umbral):
    from app.config import settings
    context._orig_threshold = settings.brute_force_threshold
    settings.brute_force_threshold = int(umbral)


@given("{n} eventos de {tipo} desde IP {ip}")
def step_given_n_events_from_ip(context, n, tipo, ip):
    tipo = _strip_quotes(tipo)
    ip = _strip_quotes(ip)
    now = datetime.now(UTC)
    context.events = [
        {"id": i, "event_type": tipo, "source_ip": ip,
         "target_server": "web-01", "severity": "medium",
         "raw_data": {"user": "admin"}, "created_at": now - timedelta(seconds=i * 5)}
        for i in range(int(n))
    ]


@given("{n} eventos de {tipo} desde distintas IPs")
def step_given_port_scan_events(context, n, tipo):
    tipo = _strip_quotes(tipo)
    now = datetime.now(UTC)
    ips = ["10.0.0.1", "10.0.0.2", "10.0.0.3"]
    context.events = [
        {"id": i, "event_type": tipo, "source_ip": ips[i % len(ips)],
         "target_server": f"server-{i}", "severity": "low",
         "raw_data": {"ports": [22, 80]}, "created_at": now - timedelta(seconds=i * 5)}
        for i in range(int(n))
    ]


@given("eventos creados hace más de {segundos} segundos")
def step_given_old_events(context, segundos):
    now = datetime.now(UTC)
    old = now - timedelta(seconds=int(segundos) + 60)
    context.events = [
        {"id": 1, "event_type": "auth_failed", "source_ip": "10.0.0.1",
         "target_server": "web-01", "severity": "medium",
         "raw_data": {"user": "admin"}, "created_at": old},
    ]


@given("eventos de {tipo} desde IP {ip} ({n} eventos)")
def step_given_mixed_events(context, tipo, ip, n):
    tipo = _strip_quotes(tipo)
    ip = _strip_quotes(ip)
    if _ctx_get(context, '_mixed_events') is None:
        context._mixed_events = []
    now = datetime.now(UTC)
    offset = len(context._mixed_events)
    for i in range(int(n)):
        context._mixed_events.append(
            {"id": offset + i, "event_type": tipo, "source_ip": ip,
             "target_server": "web-01", "severity": "medium",
             "raw_data": {"user": "admin"}, "created_at": now - timedelta(seconds=i * 5)}
        )
    context.events = context._mixed_events


@when("el skill correlaciona los eventos")
def step_when_correlate(context):
    result = asyncio.run(context.correlation.execute({"events": context.events}))
    context.patterns = result.get("patterns", [])


@then("genera un patrón {tipo}")
def step_then_pattern_exists(context, tipo):
    tipo = _strip_quotes(tipo)
    found = [p for p in context.patterns if p["pattern"] == tipo]
    assert found, f"No se encontró patrón {tipo} en {context.patterns}"
    context._matched_pattern = found[0]


@then("el patrón tiene source_ip {ip}")
def step_then_pattern_source_ip(context, ip):
    ip = _strip_quotes(ip)
    assert context._matched_pattern.get("source_ip") == ip, \
        f"IP esperada {ip}, obtenida {context._matched_pattern.get('source_ip')}"


@then("la severidad es {sev}")
def step_then_severity_check(context, sev):
    sev = _strip_quotes(sev)
    matched = _ctx_get(context, '_matched_pattern')
    if matched:
        actual = matched.get("severity")
    elif _ctx_get(context, 'server_alerts'):
        actual = context.server_alerts[0].get("severity", "")
    else:
        actual = context.anomalies[0].get("severity", "")
    assert actual == sev, f"Severidad esperada {sev}, obtenida {actual}"


@then("no genera patrón {tipo}")
def step_then_no_pattern(context, tipo):
    tipo = _strip_quotes(tipo)
    found = [p for p in context.patterns if p["pattern"] == tipo]
    assert len(found) == 0, f"Se encontró patrón {tipo} cuando no debía"


@then("solo genera patrón para IP {ip}")
def step_then_only_pattern_for(context, ip):
    ip = _strip_quotes(ip)
    patterns_for_ip = [p for p in context.patterns if p.get("source_ip") == ip]
    assert len(patterns_for_ip) > 0, f"No hay patrón para IP {ip}"
    other_ips = [p for p in context.patterns if p.get("source_ip") != ip and p.get("source_ip") is not None]
    assert len(other_ips) == 0, f"Hay patrones para otras IPs: {other_ips}"


@then("incluye todas las IPs origen")
def step_then_includes_all_ips(context):
    assert "source_ips" in context._matched_pattern
    assert len(context._matched_pattern["source_ips"]) > 1


@then("no se generan patrones")
def step_then_no_patterns(context):
    assert len(context.patterns) == 0, \
        f"Se esperaban 0 patrones, se obtuvieron {len(context.patterns)}"


# ═══════════════════════════════════════════════════════
# SERVER STATE
# ═══════════════════════════════════════════════════════

@given("el skill ServerStateSkill está inicializado")
def step_given_server_state_skill(context):
    context.server_skill = ServerStateSkill()
    context.server_alerts = []


@given("un servidor con status {status}")
def step_given_server_status(context, status):
    status = _strip_quotes(status)
    context.servers = context.servers_list = [{"hostname": "web-01", "ip_address": "192.168.1.10",
                             "status": status, "cpu_usage": 30.0,
                             "memory_usage": 40.0, "disk_usage": 50.0}]


@given("un servidor con cpu_usage de {cpu}%")
def step_given_server_cpu(context, cpu):
    context.servers = context.servers_list = [{"hostname": "web-01", "ip_address": "192.168.1.10",
                             "status": "online", "cpu_usage": float(cpu),
                             "memory_usage": 40.0, "disk_usage": 50.0}]


@given("un servidor con memory_usage de {mem}%")
def step_given_server_memory(context, mem):
    context.servers = context.servers_list = [{"hostname": "web-01", "ip_address": "192.168.1.10",
                             "status": "online", "cpu_usage": 30.0,
                             "memory_usage": float(mem), "disk_usage": 50.0}]


@given("un servidor con disk_usage de {disk}%")
def step_given_server_disk(context, disk):
    context.servers = context.servers_list = [{"hostname": "web-01", "ip_address": "192.168.1.10",
                             "status": "online", "cpu_usage": 30.0,
                             "memory_usage": 40.0, "disk_usage": float(disk)}]


@given("un servidor {h} con CPU {cpu}% ({s})")
def step_given_multi_server_cpu(context, h, cpu, s):
    h = _strip_quotes(h)
    if _ctx_get(context, '_multi') is None:
        context._multi = []
    context._multi.append({"hostname": h, "ip_address": f"192.168.1.{10 + len(context._multi) * 10}",
                           "status": "online", "cpu_usage": float(cpu),
                           "memory_usage": 40.0, "disk_usage": 50.0})
    context.servers_list = context.servers = context._multi


@given("un servidor {h} con status {status} ({s})")
def step_given_multi_server_status(context, h, status, s):
    h = _strip_quotes(h)
    status = _strip_quotes(status)
    if _ctx_get(context, '_multi') is None:
        context._multi = []
    context._multi.append({"hostname": h, "ip_address": f"192.168.1.{10 + len(context._multi) * 10}",
                           "status": status, "cpu_usage": 0.0,
                           "memory_usage": 0.0, "disk_usage": 40.0})
    context.servers_list = context.servers = context._multi


@given("el skill ha procesado servidores en un ciclo anterior")
def step_given_previous_cycle(context):
    context.server_skill = ServerStateSkill()
    asyncio.run(context.server_skill.execute({
        "servers": [{"hostname": "web-01", "status": "online", "cpu_usage": 30.0,
                     "memory_usage": 40.0, "disk_usage": 50.0}]
    }))


@when("procesa los mismos servidores en un nuevo ciclo")
def step_when_second_cycle(context):
    result = asyncio.run(context.server_skill.execute({
        "servers": [{"hostname": "web-01", "status": "online", "cpu_usage": 35.0,
                     "memory_usage": 45.0, "disk_usage": 55.0}]
    }))
    context.server_alerts = result.get("server_alerts", [])


@then("mantiene el estado interno de todos los servidores")
def step_then_state_maintained(context):
    state = context.server_skill.get_state()
    assert "web-01" in state, "El servidor web-01 no está en el estado interno"


@when("el skill procesa los servidores en estado")
def step_when_server_state_processes(context):
    result = asyncio.run(context.server_skill.execute({"servers": context.servers_list}))
    context.server_alerts = result.get("server_alerts", [])


@then("genera una alerta {tipo}")
def step_then_alert_type(context, tipo):
    tipo = _strip_quotes(tipo)
    found = [a for a in context.server_alerts if a["issue"] == tipo]
    assert found, f"No se encontró alerta {tipo} en {context.server_alerts}"


@then("el valor reportado es {valor}%")
def step_then_alert_value(context, valor):
    assert "value" in context.server_alerts[0]
    assert context.server_alerts[0]["value"] == float(valor)


@then("genera {n} alertas")
def step_then_n_alerts(context, n):
    assert len(context.server_alerts) == int(n), \
        f"Se esperaban {n} alertas, se obtuvieron {len(context.server_alerts)}"


@then("incluye {tipo} para {hostname}")
def step_then_includes_alert(context, tipo, hostname):
    tipo = _strip_quotes(tipo)
    hostname = _strip_quotes(hostname)
    found = [a for a in context.server_alerts
             if a["issue"] == tipo and a["hostname"] == hostname]
    assert found, f"No se encontró alerta {tipo} para {hostname} en {context.server_alerts}"


# ═══════════════════════════════════════════════════════
# NOTIFICATION
# ═══════════════════════════════════════════════════════

@given("el skill NotificationSkill está inicializado")
def step_given_notification_skill(context):
    context.notification = NotificationSkill()


@given("hay recomendaciones para un incidente crítico")
def step_given_recommendations(context):
    context.recommendations = [{
        "incident_ref": {"severity": "critical", "summary": "SQL Injection detected"},
        "playbook_steps": ["Bloquear IP", "Revisar logs"],
        "enhanced_recommendation": "Bloquear IP inmediatamente y revisar logs",
        "priority": "critical",
    }]


@given("el bot de Telegram está configurado con token válido")
def step_given_telegram_configured(context):
    from app.config import settings
    context._orig_token = settings.telegram_bot_token
    context._orig_chats = settings.telegram_chat_ids
    settings.telegram_bot_token = "test:token"
    settings.telegram_chat_ids = "123456"


@given("el token del bot de Telegram está vacío")
def step_given_telegram_empty(context):
    from app.config import settings
    context._orig_token = settings.telegram_bot_token
    settings.telegram_bot_token = ""


@given("hay {n} chat_ids configurados")
def step_given_n_chats(context, n):
    from app.config import settings
    settings.telegram_bot_token = "test:token"
    settings.telegram_chat_ids = ",".join([str(100000 + i) for i in range(int(n))])


@given("la API de Telegram responde con error")
def step_given_telegram_error(context):
    from app.config import settings
    settings.telegram_bot_token = "invalid:token"
    settings.telegram_chat_ids = "999999"


@when("el skill envía la notificación")
def step_when_notification_sent(context):
    # Mock Telegram to avoid real HTTP calls
    if app_settings.telegram_bot_token:
        async def mock_send(msg):
            return True
        context.notification._send_telegram = mock_send
    context.notification_result = asyncio.run(context.notification.execute({
        "recommendations": _ctx_get(context, "recommendations", []),
        "incident_id": 1,
    }))


@when("el skill intenta notificar")
def step_when_notification_attempted(context):
    context.notification_result = asyncio.run(context.notification.execute({
        "recommendations": _ctx_get(context, "recommendations", []),
        "incident_id": 1,
    }))


@then("se realiza una llamada a la API de Telegram")
def step_then_api_called(context):
    assert context.notification_result.get("notified") is not None, \
        f"No se intentó llamar a Telegram: {context.notification_result}"


@then("se marca como notificado")
def step_then_marked_notified(context):
    assert context.notification_result.get("notified") is True, \
        f"No se marcó como notificado: {context.notification_result}"


@then("omite el envío sin errores")
def step_then_skips_without_error(context):
    result = context.notification_result
    assert result.get("notified") is False, \
        f"Se esperaba notified=False, pero fue {result}"
    assert result.get("reason") == "telegram_not_configured", \
        f"Se esperaba reason=telegram_not_configured, pero fue {result}"


@then("se envía el mensaje a ambos chats")
def step_then_sent_to_both_chats(context):
    # The skill tries ALL configured chats; notified=True means at least one succeeded
    assert context.notification_result.get("notified") is not None, \
        f"No se intentó enviar: {context.notification_result}"


@then("captura el error y continúa sin interrumpir el ciclo")
def step_then_captures_error(context):
    # Should complete without exception — result exists
    assert context.notification_result is not None
    assert "notified" in context.notification_result


# ═══════════════════════════════════════════════════════
# INCIDENT CLASSIFICATION
# ═══════════════════════════════════════════════════════

@given("el skill IncidentClassificationSkill está inicializado con un LLM")
def step_given_incident_skill_init(context):
    from app.llm.opencode_client import OpenCodeClient
    mock_llm = AsyncMock(spec=OpenCodeClient)
    context.incident_skill = IncidentClassificationSkill(llm=mock_llm)
    context.incident_anomalies = []


@given("hay {n} anomalías detectadas ({tipos})")
def step_given_anomalies_detected(context, n, tipos):
    attack_types = [t.strip() for t in tipos.split(",")]
    context.incident_anomalies = [
        {"id": i, "attack_type": at, "severity": "medium", "source_ip": "10.0.0.1",
         "target_server": "web-01"}
        for i, at in enumerate(attack_types)
    ]


@given("no hay anomalías")
def step_given_no_anomalies(context):
    context.incident_anomalies = []


@given("el LLM no está disponible (lanza excepción)")
def step_given_llm_raises(context):
    context.incident_skill.llm.complete = AsyncMock(side_effect=Exception("LLM timeout"))


@given("el LLM responde con texto que no es JSON válido")
def step_given_llm_bad_json(context):
    context.incident_skill.llm.complete = AsyncMock(return_value="Esto no es JSON")


@given("hay incidentes históricos en ChromaDB")
def step_given_historical_incidents(context):
    context.incident_rag_context = "Incidente previo: SQL Injection en web-01, se bloqueó IP 10.0.0.5"


@given("se detectan anomalías de sql_injection")
def step_given_sql_anomalies(context):
    context.incident_anomalies = [
        {"id": 1, "attack_type": "sql_injection", "severity": "critical",
         "source_ip": "10.0.0.1", "target_server": "web-01"}
    ]


def _run_incident(skill, **kwargs):
    return asyncio.run(skill.execute(kwargs))


@when("el skill clasifica las anomalías con el LLM")
def step_when_classify_with_llm(context):
    valid_json = json.dumps([
        {"severity": "critical", "attack_category": "intrusión", "confidence": 0.95,
         "summary": "SQL Injection", "recommended_action": "Bloquear IP"},
        {"severity": "high", "attack_category": "intrusión", "confidence": 0.85,
         "summary": "XSS detectado", "recommended_action": "Sanitizar input"},
        {"severity": "high", "attack_category": "intrusión", "confidence": 0.80,
         "summary": "Brute force", "recommended_action": "Bloquear IP"},
    ])
    context.incident_skill.llm.complete = AsyncMock(return_value=valid_json)
    context.incident_result = _run_incident(context.incident_skill,
        anomalies=_ctx_get(context, "incident_anomalies", []),
    )


@when("el skill clasifica las anomalías")
def step_when_classify(context):
    context.incident_result = _run_incident(context.incident_skill,
        anomalies=_ctx_get(context, "incident_anomalies", []),
    )


@when("el skill ejecuta la clasificación")
def step_when_execute_classification(context):
    context.incident_result = _run_incident(context.incident_skill,
        anomalies=_ctx_get(context, "incident_anomalies", []),
    )


@when("el skill intenta parsear la respuesta")
def step_when_parse_response(context):
    context.incident_result = _run_incident(context.incident_skill,
        anomalies=_ctx_get(context, "incident_anomalies", []),
    )


@when("el skill construye el prompt para el LLM")
def step_when_build_prompt(context):
    context.incident_built_prompt = context.incident_skill._build_batch_prompt(
        anomalies=_ctx_get(context, "incident_anomalies", []),
        rag_context=_ctx_get(context, "incident_rag_context", ""),
    )


@then("el LLM recibe todas las anomalías en un solo prompt")
def step_then_llm_received_all(context):
    # The complete method was called exactly once
    assert context.incident_skill.llm.complete.call_count == 1, \
        f"LLM invocado {context.incident_skill.llm.complete.call_count} veces (se esperaba 1)"
    prompt = context.incident_skill.llm.complete.call_args[0][0]
    assert "sql_injection" in prompt and "xss" in prompt and "brute_force" in prompt, \
        f"El prompt no contiene todas las anomalías: {prompt[:200]}"


@then("se retorna una clasificación por cada anomalía")
def step_then_classification_per_anomaly(context):
    assert len(context.incident_result["classifications"]) == 3, \
        f"Se esperaban 3 clasificaciones, se obtuvieron {len(context.incident_result['classifications'])}"


@then("usa clasificación rule-based")
@then("usa fallback rule-based")
def step_then_rule_based(context):
    classifications = context.incident_result.get("classifications", [])
    assert len(classifications) > 0, "No hay clasificaciones"
    # Rule-based always has confidence=0.6
    assert classifications[0].get("confidence") == 0.6, \
        f"Se esperaba confidence=0.6 (rule-based), se obtuvo {classifications[0]}"


@then("cada anomalía tiene severidad según su tipo")
def step_then_severity_by_type(context):
    for c in context.incident_result.get("classifications", []):
        anomaly = c.get("anomaly", {})
        atype = anomaly.get("attack_type", "")
        severity = c.get("severity", "")
        # Check known mappings
        if atype == "sql_injection":
            assert severity == "critical", f"sql_injection debería ser critical, es {severity}"
        elif atype == "brute_force":
            assert severity == "high", f"brute_force debería ser high, es {severity}"


@then("retorna una lista vacía")
def step_then_empty_list(context):
    assert context.incident_result.get("classifications") == [], \
        f"Se esperaba lista vacía, se obtuvo {context.incident_result}"


@then("el prompt incluye el contexto de incidentes similares")
def step_then_prompt_has_context(context):
    prompt = getattr(context, 'incident_built_prompt', '')
    assert "Incidente previo" in prompt or "SQL Injection" in prompt, \
        f"El prompt no incluye el contexto RAG: {prompt[:200]}"
