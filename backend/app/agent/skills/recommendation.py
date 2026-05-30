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

        if classifications:
            try:
                enhanced_batch = await self._enhance_batch_with_llm(classifications)
            except Exception:
                enhanced_batch = {}

            for cls in classifications:
                attack_type = cls.get("anomaly", {}).get("attack_type", "")
                playbook = PLAYBOOKS.get(attack_type, ["Escalar al equipo SOC para análisis manual"])
                cls_key = str(cls.get("anomaly", {}).get("event_id", ""))
                enhanced = enhanced_batch.get(cls_key) or "\n".join(f"• {step}" for step in playbook)

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

        self._log(f"Generated {len(recommendations)} recommendations ({len(classifications)} LLM-batched)")
        return {"recommendations": recommendations}

    async def _enhance_batch_with_llm(self, classifications: list[dict]) -> dict[str, str]:
        import asyncio
        lines = []
        for i, cls in enumerate(classifications, 1):
            eid = cls.get("anomaly", {}).get("event_id", i)
            atype = cls.get("anomaly", {}).get("attack_type", "unknown")
            playbook = PLAYBOOKS.get(atype, ["Escalar al equipo SOC para análisis manual"])
            lines.append(
                f"[{eid}] attack={atype}, severity={cls.get('severity')}, "
                f"summary={cls.get('summary', 'N/A')}, playbook={', '.join(playbook[:3])}"
            )

        prompt = f"""Sos un analista SOC. Generá una recomendación clara y accionable (2-3 oraciones) para CADA incidente listado.

Respondé SOLO con un JSON object donde cada key es el ID del incidente:
{{{{
  "1": "Recomendación para incidente 1...",
  "2": "Recomendación para incidente 2..."
}}}}

INCIDENTES:
{chr(10).join(lines)}"""
        try:
            response = await asyncio.wait_for(self.llm.complete(prompt), timeout=60.0)
            import re, json
            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                result = json.loads(match.group())
                if isinstance(result, dict):
                    return {str(k): str(v) for k, v in result.items()}
        except (asyncio.TimeoutError, Exception) as e:
            self._warn(f"LLM batch recommendation failed: {e}, using playbooks")
        return {}
