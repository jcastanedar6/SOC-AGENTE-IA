"""
Entrypoint for dockerized simulator.
Calls the no-auth simulator endpoints to feed events into the system.
"""
import time
import random
import logging
import urllib.request
import urllib.error
import json
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8002")
SIMULATE_URL = f"{BACKEND_URL}/api/v1/simulator/events/batch"
SEED_URL = f"{BACKEND_URL}/api/v1/agent/simulate"
INTERVAL = int(os.getenv("SIMULATOR_INTERVAL", "120"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [SIM] %(message)s")
logger = logging.getLogger("simulator")


def call(url: str, method: str = "POST", data: dict = None) -> dict | None:
    try:
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, method=method,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        logger.warning(f"HTTP {e.code}: {e.read().decode()[:200]}")
        return None
    except Exception as e:
        logger.warning(f"Error: {e}")
        return None


def seed_once():
    """Seed sample data on first run."""
    logger.info("Seeding sample data...")
    result = call(f"{SEED_URL}?count=8")
    if result:
        logger.info(f"Seed result: {result}")
    else:
        logger.warning("Seed failed (may already have data)")


def simulate_batch(count: int = 5):
    """Generate a batch of random events."""
    result = call(f"{SIMULATE_URL}?count={count}")
    if result:
        logger.info(f"Generated {result.get('events_created', 0)} events")
    else:
        logger.warning("Simulate batch failed")


def main():
    logger.info(f"Simulator started — backend: {BACKEND_URL}, interval: {INTERVAL}s")
    time.sleep(10)  # Wait for backend to be ready
    seed_once()
    while True:
        simulate_batch(random.randint(3, 8))
        logger.info(f"Next batch in {INTERVAL}s...")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
