import logging

import httpx
from app.config import settings

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot"


async def send_code(chat_id: str, code: str) -> bool:
    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN not set, skipping code send")
        return False

    text = (
        f"🔐 *Código de verificación SOC*\n\n"
        f"Tu código de un solo uso es:\n\n"
        f"`{code}`\n\n"
        f"Válido por 5 minutos. No lo compartas con nadie."
    )

    try:
        url = f"{TELEGRAM_API}{settings.telegram_bot_token}/sendMessage"
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                url,
                json={"chat_id": chat_id.strip(), "text": text, "parse_mode": "Markdown"},
            )
            if response.status_code == 200:
                logger.warning("Verification code for %s: %s", chat_id, code)
                return True
            logger.error("Telegram send failed: %s %s", response.status_code, response.text)
            return False
    except Exception as e:
        logger.error("Telegram send exception: %s", e)
        return False
