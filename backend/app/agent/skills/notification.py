import httpx
from typing import Any
from app.agent.skills.base import AgentSkill
from app.config import settings


TELEGRAM_API = "https://api.telegram.org/bot"


class NotificationSkill(AgentSkill):
    name = "notification"

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        recommendations: list[dict] = context.get("recommendations", [])
        incident_id: int | None = context.get("incident_id")

        critical = [r for r in recommendations if r.get("priority") in ("critical", "high")]
        if not critical:
            return {"notified": False, "reason": "no_critical_incidents"}

        message = self._format_message(critical, incident_id)

        if not settings.telegram_bot_token or not settings.telegram_chat_ids:
            self._warn("Telegram not configured — notification skipped")
            return {"notified": False, "reason": "telegram_not_configured", "message_preview": message}

        success = await self._send_telegram(message)
        return {"notified": success, "message": message}


    async def _send_telegram(self, message: str) -> bool:
        sent_any = False
        for chat_id in settings.telegram_chat_id_list:
            try:
                url = f"{TELEGRAM_API}{settings.telegram_bot_token}/sendMessage"
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.post(
                        url,
                        json={
                            "chat_id": chat_id,
                            "text": message,
                            "parse_mode": "Markdown",
                        },
                    )
                    if response.status_code == 200:
                        sent_any = True
                    else:
                        self._warn(f"Telegram send to {chat_id}: HTTP {response.status_code}")
            except Exception as e:
                self._warn(f"Telegram notification failed for {chat_id}: {e}")
        return sent_any

    def _format_message(self, recommendations: list[dict], incident_id: int | None) -> str:
        lines = ["🚨 *ALERTA SOC — Incidente Detectado*\n"]
        if incident_id:
            lines.append(f"📋 Incidente #{incident_id}\n")

        for rec in recommendations[:3]:
            severity = rec.get("priority", "?").upper()
            summary = rec.get("enhanced_recommendation", "Ver detalles en dashboard")
            lines.append(f"⚠️ [{severity}] {summary[:200]}")

        lines.append("\n🖥️ Ver detalles: http://localhost:5175/incidents")
        return "\n".join(lines)


