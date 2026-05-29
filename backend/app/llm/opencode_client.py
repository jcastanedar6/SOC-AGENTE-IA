import asyncio
import httpx
import logging
from app.config import settings

logger = logging.getLogger(__name__)

# Separate timeout for DNS/connect vs total
CONNECT_TIMEOUT = 5.0
TOTAL_TIMEOUT = 60.0


class OpenCodeClient:
    def __init__(self):
        self.base_url = settings.opencode_api_url
        self.model = settings.opencode_model
        self.timeout = settings.opencode_timeout

    async def complete(self, prompt: str, system: str | None = None) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system

        timeout = httpx.Timeout(TOTAL_TIMEOUT, connect=CONNECT_TIMEOUT)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await asyncio.wait_for(
                client.post(f"{self.base_url}/api/generate", json=payload),
                timeout=TOTAL_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")

    async def chat(self, messages: list[dict], system: str | None = None) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        if system:
            payload["system"] = system

        timeout = httpx.Timeout(TOTAL_TIMEOUT, connect=CONNECT_TIMEOUT)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await asyncio.wait_for(
                client.post(f"{self.base_url}/api/chat", json=payload),
                timeout=TOTAL_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
