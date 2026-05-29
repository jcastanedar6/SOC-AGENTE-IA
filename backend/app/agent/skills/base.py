from abc import ABC, abstractmethod
from typing import Any
import logging

logger = logging.getLogger(__name__)


class AgentSkill(ABC):
    name: str = "base_skill"

    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute the skill logic. Returns a result dict."""
        ...

    def _log(self, msg: str) -> None:
        logger.info(f"[{self.name}] {msg}")

    def _warn(self, msg: str) -> None:
        logger.warning(f"[{self.name}] {msg}")
