"""Simulator-only endpoints — NO AUTH, only for internal/dev use via Docker."""

import random
from datetime import datetime, UTC
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.event import Event
from app.models.server import Server

router = APIRouter()


@router.post("/events", summary="Create random event (no auth, simulator only)")
def create_random_event(
    event_type: str = Query(None),
    db: Session = Depends(get_db),
):
    """Create a single random SOC event. Used by the simulator container."""
    attack_ips = [
        "45.33.32.156", "103.21.244.0", "185.220.101.47",
        "194.165.16.78", "91.108.4.10",
    ]

    scenarios = [
        {"type": "auth_failed", "sev": "medium", "users": ["admin", "root", "ubuntu", "postgres"]},
        {"type": "port_scan", "sev": "low", "users": []},
        {"type": "sql_injection", "sev": "critical", "users": []},
        {"type": "xss", "sev": "high", "users": []},
        {"type": "access", "sev": "low", "users": ["dev", "monitor"]},
    ]

    if event_type:
        sc = next((s for s in scenarios if s["type"] == event_type), scenarios[0])
    else:
        sc = random.choice(scenarios)

    servers = db.query(Server).all()
    target = random.choice(servers).hostname if servers else "web-01"

    raw_data: dict = {}
    if sc["type"] == "auth_failed":
        raw_data = {"user": random.choice(sc["users"]), "service": "ssh", "attempt": random.randint(1, 20)}
    elif sc["type"] == "port_scan":
        raw_data = {"port": random.randint(1, 65535), "protocol": random.choice(["tcp", "udp"]), "state": random.choice(["open", "filtered"])}
    elif sc["type"] == "sql_injection":
        raw_data = {"payload": random.choice(["' OR '1'='1", "UNION SELECT *", "'; DROP TABLE--"]), "endpoint": "/login"}
    elif sc["type"] == "xss":
        raw_data = {"payload": "<script>alert(1)</script>", "endpoint": "/comments"}
    else:
        raw_data = {"path": "/dashboard", "method": "GET", "user": random.choice(sc["users"])}

    evt = Event(
        event_type=sc["type"],
        source_ip=random.choice(attack_ips),
        target_server=target,
        severity=sc["sev"],
        raw_data=raw_data,
    )
    db.add(evt)
    db.commit()
    db.refresh(evt)

    return {
        "id": evt.id,
        "event_type": evt.event_type,
        "source_ip": evt.source_ip,
        "severity": evt.severity,
    }


@router.post("/events/batch", summary="Create multiple random events (no auth)")
def create_random_events(
    count: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Batch-create random SOC events for simulation."""
    results = []
    for _ in range(count):
        attack_ips = [
            "45.33.32.156", "103.21.244.0", "185.220.101.47",
            "194.165.16.78", "91.108.4.10",
        ]
        scenarios = [
            {"type": "auth_failed", "sev": "medium", "users": ["admin", "root", "ubuntu", "postgres"]},
            {"type": "port_scan", "sev": "low", "users": []},
            {"type": "sql_injection", "sev": "critical", "users": []},
            {"type": "xss", "sev": "high", "users": []},
            {"type": "access", "sev": "low", "users": ["dev", "monitor"]},
        ]
        sc = random.choice(scenarios)
        servers = db.query(Server).all()
        target = random.choice(servers).hostname if servers else "web-01"

        raw_data: dict = {}
        if sc["type"] == "auth_failed":
            raw_data = {"user": random.choice(sc["users"]), "service": "ssh", "attempt": random.randint(1, 20)}
        elif sc["type"] == "port_scan":
            raw_data = {"port": random.randint(1, 65535), "protocol": random.choice(["tcp", "udp"]), "state": random.choice(["open", "filtered"])}
        elif sc["type"] == "sql_injection":
            raw_data = {"payload": random.choice(["' OR '1'='1", "UNION SELECT *", "'; DROP TABLE--"]), "endpoint": "/login"}
        elif sc["type"] == "xss":
            raw_data = {"payload": "<script>alert(1)</script>", "endpoint": "/comments"}
        else:
            raw_data = {"path": "/dashboard", "method": "GET", "user": random.choice(sc["users"])}

        evt = Event(
            event_type=sc["type"],
            source_ip=random.choice(attack_ips),
            target_server=target,
            severity=sc["sev"],
            raw_data=raw_data,
        )
        db.add(evt)
        results.append({"event_type": sc["type"], "severity": sc["sev"]})

    db.commit()
    return {"events_created": len(results), "events": results}


@router.post("/servers", summary="Register a server (no auth, simulator only)")
def register_server(
    hostname: str = Query("srv-simulator-01"),
    ip_address: str = Query("10.0.0.99"),
    db: Session = Depends(get_db),
):
    existing = db.query(Server).filter(Server.hostname == hostname).first()
    if existing:
        return {"id": existing.id, "hostname": existing.hostname, "message": "already exists"}
    srv = Server(hostname=hostname, ip_address=ip_address, role="simulator", os="Simulated")
    db.add(srv)
    db.commit()
    db.refresh(srv)
    return {"id": srv.id, "hostname": srv.hostname, "message": "created"}
