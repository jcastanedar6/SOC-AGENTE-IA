import logging
import asyncio
from sqlalchemy.orm import Session
from app.agent.state import AgentState
from app.agent.skills.event_correlation import EventCorrelationSkill
from app.agent.skills.anomaly_detection import AnomalyDetectionSkill
from app.agent.skills.incident_classification import IncidentClassificationSkill
from app.agent.skills.server_state import ServerStateSkill
from app.agent.skills.recommendation import RecommendationSkill
from app.agent.skills.notification import NotificationSkill
from app.llm.opencode_client import OpenCodeClient
from app.rag.retriever import retrieve_context
from app.rag.store import add_incident_to_rag
from app.models.event import Event
from app.models.incident import Incident
from app.models.server import Server

logger = logging.getLogger(__name__)


class SOCAgent:
    def __init__(self):
        self.state = AgentState()
        self.llm = OpenCodeClient()
        self.correlation = EventCorrelationSkill()
        self.anomaly = AnomalyDetectionSkill()
        self.classification = IncidentClassificationSkill(self.llm)
        self.server_state = ServerStateSkill()
        self.recommendation = RecommendationSkill(self.llm)
        self.notification = NotificationSkill()

    async def run_cycle(self, db: Session) -> dict:
        if self.state.is_running:
            return {"status": "already_running"}

        self.state.is_running = True
        self.state.reset_cycle()

        try:
            result = await asyncio.wait_for(
                self._run_cycle_inner(db),
                timeout=120.0,
            )
        except asyncio.TimeoutError:
            logger.warning("Agent cycle timed out after 120s")
            self.state.record_error("cycle timed out")
            result = {"status": "error", "error": "cycle timed out"}
        except Exception as e:
            logger.exception("Agent cycle error")
            self.state.record_error(str(e))
            result = {"status": "error", "error": str(e)}
        finally:
            self.state.is_running = False

        return result

    async def _run_cycle_inner(self, db: Session) -> dict:
        events = self._fetch_unprocessed_events(db)
        servers = self._fetch_servers(db)

        server_ctx = {"servers": [self._server_to_dict(s) for s in servers]}
        await self.server_state.execute(server_ctx)

        event_dicts = [self._event_to_dict(e) for e in events]
        correlation_result = await self.correlation.execute({"events": event_dicts})
        anomaly_result = await self.anomaly.execute({
            "events": event_dicts,
            "patterns": correlation_result.get("patterns", []),
            "servers": server_ctx["servers"],
        })

        anomalies = anomaly_result.get("anomalies", [])
        if anomalies:
            query_text = " ".join(a.get("attack_type", "") for a in anomalies[:3])
            rag_context = retrieve_context(query_text)

            classification_result = await self.classification.execute({
                "anomalies": anomalies,
                "rag_context": rag_context,
            })
        classifications = classification_result.get("classifications", [])

        server_state_result = await self.server_state.execute(server_ctx)
        recommendation_result = await self.recommendation.execute({
            "classifications": classifications,
            "server_alerts": server_state_result.get("server_alerts", []),
        })

        incident = self._create_incident(db, classifications, recommendation_result)
        if incident:
            add_incident_to_rag({
                "id": incident.id,
                "title": incident.title,
                "attack_type": incident.attack_type,
                "severity": incident.severity,
                "description": incident.description,
                "recommendation": incident.recommendation,
                "status": incident.status,
            })

            notification_result = await self.notification.execute({
                "recommendations": recommendation_result.get("recommendations", []),
                "incident_id": incident.id,
            })

            self.state.incidents_created += 1
            if notification_result.get("notified"):
                self.state.notifications_sent += 1

        self._mark_events_processed(db, [e.id for e in events])
        self.state.events_processed += len(events)

        return {
            "status": "completed",
            "events_analyzed": len(events),
            "anomalies_found": len(anomalies),
            "incidents_created": self.state.incidents_created,
        }

    def _fetch_unprocessed_events(self, db: Session) -> list[Event]:
        return db.query(Event).filter(Event.processed == False).limit(100).all()

    def _fetch_servers(self, db: Session) -> list[Server]:
        return db.query(Server).all()

    def _event_to_dict(self, event: Event) -> dict:
        return {
            "id": event.id,
            "event_type": event.event_type,
            "source_ip": event.source_ip,
            "target_server": event.target_server,
            "severity": event.severity,
            "raw_data": event.raw_data,
            "created_at": event.created_at,
        }

    def _server_to_dict(self, server: Server) -> dict:
        return {
            "hostname": server.hostname,
            "ip_address": server.ip_address,
            "status": server.status,
            "cpu_usage": server.cpu_usage,
            "memory_usage": server.memory_usage,
            "disk_usage": server.disk_usage,
        }

    def _create_incident(self, db: Session, classifications: list[dict], recommendations: dict) -> Incident | None:
        if not classifications:
            return None

        top = max(classifications, key=lambda c: {"low": 0, "medium": 1, "high": 2, "critical": 3}.get(c.get("severity", "low"), 0))
        recs = recommendations.get("recommendations", [])
        rec_text = recs[0].get("enhanced_recommendation", "") if recs else ""

        attack_type = top.get("anomaly", {}).get("attack_type", "unknown")
        source_ips = list({c.get("anomaly", {}).get("source_ip") for c in classifications if c.get("anomaly", {}).get("source_ip")})

        incident = Incident(
            title=f"Incidente detectado: {attack_type.replace('_', ' ').title()}",
            description=top.get("summary", ""),
            severity=top.get("severity", "medium"),
            attack_type=attack_type,
            source_ips=source_ips,
            recommendation=rec_text,
            llm_analysis=top.get("summary", ""),
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)
        return incident

    def _mark_events_processed(self, db: Session, event_ids: list[int]):
        if event_ids:
            db.query(Event).filter(Event.id.in_(event_ids)).update({"processed": True}, synchronize_session=False)
            db.commit()

    def seed_sample_data(self, db: Session) -> dict:
        """Seed the database with sample servers and events for testing."""
        from datetime import datetime, UTC

        # ── Servers ──
        sample_servers = [
            {"hostname": "web-01", "ip_address": "192.168.1.10", "role": "web", "os": "Ubuntu 22.04", "status": "online", "cpu_usage": 45.0, "memory_usage": 60.0, "disk_usage": 50.0},
            {"hostname": "db-01", "ip_address": "192.168.1.20", "role": "database", "os": "Ubuntu 22.04", "status": "online", "cpu_usage": 95.0, "memory_usage": 80.0, "disk_usage": 70.0},
            {"hostname": "cache-01", "ip_address": "192.168.1.30", "role": "cache", "os": "Ubuntu 22.04", "status": "offline", "cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 40.0},
            {"hostname": "api-01", "ip_address": "192.168.1.40", "role": "api", "os": "Ubuntu 22.04", "status": "online", "cpu_usage": 30.0, "memory_usage": 45.0, "disk_usage": 35.0},
        ]
        servers_created = 0
        for srv in sample_servers:
            exists = db.query(Server).filter(Server.hostname == srv["hostname"]).first()
            if not exists:
                db.add(Server(**srv))
                servers_created += 1

        # ── Events ──
        now = datetime.now(UTC)
        sample_events = [
            # Brute force desde 45.33.32.156
            {"event_type": "auth_failed", "source_ip": "45.33.32.156", "target_server": "web-01", "severity": "medium", "raw_data": {"user": "admin", "service": "ssh", "attempt": 1}, "created_at": now},
            {"event_type": "auth_failed", "source_ip": "45.33.32.156", "target_server": "web-01", "severity": "medium", "raw_data": {"user": "root", "service": "ssh", "attempt": 2}, "created_at": now},
            {"event_type": "auth_failed", "source_ip": "45.33.32.156", "target_server": "web-01", "severity": "medium", "raw_data": {"user": "admin", "service": "ssh", "attempt": 3}, "created_at": now},
            {"event_type": "auth_failed", "source_ip": "45.33.32.156", "target_server": "web-01", "severity": "medium", "raw_data": {"user": "postgres", "service": "ssh", "attempt": 4}, "created_at": now},
            {"event_type": "auth_failed", "source_ip": "45.33.32.156", "target_server": "web-01", "severity": "medium", "raw_data": {"user": "ubuntu", "service": "ssh", "attempt": 5}, "created_at": now},
            {"event_type": "auth_failed", "source_ip": "45.33.32.156", "target_server": "web-01", "severity": "medium", "raw_data": {"user": "admin", "service": "ssh", "attempt": 6}, "created_at": now},
            # Port scan desde 103.21.244.0
            {"event_type": "port_scan", "source_ip": "103.21.244.0", "target_server": "web-01", "severity": "low", "raw_data": {"port": 22, "protocol": "tcp", "state": "open"}, "created_at": now},
            {"event_type": "port_scan", "source_ip": "103.21.244.0", "target_server": "db-01", "severity": "low", "raw_data": {"port": 3306, "protocol": "tcp", "state": "open"}, "created_at": now},
            {"event_type": "port_scan", "source_ip": "103.21.244.0", "target_server": "cache-01", "severity": "low", "raw_data": {"port": 6379, "protocol": "tcp", "state": "filtered"}, "created_at": now},
            {"event_type": "port_scan", "source_ip": "103.21.244.0", "target_server": "api-01", "severity": "low", "raw_data": {"port": 443, "protocol": "tcp", "state": "open"}, "created_at": now},
            # SQL Injection desde 185.220.101.47
            {"event_type": "sql_injection", "source_ip": "185.220.101.47", "target_server": "api-01", "severity": "critical", "raw_data": {"payload": "' OR '1'='1", "endpoint": "/login", "method": "POST"}, "created_at": now},
            {"event_type": "sql_injection", "source_ip": "185.220.101.47", "target_server": "api-01", "severity": "critical", "raw_data": {"payload": "'; DROP TABLE users--", "endpoint": "/search", "method": "GET"}, "created_at": now},
            # XSS desde 194.165.16.78
            {"event_type": "xss", "source_ip": "194.165.16.78", "target_server": "web-01", "severity": "high", "raw_data": {"payload": "<script>document.cookie</script>", "endpoint": "/comments", "method": "POST"}, "created_at": now},
        ]
        events_created = 0
        for evt in sample_events:
            db.add(Event(**evt))
            events_created += 1

        db.commit()

        return {
            "servers_created": servers_created,
            "events_created": events_created,
            "message": f"Seeded {servers_created} servers and {events_created} events",
        }

    def simulate_random_events(self, db: Session, count: int = 5) -> dict:
        """Generate random attack events for continuous simulation."""
        import random
        from datetime import datetime, UTC

        attack_ips = ["45.33.32.156", "103.21.244.0", "185.220.101.47", "194.165.16.78", "91.108.4.10"]
        internal_ips = ["192.168.10.10", "192.168.10.20"]
        servers_available = db.query(Server).all()
        if not servers_available:
            # Auto-seed if no servers exist
            self.seed_sample_data(db)
            servers_available = db.query(Server).all()
        target_servers = [s.hostname for s in servers_available] or ["web-01"]

        scenarios = [
            {"type": "auth_failed", "sev": "medium", "ips": attack_ips,
             "raw": lambda: {"user": random.choice(["admin", "root", "ubuntu", "postgres"]), "service": "ssh", "attempt": random.randint(3, 15)}},
            {"type": "port_scan", "sev": "low", "ips": attack_ips,
             "raw": lambda: {"port": random.randint(1, 65535), "protocol": random.choice(["tcp", "udp"]), "state": random.choice(["open", "filtered"])}},
            {"type": "sql_injection", "sev": "critical", "ips": attack_ips,
             "raw": lambda: {"payload": random.choice(["' OR '1'='1", "UNION SELECT *", "'; DROP TABLE--"]), "endpoint": random.choice(["/login", "/search"])}},
            {"type": "xss", "sev": "high", "ips": attack_ips,
             "raw": lambda: {"payload": "<script>alert(1)</script>", "endpoint": "/comments"}},
            {"type": "access", "sev": "low", "ips": internal_ips,
             "raw": lambda: {"path": "/dashboard", "method": "GET", "user": random.choice(["dev", "admin"])}},
        ]

        now = datetime.now(UTC)
        created = 0
        for _ in range(count):
            sc = random.choice(scenarios)
            evt = Event(
                event_type=sc["type"],
                source_ip=random.choice(sc["ips"]),
                target_server=random.choice(target_servers),
                severity=sc["sev"],
                raw_data=sc["raw"](),
                created_at=now,
            )
            db.add(evt)
            created += 1

        db.commit()
        return {"events_created": created, "message": f"Generated {created} random events"}


_agent_instance: SOCAgent | None = None


def get_agent() -> SOCAgent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = SOCAgent()
    return _agent_instance
