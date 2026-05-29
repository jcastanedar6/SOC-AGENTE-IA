import json
import re
from typing import Any
from app.agent.skills.base import AgentSkill
from app.llm.opencode_client import OpenCodeClient


class IncidentClassificationSkill(AgentSkill):
    name = "incident_classification"

    def __init__(self, llm: OpenCodeClient):
        self.llm = llm

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        anomalies: list[dict] = context.get("anomalies", [])
        rag_context: str = context.get("rag_context", "")
        # Limit RAG context to avoid huge prompts
        rag_context = rag_context[:1500] if rag_context else ""

        if not anomalies:
            return {"classifications": []}

        # Try LLM first: batch all anomalies in ONE call to save time
        try:
            prompt = self._build_batch_prompt(anomalies, rag_context)
            response = await self.llm.complete(prompt)
            classifications = self._parse_batch_response(response, anomalies)
            if classifications:
                self._log(f"LLM classified {len(classifications)} anomalies")
                return {"classifications": classifications}
        except Exception as e:
            self._warn(f"LLM batch call failed: {e}, using rule-based")

        # Fallback: rule-based for each anomaly
        classifications = [self._rule_based_classification(a) for a in anomalies]
        self._log(f"Rule-based classified {len(classifications)} anomalies")
        return {"classifications": classifications}

    def _build_batch_prompt(self, anomalies: list[dict], rag_context: str) -> str:
        anomaly_lines = []
        for i, a in enumerate(anomalies, 1):
            anomaly_lines.append(
                f"{i}. attack_type={a.get('attack_type')}, severity={a.get('severity')}, "
                f"source_ip={a.get('source_ip', '?')}, target={a.get('target_server', '?')}"
            )

        return f"""Sos un analista SOC experto. Clasificá estas anomalías:

CONTEXTO: {rag_context or "N/A"}

ANOMALÍAS:
{chr(10).join(anomaly_lines)}

Respondé SOLO con un JSON array, un objeto por anomalía:
[
  {{"severity": "high", "attack_category": "intrusión", "confidence": 0.9, "summary": "...", "recommended_action": "..."}},
  ...
]"""

    def _parse_batch_response(self, response: str, anomalies: list[dict]) -> list[dict]:
        match = re.search(r"\[.*\]", response, re.DOTALL)
        if not match:
            return []
        try:
            parsed = json.loads(match.group())
            if not isinstance(parsed, list):
                return []
            # Merge with anomalies
            for i, item in enumerate(parsed):
                if i < len(anomalies):
                    item["anomaly"] = anomalies[i]
            return parsed
        except (json.JSONDecodeError, IndexError):
            return []

    def _parse_response(self, response: str, anomaly: dict) -> dict:
        import json
        import re
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group())
                parsed["anomaly"] = anomaly
                return parsed
            except json.JSONDecodeError:
                pass
        return self._rule_based_classification(anomaly)

    def _rule_based_classification(self, anomaly: dict) -> dict:
        severity_map = {
            "sql_injection": "critical",
            "command_injection": "critical",
            "brute_force": "high",
            "xss": "high",
            "port_scan": "medium",
            "path_traversal": "medium",
            "resource_exhaustion": "high",
        }
        return {
            "severity": severity_map.get(anomaly.get("attack_type", ""), anomaly.get("severity", "medium")),
            "attack_category": "intrusión",
            "confidence": 0.6,
            "summary": f"Actividad sospechosa: {anomaly.get('attack_type')}",
            "recommended_action": "Investigar y bloquear IP origen si corresponde",
            "anomaly": anomaly,
        }
