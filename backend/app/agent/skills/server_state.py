from typing import Any
from app.agent.skills.base import AgentSkill


class ServerStateSkill(AgentSkill):
    name = "server_state"

    def __init__(self):
        self._state: dict[str, dict] = {}

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        servers: list[dict] = context.get("servers", [])
        for server in servers:
            hostname = server.get("hostname")
            if hostname:
                self._state[hostname] = server

        alerts = []
        for hostname, state in self._state.items():
            if state.get("status") == "offline":
                alerts.append({"hostname": hostname, "issue": "server_offline", "severity": "critical"})
            elif state.get("cpu_usage", 0) > 85:
                alerts.append({"hostname": hostname, "issue": "high_cpu", "severity": "high", "value": state["cpu_usage"]})
            elif state.get("memory_usage", 0) > 85:
                alerts.append({"hostname": hostname, "issue": "high_memory", "severity": "high", "value": state["memory_usage"]})
            elif state.get("disk_usage", 0) > 90:
                alerts.append({"hostname": hostname, "issue": "disk_full", "severity": "medium", "value": state["disk_usage"]})

        self._log(f"Tracking {len(self._state)} servers, {len(alerts)} alerts")
        return {"server_alerts": alerts, "servers_tracked": len(self._state)}

    def get_state(self) -> dict[str, dict]:
        return self._state.copy()
