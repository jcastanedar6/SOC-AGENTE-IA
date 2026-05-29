import pytest

from app.agent.skills.incident_classification import IncidentClassificationSkill


@pytest.fixture
def sample_anomaly():
    return {
        "event_id": 1,
        "attack_type": "sql_injection",
        "severity": "critical",
        "source_ip": "10.0.0.1",
        "target_server": "web-01",
    }


@pytest.fixture
def sample_anomalies(sample_anomaly):
    return [sample_anomaly]


@pytest.fixture
def skill(mock_llm):
    return IncidentClassificationSkill(mock_llm)


@pytest.mark.asyncio
async def test_classification_with_llm(mock_llm, sample_anomalies):
    """Mock returns array JSON for batch classification."""
    mock_llm.complete.return_value = (
        '[{"severity": "high", "attack_category": "intrusión", "confidence": 0.9, '
        '"summary": "test", "recommended_action": "block"}]'
    )
    skill = IncidentClassificationSkill(mock_llm)
    result = await skill.execute({"anomalies": sample_anomalies, "rag_context": ""})
    classifications = result["classifications"]
    assert len(classifications) == 1
    assert classifications[0]["severity"] == "high"
    assert classifications[0]["confidence"] == 0.9
    assert classifications[0]["anomaly"] == sample_anomalies[0]


@pytest.mark.asyncio
async def test_classification_with_rag_context(mock_llm, sample_anomalies):
    mock_llm.complete.return_value = (
        '[{"severity": "high", "attack_category": "intrusión", "confidence": 0.9, '
        '"summary": "test", "recommended_action": "block"}]'
    )
    skill = IncidentClassificationSkill(mock_llm)
    rag = "1. [SQL_INJECTION | critical] Incidente previo en web-01"
    result = await skill.execute({"anomalies": sample_anomalies, "rag_context": rag})
    assert len(result["classifications"]) == 1
    call_args = mock_llm.complete.call_args[0][0]
    assert "Incidente previo" in call_args


@pytest.mark.asyncio
async def test_rule_based_fallback_on_llm_failure(mock_llm_fallback, sample_anomalies):
    skill = IncidentClassificationSkill(mock_llm_fallback)
    result = await skill.execute({"anomalies": sample_anomalies, "rag_context": ""})
    classifications = result["classifications"]
    assert len(classifications) == 1
    assert classifications[0]["severity"] == "critical"
    assert classifications[0]["attack_category"] == "intrusión"
    assert classifications[0]["confidence"] == 0.6


@pytest.mark.asyncio
async def test_empty_anomalies(mock_llm):
    skill = IncidentClassificationSkill(mock_llm)
    result = await skill.execute({"anomalies": [], "rag_context": ""})
    assert result["classifications"] == []


@pytest.mark.asyncio
async def test_rule_based_all_attack_types(mock_llm_fallback, sample_anomalies):
    skill = IncidentClassificationSkill(mock_llm_fallback)
    attacks = [
        {"attack_type": "sql_injection", "expected": "critical"},
        {"attack_type": "command_injection", "expected": "critical"},
        {"attack_type": "brute_force", "expected": "high"},
        {"attack_type": "xss", "expected": "high"},
        {"attack_type": "port_scan", "expected": "medium"},
        {"attack_type": "path_traversal", "expected": "medium"},
        {"attack_type": "resource_exhaustion", "expected": "high"},
        {"attack_type": "unknown_type", "expected": "medium"},
    ]
    for atk in attacks:
        result = await skill.execute({"anomalies": [{"attack_type": atk["attack_type"], "severity": "medium"}], "rag_context": ""})
        assert result["classifications"][0]["severity"] == atk["expected"], f"Failed for {atk['attack_type']}"


@pytest.mark.asyncio
async def test_prompt_structure(mock_llm, sample_anomalies):
    skill = IncidentClassificationSkill(mock_llm)
    prompt = skill._build_batch_prompt(sample_anomalies, "contexto histórico")
    assert "analista SOC" in prompt
    assert "sql_injection" in prompt
    assert "10.0.0.1" in prompt
    assert "contexto histórico" in prompt


@pytest.mark.asyncio
async def test_malformed_json_falls_back(skill, sample_anomaly):
    """When batch JSON is invalid, falls back to rule-based."""
    skill.llm.complete.return_value = "not json at all"
    result = await skill.execute({"anomalies": [sample_anomaly], "rag_context": ""})
    assert result["classifications"][0]["severity"] == "critical"
    assert result["classifications"][0]["confidence"] == 0.6
