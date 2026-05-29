from typing import Any
from app.agent.skills.base import AgentSkill
from app.config import settings


ATTACK_SIGNATURES = {
    "sql_injection": ["' OR ", "UNION SELECT", "DROP TABLE", "1=1", "--", "xp_cmdshell"],
    "xss": ["<script>", "javascript:", "onerror=", "onload=", "alert("],
    "path_traversal": ["../", "..\\", "%2e%2e", "etc/passwd"],
    "command_injection": ["; cat ", "| ls", "`id`", "$(whoami)"],
}


class AnomalyDetectionSkill(AgentSkill):
    name = "anomaly_detection"

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        events: list[dict] = context.get("events", [])
        patterns: list[dict] = context.get("patterns", [])

        anomalies = []

        for event in events:
            raw = str(event.get("raw_data", "")).lower()
            for attack_type, signatures in ATTACK_SIGNATURES.items():
                if any(sig.lower() in raw for sig in signatures):
                    anomalies.append({
                        "event_id": event.get("id"),
                        "attack_type": attack_type,
                        "severity": "critical" if attack_type in ("sql_injection", "command_injection") else "high",
                        "source_ip": event.get("source_ip"),
                        "target_server": event.get("target_server"),
                    })
                    break

        for server in context.get("servers", []):
            if server.get("cpu_usage", 0) > 90 or server.get("memory_usage", 0) > 90:
                anomalies.append({
                    "event_id": None,
                    "attack_type": "resource_exhaustion",
                    "severity": "high",
                    "source_ip": None,
                    "target_server": server.get("hostname"),
                })

        for pattern in patterns:
            if pattern.get("pattern") == "brute_force":
                anomalies.append({
                    "event_id": None,
                    "attack_type": "brute_force",
                    "severity": pattern.get("severity", "high"),
                    "source_ip": pattern.get("source_ip"),
                    "target_server": None,
                    "pattern_data": pattern,
                })

        self._log(f"Detected {len(anomalies)} anomalies from {len(events)} events")
        return {"anomalies": anomalies}
