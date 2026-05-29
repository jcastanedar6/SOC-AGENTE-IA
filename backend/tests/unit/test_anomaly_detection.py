import pytest

from app.agent.skills.anomaly_detection import AnomalyDetectionSkill


@pytest.fixture
def skill():
    return AnomalyDetectionSkill()


@pytest.mark.asyncio
async def test_sql_injection_detected(skill, sample_events):
    events = [
        {"id": 10, "event_type": "access", "source_ip": "10.0.0.3", "target_server": "web-01",
         "raw_data": {"query": "' OR 1=1--"}},
    ]
    result = await skill.execute({"events": events, "patterns": [], "servers": []})
    anomalies = result["anomalies"]
    assert len(anomalies) == 1
    assert anomalies[0]["attack_type"] == "sql_injection"
    assert anomalies[0]["severity"] == "critical"


@pytest.mark.asyncio
async def test_xss_detected(skill):
    events = [
        {"id": 11, "event_type": "access", "source_ip": "10.0.0.4", "target_server": "web-01",
         "raw_data": {"payload": "<script>alert('xss')</script>"}},
    ]
    result = await skill.execute({"events": events, "patterns": [], "servers": []})
    anomalies = result["anomalies"]
    assert len(anomalies) == 1
    assert anomalies[0]["attack_type"] == "xss"
    assert anomalies[0]["severity"] == "high"


@pytest.mark.asyncio
async def test_path_traversal_detected(skill):
    events = [
        {"id": 12, "event_type": "access", "source_ip": "10.0.0.5", "target_server": "web-01",
         "raw_data": {"path": "/../../../etc/passwd"}},
    ]
    result = await skill.execute({"events": events, "patterns": [], "servers": []})
    anomalies = result["anomalies"]
    assert len(anomalies) == 1
    assert anomalies[0]["attack_type"] == "path_traversal"


@pytest.mark.asyncio
async def test_command_injection_detected(skill):
    events = [
        {"id": 13, "event_type": "access", "source_ip": "10.0.0.6", "target_server": "web-01",
         "raw_data": {"cmd": "id; cat /etc/shadow"}},
    ]
    result = await skill.execute({"events": events, "patterns": [], "servers": []})
    anomalies = result["anomalies"]
    assert len(anomalies) == 1
    assert anomalies[0]["attack_type"] == "command_injection"
    assert anomalies[0]["severity"] == "critical"


@pytest.mark.asyncio
async def test_resource_exhaustion_detected(skill, sample_servers):
    result = await skill.execute({"events": [], "patterns": [], "servers": sample_servers})
    anomalies = result["anomalies"]
    resource = [a for a in anomalies if a["attack_type"] == "resource_exhaustion"]
    assert len(resource) == 1
    assert resource[0]["target_server"] == "db-01"


@pytest.mark.asyncio
async def test_brute_force_from_pattern(skill, sample_events):
    patterns = [{"pattern": "brute_force", "source_ip": "10.0.0.1", "severity": "high"}]
    result = await skill.execute({"events": sample_events, "patterns": patterns, "servers": []})
    anomalies = result["anomalies"]
    brute = [a for a in anomalies if a["attack_type"] == "brute_force"]
    assert len(brute) == 1
    assert brute[0]["source_ip"] == "10.0.0.1"
    assert "pattern_data" in brute[0]


@pytest.mark.asyncio
async def test_no_anomalies_with_clean_events(skill, sample_events):
    clean = [
        {"id": 20, "event_type": "access", "source_ip": "192.168.1.1", "target_server": "web-01",
         "raw_data": {"path": "/index.html", "method": "GET"}},
    ]
    result = await skill.execute({"events": clean, "patterns": [], "servers": []})
    assert result["anomalies"] == []


@pytest.mark.asyncio
async def test_raw_data_as_string_instead_of_dict(skill):
    events = [
        {"id": 30, "event_type": "access", "source_ip": "10.0.0.7", "target_server": "web-01",
         "raw_data": "GET /?q=' OR 1=1-- HTTP/1.1"},
    ]
    result = await skill.execute({"events": events, "patterns": [], "servers": []})
    anomalies = result["anomalies"]
    assert len(anomalies) == 1
    assert anomalies[0]["attack_type"] == "sql_injection"
