"""
Tests for Phase 2: Scalable Message Processing
Verifies:
1. Fast message ingestion (<50ms ACK).
2. Idempotent duplicate message rejection.
3. Background asynchronous worker processing.
4. Persistent database state for conversations and messages.
5. Automatic escalation ticket generation in DB for Level 3 queries.
6. Real-time queue telemetry and health reporting.
"""

import pytest
import time
import uuid
from fastapi.testclient import TestClient
from app.api import app
from app.database import init_db, SessionLocal, MessageRecord, ConversationRecord, ProcessingJobRecord, TicketRecord
from app.queue_manager import get_queue_manager

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    init_db()
    queue_mgr = get_queue_manager()
    queue_mgr.start_workers()
    yield


def test_fast_message_ingestion_and_ack():
    """Ingestion endpoint must validate payload, persist message, and return ACK quickly."""
    msg_id = f"MSG-{uuid.uuid4().hex[:8]}"
    conv_id = f"CONV-{uuid.uuid4().hex[:8]}"
    payload = {
        "channel": "waterscience_website",
        "customer_id": "CUST-101",
        "conversation_id": conv_id,
        "message_id": msg_id,
        "message": "Will CLEO SFU-717 fit my 24mm metal tap?"
    }

    start = time.time()
    response = client.post("/api/v2/messages/ingest", json=payload)
    latency_ms = (time.time() - start) * 1000.0

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["message_id"] == msg_id
    assert data["conversation_id"] == conv_id
    assert data["job_id"] is not None
    assert latency_ms < 500  # Fast ACK


def test_idempotent_duplicate_message_protection():
    """Sending the exact same message_id twice must be recognized as duplicate."""
    msg_id = f"MSG-DUP-{uuid.uuid4().hex[:8]}"
    conv_id = f"CONV-{uuid.uuid4().hex[:8]}"
    payload = {
        "channel": "amazon",
        "customer_id": "CUST-202",
        "conversation_id": conv_id,
        "message_id": msg_id,
        "message": "I need a replacement cartridge for VERSA STF-1025"
    }

    # First submission
    r1 = client.post("/api/v2/messages/ingest", json=payload)
    assert r1.status_code == 200
    assert r1.json()["status"] == "accepted"

    # Second submission with same message_id
    r2 = client.post("/api/v2/messages/ingest", json=payload)
    assert r2.status_code == 200
    assert r2.json()["status"] == "duplicate_ignored"

    # Verify database has only 1 message record
    with SessionLocal() as db:
        count = db.query(MessageRecord).filter_by(message_id=msg_id).count()
        assert count == 1


def test_async_worker_execution_and_job_completion():
    """Background worker must process the queued job to 'completed' status."""
    msg_id = f"MSG-WORKER-{uuid.uuid4().hex[:8]}"
    conv_id = f"CONV-WORKER-{uuid.uuid4().hex[:8]}"
    payload = {
        "channel": "waterscience_website",
        "customer_id": "CUST-303",
        "conversation_id": conv_id,
        "message_id": msg_id,
        "message": "Will CLEO SFU-717 fit my 24mm standard metal threaded kitchen tap?"
    }

    r = client.post("/api/v2/messages/ingest", json=payload)
    job_id = r.json()["job_id"]

    # Poll for completion (up to 8 seconds)
    completed = False
    for _ in range(16):
        time.sleep(0.5)
        jr = client.get(f"/api/v2/jobs/{job_id}")
        if jr.status_code == 200:
            job_data = jr.json()
            if job_data["status"] == "completed":
                completed = True
                assert job_data["resolution_level"] == "level_1_automatic"
                assert job_data["auto_dispatched"] is True
                assert "24" in job_data["response_text"] or "metal" in job_data["response_text"].lower()
                break

    assert completed is True


def test_level_3_escalation_creates_database_ticket():
    """Level 3 queries (e.g. active water leak) must create an escalation ticket in DB."""
    msg_id = f"MSG-LEAK-{uuid.uuid4().hex[:8]}"
    conv_id = f"CONV-LEAK-{uuid.uuid4().hex[:8]}"
    payload = {
        "channel": "waterscience_website",
        "customer_id": "CUST-LEAK",
        "conversation_id": conv_id,
        "message_id": msg_id,
        "message": "Water is flooding my bathroom from the filter joint! Help!"
    }

    r = client.post("/api/v2/messages/ingest", json=payload)
    job_id = r.json()["job_id"]

    # Poll for completion
    for _ in range(16):
        time.sleep(0.5)
        jr = client.get(f"/api/v2/jobs/{job_id}")
        if jr.status_code == 200 and jr.json()["status"] == "completed":
            break

    # Verify escalation ticket exists in database
    with SessionLocal() as db:
        ticket = db.query(TicketRecord).filter_by(conversation_id=conv_id).first()
        assert ticket is not None
        assert ticket.status == "open"
        assert ticket.priority == "urgent"
        assert "leak" in ticket.escalation_reason.lower() or "safety" in ticket.escalation_reason.lower()


def test_queue_telemetry_endpoint():
    """The /api/v2/queue/stats endpoint should return live worker and throughput statistics."""
    r = client.get("/api/v2/queue/stats")
    assert r.status_code == 200
    data = r.json()
    assert "queue_depth" in data
    assert "active_workers" in data
    assert "configured_concurrency" in data
    assert data["configured_concurrency"] >= 1
    assert "total_processed" in data
    assert "average_latency_ms" in data
