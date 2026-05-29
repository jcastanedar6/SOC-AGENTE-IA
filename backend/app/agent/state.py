from dataclasses import dataclass, field
from datetime import datetime, UTC


@dataclass
class AgentState:
    is_running: bool = False
    last_run: datetime | None = None
    events_processed: int = 0
    incidents_created: int = 0
    notifications_sent: int = 0
    errors: list[str] = field(default_factory=list)

    def reset_cycle(self):
        self.last_run = datetime.now(UTC)
        self.errors.clear()

    def record_error(self, error: str):
        self.errors.append(f"[{datetime.now(UTC).isoformat()}] {error}")
        if len(self.errors) > 50:
            self.errors = self.errors[-50:]

    def to_dict(self) -> dict:
        return {
            "is_running": self.is_running,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "events_processed": self.events_processed,
            "incidents_created": self.incidents_created,
            "notifications_sent": self.notifications_sent,
            "errors": self.errors,
        }
