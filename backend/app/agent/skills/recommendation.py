from typing import Any
from app.agent.skills.base import AgentSkill
from app.llm.opencode_client import OpenCodeClient


PLAYBOOKS: dict[str, list[str]] = {
    "brute_force": [
        "Bloquear IP origen en firewall",
        "Revisar logs de acceso del servicio afectado",
        "Aumentar umbral de intentos fallidos",
        "Activar autenticación multifactor si no está activa",
        "Notificar al equipo de administración",
    ],
    "sql_injection": [
        "Analizar logs del servidor web y base de datos",
        "Revisar queries ejecutadas en ventana de tiempo del ataque",
        "Aplicar WAF rules para bloquear el patrón detectado",
        "Verificar integridad de datos en tablas afectadas",
        "Parchear aplicación con consultas parametrizadas",
    ],
    "port_scan": [
        "Registrar IP origen en lista de vigilancia",
        "Revisar qué puertos fueron escaneados",
        "Verificar que servicios no necesarios estén cerrados",
        "Configurar alertas en IDS para esa IP",
    ],
    "resource_exhaustion": [
        "Identificar procesos que consumen recursos",
        "Verificar si hay procesos no autorizados",
        "Revisar logs de sistema en el período afectado",
        "Considerar reinicio controlado si persiste",
    ],
}


class RecommendationSkill(AgentSkill):
    name = "recommendation"

    def __init__(self, llm: OpenCodeClient):
        self.llm = llm

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        classifications: list[dict] = context.get("classifications", [])
        server_alerts: list[dict] = context.get("server_alerts", [])

        recommendations = []

        for cls in classifications:
            attack_type = cls.get("anomaly", {}).get("attack_type", "")
            playbook = PLAYBOOKS.get(attack_type, ["Escalar al equipo SOC para análisis manual"])

            try:
                enhanced = await self._enhance_with_llm(cls, playbook)
            except Exception:
                enhanced = "\n".join(f"• {step}" for step in playbook)

            recommendations.append({
                "incident_ref": cls,
                "playbook_steps": playbook,
                "enhanced_recommendation": enhanced,
                "priority": cls.get("severity", "medium"),
            })

        for alert in server_alerts:
            recommendations.append({
                "incident_ref": alert,
                "playbook_steps": PLAYBOOKS.get(alert.get("issue", ""), ["Revisar estado del servidor"]),
                "enhanced_recommendation": f"Atención requerida en {alert.get('hostname')}: {alert.get('issue')}",
                "priority": alert.get("severity", "medium"),
            })

        self._log(f"Generated {len(recommendations)} recommendations")
        return {"recommendations": recommendations}

    async def _enhance_with_llm(self, classification: dict, playbook: list[str]) -> str:
        import asyncio
        prompt = f"""Sos un analista SOC. Dado este incidente y los pasos del playbook, generá una recomendación clara y accionable en 2-3 oraciones.

Incidente: {classification.get("summary", "Incidente de seguridad")}
Severidad: {classification.get("severity")}
Pasos del playbook: {", ".join(playbook[:3])}

Recomendación (2-3 oraciones, tono técnico y directo):"""
        try:
            return await asyncio.wait_for(self.llm.complete(prompt), timeout=30.0)
        except (asyncio.TimeoutError, Exception):
            return "\n".join(f"• {step}" for step in playbook)
