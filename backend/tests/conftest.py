from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta, UTC
import pytest

from app.config import Settings


@pytest.fixture(autouse=True)
def override_settings():
    original = None
    from app.config import settings
    original = settings.database_url
    settings.database_url = "sqlite:///./test_agente_soc.db"
    settings.correlation_window_seconds = 3600
    settings.brute_force_threshold = 3
    settings.telegram_bot_token = ""
    settings.telegram_chat_ids = ""
    yield
    settings.database_url = original
    settings.correlation_window_seconds = 60
    settings.brute_force_threshold = 5


@pytest.fixture
def mock_llm():
    client = MagicMock()
    client.complete = AsyncMock(return_value='[{"severity": "high", "attack_category": "intrusión", "confidence": 0.9, "summary": "Ataque detectado", "recommended_action": "Bloquear IP"}]')
    client.chat = AsyncMock(return_value="Recomendación del LLM")
    client.health = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_llm_fallback():
    client = MagicMock()
    client.complete = AsyncMock(side_effect=Exception("LLM unavailable"))
    return client


@pytest.fixture
def sample_events():
    now = datetime.now(UTC)
    return [
        {"id": 1, "event_type": "auth_failed", "source_ip": "10.0.0.1", "target_server": "web-01", "severity": "medium", "raw_data": {"user": "admin"}, "created_at": now - timedelta(seconds=10)},
        {"id": 2, "event_type": "auth_failed", "source_ip": "10.0.0.1", "target_server": "web-01", "severity": "medium", "raw_data": {"user": "root"}, "created_at": now - timedelta(seconds=20)},
        {"id": 3, "event_type": "auth_failed", "source_ip": "10.0.0.1", "target_server": "web-01", "severity": "medium", "raw_data": {"user": "admin"}, "created_at": now - timedelta(seconds=30)},
        {"id": 4, "event_type": "auth_failed", "source_ip": "10.0.0.1", "target_server": "web-01", "severity": "medium", "raw_data": {"user": "postgres"}, "created_at": now - timedelta(seconds=40)},
        {"id": 5, "event_type": "port_scan", "source_ip": "10.0.0.2", "target_server": "web-01", "severity": "low", "raw_data": {"ports": [22, 80, 443]}, "created_at": now - timedelta(seconds=15)},
        {"id": 6, "event_type": "port_scan", "source_ip": "10.0.0.2", "target_server": "db-01", "severity": "low", "raw_data": {"ports": [22, 3306]}, "created_at": now - timedelta(seconds=25)},
        {"id": 7, "event_type": "port_scan", "source_ip": "10.0.0.2", "target_server": "cache-01", "severity": "low", "raw_data": {"ports": [22, 6379]}, "created_at": now - timedelta(seconds=35)},
    ]


@pytest.fixture
def sample_event_dicts():
    now = datetime.now(UTC)
    return [
        {"id": 1, "event_type": "auth_failed", "source_ip": "10.0.0.1", "target_server": "web-01", "severity": "medium", "raw_data": {"user": "admin"}, "created_at": now},
        {"id": 2, "event_type": "access", "source_ip": "10.0.0.2", "target_server": "web-01", "severity": "low", "raw_data": {"path": "/", "method": "GET"}, "created_at": now},
    ]


@pytest.fixture
def sample_servers():
    return [
        {"hostname": "web-01", "ip_address": "192.168.1.10", "status": "online", "cpu_usage": 45.0, "memory_usage": 60.0, "disk_usage": 50.0},
        {"hostname": "db-01", "ip_address": "192.168.1.20", "status": "online", "cpu_usage": 95.0, "memory_usage": 80.0, "disk_usage": 70.0},
        {"hostname": "cache-01", "ip_address": "192.168.1.30", "status": "offline", "cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 40.0},
    ]
