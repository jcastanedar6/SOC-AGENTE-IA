"""
Simulador de eventos SOC.
Se registra como servidor en el backend y genera escenarios de ataque realistas.
"""
import json
import time
import random
import argparse
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError

BASE_URL = "http://localhost:8002/api/v1"

def _url(path: str) -> str:
    return f"{BASE_URL}{path}" if path.endswith("/") else f"{BASE_URL}{path}/"

SERVER = {
    "hostname": "srv-correlator-01",
    "ip_address": "192.168.10.5",
    "role": "correlator",
    "os": "Ubuntu Server 22.04",
    "services": ["syslog", "auth", "nginx", "postgresql"],
}

ATTACK_IPS = [
    "45.33.32.156",
    "103.21.244.0",
    "185.220.101.47",
    "194.165.16.78",
    "91.108.4.10",
]

INTERNAL_IPS = ["192.168.10.10", "192.168.10.20", "192.168.10.30"]


def _request(method: str, path: str, body: dict) -> dict | None:
    try:
        data = json.dumps(body).encode()
        req = Request(
            _url(path),
            data=data,
            headers={"Content-Type": "application/json"},
            method=method,
        )
        with urlopen(req, timeout=5) as res:
            if res.status == 204:
                return {}
            return json.loads(res.read())
    except URLError as e:
        print(f"  [!] Error {method} {path}: {e}")
        return None
    except Exception as e:
        print(f"  [!] Error {method} {path}: {e}")
        return None


def post(path: str, body: dict) -> dict | None:
    return _request("POST", path, body)


def patch(path: str, body: dict) -> dict | None:
    return _request("PATCH", path, body)


def register_server() -> int | None:
    print(f"[*] Registrando servidor: {SERVER['hostname']} ({SERVER['ip_address']})")
    result = post("/servers", SERVER)
    if result:
        print(f"  [+] Servidor registrado — ID #{result['id']}")
        return result["id"]
    # Ya existe — buscar ID
    try:
        with urlopen(_url("/servers"), timeout=5) as res:
            servers = json.loads(res.read())
        for s in servers:
            if s["hostname"] == SERVER["hostname"]:
                print(f"  [~] Servidor ya existía — ID #{s['id']}")
                return s["id"]
    except Exception:
        pass
    return None


def update_server_metrics(server_id: int, cpu: float, mem: float, disk: float):
    patch(f"/servers/{server_id}", {"cpu_usage": cpu, "memory_usage": mem, "disk_usage": disk})


def emit_event(event_type: str, source_ip: str, severity: str, raw_data: dict = None):
    payload = {
        "event_type": event_type,
        "source_ip": source_ip,
        "target_server": SERVER["hostname"],
        "severity": severity,
        "raw_data": raw_data or {},
    }
    result = post("/events", payload)
    if result:
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"  [{ts}] {severity.upper():8} | {event_type:25} | src={source_ip}")
    return result


# ── Escenarios ────────────────────────────────────────────────────────────────

def scenario_brute_force(attacker_ip: str = None, count: int = 10):
    ip = attacker_ip or random.choice(ATTACK_IPS)
    print(f"\n[SCENARIO] Brute Force desde {ip} ({count} intentos)")
    for i in range(count):
        emit_event("auth_failed", ip, "medium", {
            "user": random.choice(["admin", "root", "ubuntu", "postgres"]),
            "service": "ssh",
            "attempt": i + 1,
        })
        time.sleep(0.3)


def scenario_port_scan(attacker_ip: str = None):
    ip = attacker_ip or random.choice(ATTACK_IPS)
    ports = random.sample(range(1, 65535), 15)
    print(f"\n[SCENARIO] Port Scan desde {ip} ({len(ports)} puertos)")
    for port in ports:
        emit_event("port_scan", ip, "low", {
            "port": port,
            "protocol": random.choice(["tcp", "udp"]),
            "state": "filtered" if random.random() > 0.3 else "open",
        })
        time.sleep(0.1)


def scenario_sql_injection(attacker_ip: str = None):
    ip = attacker_ip or random.choice(ATTACK_IPS)
    payloads = [
        "' OR '1'='1",
        "' UNION SELECT username, password FROM users--",
        "1; DROP TABLE users--",
        "admin'--",
        "' OR 1=1; xp_cmdshell('whoami')--",
    ]
    print(f"\n[SCENARIO] SQL Injection desde {ip}")
    for payload in payloads:
        emit_event("sql_injection", ip, "critical", {
            "payload": payload,
            "endpoint": random.choice(["/login", "/search", "/api/users"]),
            "method": "POST",
        })
        time.sleep(0.2)


