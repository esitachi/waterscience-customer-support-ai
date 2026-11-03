"""
Tests for Phase 5: Scale & Performance Simulator
Verifies:
1. High-throughput message ingestion and concurrent background processing.
2. Handling of 2,000+ realistic customer messages.
3. Multiple traffic profiles (steady, burst, spiky, mixed).
4. Telemetry tracking: throughput, p95 latency, error rates.
5. Zero message loss guarantee.
6. Acceptance criteria verification report.
"""

import time
import pytest
from fastapi.testclient import TestClient
from app.api import app
from app.simulator import ScaleSimulatorEngine, SimulationRequest
from app.database import init_db
from app.config import settings

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_env():
    init_db()
    settings.EMERGENCY_AUTOMATION_PAUSED = False
    yield


def test_simulator_start_and_status_endpoints():
    """Simulator API starts load simulation and returns live telemetry."""
    req = {
        "total_messages": 100,
        "profile": "mixed",
        "concurrency": 4
    }

    start_res = client.post("/api/v2/simulator/start", json=req)
    assert start_res.status_code == 200
    data = start_res.json()
    assert data["status"] in ["running", "completed"]
    assert data["total_messages"] == 100

    # Wait for completion
    for _ in range(30):
        time.sleep(0.3)
        st = client.get("/api/v2/simulator/status").json()
        if st["status"] == "completed":
            assert st["total_processed"] >= 100
            assert st["throughput_msgs_sec"] > 0
            assert st["lost_messages"] == 0
            break


def test_2000_message_benchmark_simulation():
    """
    Simulates 2,000 realistic messages across mixed risk tiers (Level 1, 2, 3)
    and verifies throughput, p95 latency, zero message loss, and acceptance criteria.
    """
    req = {
        "total_messages": 2000,
        "profile": "mixed",
        "concurrency": 10
    }

    start_res = client.post("/api/v2/simulator/start", json=req)
    assert start_res.status_code == 200

    # Poll until 2000 messages processed or timed out
    completed = False
    for _ in range(90):
        time.sleep(0.5)
        st = client.get("/api/v2/simulator/status").json()
        if st["status"] == "completed":
            completed = True
            assert st["total_processed"] >= 2000
            assert st["lost_messages"] == 0
            assert st["throughput_msgs_sec"] >= 40.0
            assert st["p95_latency_ms"] < 2000.0
            assert st["error_rate_percent"] < 0.5
            break

    assert completed is True

    # Check Acceptance Report
    rep_res = client.get("/api/v2/simulator/report")
    assert rep_res.status_code == 200
    report = rep_res.json()

    assert report["acceptance_criteria"]["volume_2000_plus"]["passed"] is True
    assert report["acceptance_criteria"]["zero_message_loss"]["passed"] is True
    assert report["acceptance_criteria"]["latency_p95_under_2s"]["passed"] is True
    assert report["acceptance_criteria"]["error_rate_under_half_percent"]["passed"] is True


def test_traffic_profiles_support():
    """Simulator must accept all 4 traffic profiles: steady, burst, spiky, mixed."""
    for prof in ["steady", "burst", "spiky"]:
        r = client.post("/api/v2/simulator/start", json={"total_messages": 50, "profile": prof})
        assert r.status_code == 200
        # Stop or wait brief
        time.sleep(0.3)
        client.post("/api/v2/simulator/stop")
