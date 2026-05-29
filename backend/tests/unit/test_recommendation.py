import pytest

from app.agent.skills.recommendation import RecommendationSkill, PLAYBOOKS


@pytest.fixture
def sample_classifications():
    return [
        {
            "severity": "critical",
            "attack_category": "intrusión",
            "summary": "SQL injection detectada en web-01",
            "anomaly": {"attack_type": "sql_injection"},
        }
    ]


@pytest.mark.asyncio
async def test_playbook_for_attack_type(mock_llm, sample_classifications):
    skill = RecommendationSkill(mock_llm)
    result = await skill.execute({"classifications": sample_classifications, "server_alerts": []})
    recs = result["recommendations"]
    assert len(recs) == 1
    assert "Analizar logs" in str(recs[0]["playbook_steps"])
    assert len(recs[0]["playbook_steps"]) > 0


@pytest.mark.asyncio
async def test_unknown_attack_uses_default_playbook(mock_llm):
    skill = RecommendationSkill(mock_llm)
    classifications = [{"severity": "medium", "anomaly": {"attack_type": "unknown_attack"}}]
    result = await skill.execute({"classifications": classifications, "server_alerts": []})
    recs = result["recommendations"]
    assert "escalar" in recs[0]["playbook_steps"][0].lower()


@pytest.mark.asyncio
async def test_llm_enhancement_applied(mock_llm, sample_classifications):
    skill = RecommendationSkill(mock_llm)
    result = await skill.execute({"classifications": sample_classifications, "server_alerts": []})
    recs = result["recommendations"]
    assert "severity" in recs[0]["enhanced_recommendation"]


@pytest.mark.asyncio
async def test_llm_fallback_on_failure(mock_llm_fallback, sample_classifications):
    skill = RecommendationSkill(mock_llm_fallback)
    result = await skill.execute({"classifications": sample_classifications, "server_alerts": []})
    recs = result["recommendations"]
    assert "•" in recs[0]["enhanced_recommendation"]
    assert "Analizar logs" in recs[0]["enhanced_recommendation"]


@pytest.mark.asyncio
async def test_server_alerts_also_generate_recommendations(mock_llm):
    skill = RecommendationSkill(mock_llm)
    result = await skill.execute({
        "classifications": [],
        "server_alerts": [
            {"hostname": "web-01", "issue": "high_cpu", "severity": "high"},
        ],
    })
    recs = result["recommendations"]
    assert len(recs) == 1
    assert "web-01" in recs[0]["enhanced_recommendation"]


@pytest.mark.asyncio
async def test_priority_matches_classification_severity(mock_llm, sample_classifications):
    skill = RecommendationSkill(mock_llm)
    result = await skill.execute({"classifications": sample_classifications, "server_alerts": []})
    assert result["recommendations"][0]["priority"] == "critical"


@pytest.mark.asyncio
async def test_empty_inputs(mock_llm):
    skill = RecommendationSkill(mock_llm)
    result = await skill.execute({"classifications": [], "server_alerts": []})
    assert result["recommendations"] == []


def test_playbooks_defined():
    assert "brute_force" in PLAYBOOKS
    assert "sql_injection" in PLAYBOOKS
    assert "port_scan" in PLAYBOOKS
    assert "resource_exhaustion" in PLAYBOOKS