def scenario_service_down(server_id: int):
    print(f"\n[SCENARIO] Caída de servicio en {SERVER['hostname']}")
    update_server_metrics(server_id, cpu=95.0, mem=92.0, disk=45.0)
    emit_event("service_down", SERVER["ip_address"], "high", {
        "service": "postgresql",
        "reason": "out_of_memory",
        "pid": random.randint(1000, 9999),
    })
    emit_event("service_down", SERVER["ip_address"], "high", {
        "service": "nginx",
        "reason": "connection_refused",
    })


def scenario_xss(attacker_ip: str = None):
    ip = attacker_ip or random.choice(ATTACK_IPS)
    payloads = [
        "<script>document.cookie</script>",
        "<img src=x onerror=alert(1)>",
        "javascript:alert('XSS')",
    ]
    print(f"\n[SCENARIO] XSS desde {ip}")
    for payload in payloads:
        emit_event("xss", ip, "high", {
            "payload": payload,
            "endpoint": "/comments",
            "method": "POST",
        })
        time.sleep(0.2)


def scenario_combined_attack():
    ip = random.choice(ATTACK_IPS)
    print(f"\n[SCENARIO] Ataque combinado desde {ip}")
    scenario_port_scan(ip)
    time.sleep(1)
    scenario_brute_force(ip, count=7)
    time.sleep(1)
    scenario_sql_injection(ip)


def scenario_noise():
    print(f"\n[SCENARIO] Ruido normal (eventos benignos)")
    for _ in range(5):
        emit_event("auth_failed", random.choice(INTERNAL_IPS), "low", {
            "user": "developer",
            "service": "ssh",
            "reason": "wrong_password",
        })
        time.sleep(0.5)


# ── Runner ────────────────────────────────────────────────────────────────────

SCENARIOS = {
    "brute_force":    lambda sid: scenario_brute_force(),
    "port_scan":      lambda sid: scenario_port_scan(),
    "sql_injection":  lambda sid: scenario_sql_injection(),
    "service_down":   lambda sid: scenario_service_down(sid),
    "xss":            lambda sid: scenario_xss(),
    "combined":       lambda sid: scenario_combined_attack(),
    "noise":          lambda sid: scenario_noise(),
}


def run_scenario(name: str, server_id: int):
    fn = SCENARIOS.get(name)
    if not fn:
        print(f"[!] Escenario desconocido: {name}. Opciones: {list(SCENARIOS.keys())}")
        return
    fn(server_id)


def run_all(server_id: int, delay: float = 2.0):
    for name in SCENARIOS:
        run_scenario(name, server_id)
        print(f"  [~] Esperando {delay}s antes del siguiente escenario...")
        time.sleep(delay)


def run_loop(server_id: int, interval: int = 30):
    print(f"\n[*] Modo loop — generando eventos cada {interval}s. Ctrl+C para detener.\n")
    while True:
        name = random.choice(list(SCENARIOS.keys()))
        run_scenario(name, server_id)
        print(f"\n[~] Próximo ciclo en {interval}s...")
        time.sleep(interval)


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulador de eventos SOC")
    parser.add_argument("--scenario", "-s", default="all",
                        help=f"Escenario a ejecutar: {list(SCENARIOS.keys())} | all | loop")
    parser.add_argument("--loop-interval", type=int, default=30,
                        help="Intervalo en segundos para modo loop (default: 30)")
    args = parser.parse_args()

    print("=" * 60)
    print("  SIMULADOR SOC — Agente Inteligente")
    print(f"  Backend: {BASE_URL}")
    print("=" * 60)

    server_id = register_server()
    if not server_id:
        print("[!] No se pudo registrar el servidor. ¿Está corriendo el backend?")
        exit(1)

    if args.scenario == "all":
        run_all(server_id)
    elif args.scenario == "loop":
        run_loop(server_id, args.loop_interval)
    else:
        run_scenario(args.scenario, server_id)

    print("\n[✓] Simulación completada.")
    print(f"[*] Disparar análisis del agente:")
    print(f"    curl -X POST {BASE_URL}/agent/run")
