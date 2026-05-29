from datetime import datetime, timedelta, UTC
import pytest

from app.agent.skills.event_correlation import EventCorrelationSkill


@pytest.fixture
def skill():
    return EventCorrelationSkill()


@pytest.mark.asyncio
async def test_brute_force_detected(skill, sample_events):
    result = await skill.execute({"events": sample_events})
    patterns = result["patterns"]

    brute_force = [p for p in patterns if p["pattern"] == "brute_force"]
    assert len(brute_force) == 1
    assert brute_force[0]["source_ip"] == "10.0.0.1"
    assert brute_force[0]["count"] >= 3
    assert brute_force[0]["severity"] == "high"


@pytest.mark.asyncio
async def test_port_scan_campaign_detected(skill, sample_events):
    result = await skill.execute({"events": sample_events})
    patterns = result["patterns"]

    port_scan = [p for p in patterns if p["pattern"] == "port_scan_campaign"]
    assert len(port_scan) == 1
    assert "10.0.0.2" in port_scan[0]["source_ips"]
    assert port_scan[0]["count"] >= 3
    assert port_scan[0]["severity"] == "medium"


@pytest.mark.asyncio
async def test_no_events(skill):
    result = await skill.execute({"events": []})
    assert result["patterns"] == []
    assert result["analyzed_events"] == 0


@pytest.mark.asyncio
async def test_events_outside_window_ignored(skill):
    old = datetime.now(UTC) - timedelta(seconds=7200)
    events = [
        {"id": 1, "event_type": "auth_failed", "source_ip": "10.0.0.1", "created_at": old},
        {"id": 2, "event_type": "auth_failed", "source_ip": "10.0.0.1", "created_at": old},
    ]
    result = await skill.execute({"events": events})
    assert result["patterns"] == []


@pytest.mark.asyncio
async def test_events_without_ip_still_analyzed(skill):
    from datetime import datetime
    events = [
        {"id": 1, "event_type": "port_scan", "created_at": datetime.now(UTC)},
        {"id": 2, "event_type": "port_scan", "created_at": datetime.now(UTC)},
        {"id": 3, "event_type": "port_scan", "created_at": datetime.now(UTC)},
    ]
    result = await skill.execute({"events": events})
    patterns = result["patterns"]
    port_scan = [p for p in patterns if p["pattern"] == "port_scan_campaign"]
    assert len(port_scan) == 1


@pytest.mark.asyncio
async def test_parse_ts_with_string(skill):
    ts = skill._parse_ts("2024-01-15T10:30:00Z")
    assert ts.year == 2024
    assert ts.month == 1
    assert ts.day == 15


@pytest.mark.asyncio
async def test_parse_ts_with_none(skill):
    ts = skill._parse_ts(None)
    assert ts == datetime.min.replace(tzinfo=UTC)
