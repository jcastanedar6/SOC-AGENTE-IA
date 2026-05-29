import pytest

from app.agent.skills.notification import NotificationSkill


@pytest.fixture
def skill():
    return NotificationSkill()


@pytest.fixture
def critical_recs():
    return [
        {"priority": "critical", "enhanced_recommendation": "Bloquear IP 10.0.0.1 inmediatamente"},
        {"priority": "high", "enhanced_recommendation": "Revisar logs de acceso"},
    ]


@pytest.fixture
def low_recs():
    return [
        {"priority": "low", "enhanced_recommendation": "Monitorear como parte de rutina"},
        {"priority": "medium", "enhanced_recommendation": "Programar revisión semanal"},
    ]


@pytest.mark.asyncio
async def test_notifies_for_critical_incidents(skill, critical_recs):
    result = await skill.execute({"recommendations": critical_recs, "incident_id": 1})
    assert result["notified"] == False
    assert result["reason"] == "telegram_not_configured"
    assert "ALERTA" in result["message_preview"]


@pytest.mark.asyncio
async def test_skips_notification_for_low_priority(skill, low_recs):
    result = await skill.execute({"recommendations": low_recs, "incident_id": 2})
    assert result["notified"] == False
    assert result["reason"] == "no_critical_incidents"


@pytest.mark.asyncio
async def test_format_message_with_incident_id(skill, critical_recs):
    msg = skill._format_message(critical_recs, 42)
    assert "Incidente #42" in msg
    assert "ALERTA SOC" in msg
    assert "Bloquear IP" in msg


@pytest.mark.asyncio
async def test_format_message_without_incident_id(skill, critical_recs):
    msg = skill._format_message(critical_recs, None)
    assert "Incidente #" not in msg
    assert "Incidente Detectado" in msg


@pytest.mark.asyncio
async def test_format_message_truncates_long_text(skill):
    long_recs = [{"priority": "critical", "enhanced_recommendation": "A" * 500}]
    msg = skill._format_message(long_recs, 1)
    assert "A" * 200 in msg
    assert "A" * 201 not in msg


@pytest.mark.asyncio
async def test_telegram_not_configured_returns_preview(skill, critical_recs):
    from app.config import settings
    original_token = settings.telegram_bot_token
    original_ids = settings.telegram_chat_ids
    settings.telegram_bot_token = ""
    settings.telegram_chat_ids = ""

    result = await skill.execute({"recommendations": critical_recs, "incident_id": 1})

    settings.telegram_bot_token = original_token
    settings.telegram_chat_ids = original_ids
    assert result["notified"] == False
    assert result["reason"] == "telegram_not_configured"
    assert "message_preview" in result
