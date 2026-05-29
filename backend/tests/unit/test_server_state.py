import pytest

from app.agent.skills.server_state import ServerStateSkill


@pytest.fixture
def skill():
    return ServerStateSkill()


@pytest.mark.asyncio
async def test_tracks_servers(skill, sample_servers):
    result = await skill.execute({"servers": sample_servers})
    assert result["servers_tracked"] == 3
    state = skill.get_state()
    assert "web-01" in state
    assert "db-01" in state
    assert "cache-01" in state


@pytest.mark.asyncio
async def test_offline_alert(skill, sample_servers):
    result = await skill.execute({"servers": sample_servers})
    alerts = result["server_alerts"]
    offline = [a for a in alerts if a["issue"] == "server_offline"]
    assert len(offline) == 1
    assert offline[0]["hostname"] == "cache-01"
    assert offline[0]["severity"] == "critical"


@pytest.mark.asyncio
async def test_high_cpu_alert(skill, sample_servers):
    result = await skill.execute({"servers": sample_servers})
    alerts = result["server_alerts"]
    cpu = [a for a in alerts if a["issue"] == "high_cpu"]
    assert len(cpu) == 1
    assert cpu[0]["hostname"] == "db-01"
    assert cpu[0]["value"] == 95.0


@pytest.mark.asyncio
async def test_no_alerts_for_healthy_servers(skill):
    healthy = [
        {"hostname": "web-01", "status": "online", "cpu_usage": 30.0, "memory_usage": 40.0, "disk_usage": 50.0},
        {"hostname": "web-02", "status": "online", "cpu_usage": 50.0, "memory_usage": 60.0, "disk_usage": 70.0},
    ]
    result = await skill.execute({"servers": healthy})
    assert result["server_alerts"] == []


@pytest.mark.asyncio
async def test_high_memory_alert(skill):
    servers = [
        {"hostname": "mem-01", "status": "online", "cpu_usage": 30.0, "memory_usage": 90.0, "disk_usage": 40.0},
    ]
    result = await skill.execute({"servers": servers})
    alerts = result["server_alerts"]
    mem = [a for a in alerts if a["issue"] == "high_memory"]
    assert len(mem) == 1
    assert mem[0]["value"] == 90.0


@pytest.mark.asyncio
async def test_disk_full_alert(skill):
    servers = [
        {"hostname": "disk-01", "status": "online", "cpu_usage": 30.0, "memory_usage": 40.0, "disk_usage": 95.0},
    ]
    result = await skill.execute({"servers": servers})
    alerts = result["server_alerts"]
    disk = [a for a in alerts if a["issue"] == "disk_full"]
    assert len(disk) == 1
    assert disk[0]["severity"] == "medium"


@pytest.mark.asyncio
async def test_state_persists_across_calls(skill, sample_servers):
    await skill.execute({"servers": sample_servers[:1]})
    assert skill.get_state()["web-01"]["cpu_usage"] == 45.0
    await skill.execute({"servers": sample_servers[1:]})
    state = skill.get_state()
    assert len(state) == 3
    assert state["db-01"]["cpu_usage"] == 95.0


@pytest.mark.asyncio
async def test_empty_servers(skill):
    result = await skill.execute({"servers": []})
    assert result["servers_tracked"] == 0
    assert result["server_alerts"] == []


@pytest.mark.asyncio
async def test_server_without_hostname_ignored(skill):
    servers = [
        {"ip_address": "10.0.0.1", "status": "online", "cpu_usage": 50.0, "memory_usage": 50.0, "disk_usage": 50.0},
    ]
    result = await skill.execute({"servers": servers})
    assert result["servers_tracked"] == 0
