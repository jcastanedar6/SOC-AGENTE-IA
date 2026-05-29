from datetime import datetime, timedelta, UTC
from typing import Any
from collections import defaultdict
from app.agent.skills.base import AgentSkill
from app.config import settings


class EventCorrelationSkill(AgentSkill):
    name = "event_correlation"

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        events: list[dict] = context.get("events", [])
        window = settings.correlation_window_seconds

        now = datetime.now(UTC)
        cutoff = now - timedelta(seconds=window)

        recent = [e for e in events if self._parse_ts(e.get("created_at")) >= cutoff]

        by_ip: dict[str, list] = defaultdict(list)
        by_type: dict[str, list] = defaultdict(list)

        for event in recent:
            if event.get("source_ip"):
                by_ip[event["source_ip"]].append(event)
            by_type[event.get("event_type", "unknown")].append(event)

        patterns = []

        for ip, ip_events in by_ip.items():
            auth_fails = [e for e in ip_events if e.get("event_type") == "auth_failed"]
            if len(auth_fails) >= settings.brute_force_threshold:
                patterns.append({
                    "pattern": "brute_force",
                    "source_ip": ip,
                    "count": len(auth_fails),
                    "event_ids": [e["id"] for e in auth_fails],
                    "severity": "high",
                })

        if len(by_type.get("port_scan", [])) >= 3:
            scan_events = by_type["port_scan"]
            patterns.append({
                "pattern": "port_scan_campaign",
                "count": len(scan_events),
                "source_ips": list({e.get("source_ip") for e in scan_events if e.get("source_ip")}),
                "event_ids": [e["id"] for e in scan_events],
                "severity": "medium",
            })

        self._log(f"Correlating {len(recent)} events → {len(patterns)} patterns found")
        return {"patterns": patterns, "analyzed_events": len(recent)}

    def _parse_ts(self, ts: Any) -> datetime:
        if isinstance(ts, datetime):
            if ts.tzinfo is None:
                return ts.replace(tzinfo=UTC)
            return ts
        if isinstance(ts, str):
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return datetime.min.replace(tzinfo=UTC)
