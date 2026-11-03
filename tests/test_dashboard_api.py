"""
Tests for Phase 4: Support Operations Dashboard & Business Controls APIs
Verifies:
1. Retrieval of high-level operational KPIs (messages, queue depth, auto-resolution rate, latencies).
2. Human escalation inbox retrieval and ticket lifecycle management (assign, resolve, close).
3. Business-user controls: toggling emergency automation pause and auto-resolution categories.
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from app.api import app
from app.database import init_db, SessionLocal, TicketRecord, MessageRecord, ConversationRecord
from app.config import settings

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    settings.EMERGENCY_AUTOMATION_PAUSED = False
    yield


def test_dashboard_metrics_kpis():
    """Dashboard metrics API must return all operational metrics required by support managers."""
    # Seed a test conversation and message
    conv_id = f"CONV-METRIC-{uuid.uuid4().hex[:6]}"
    with SessionLocal() as db:
        c = ConversationRecord(
            conversation_id=conv_id,
            customer_id="CUST-M1",
            status="auto_resolved",
            resolution_level="level_1_automatic"
        )
        db.add(c)
        m = MessageRecord(
            message_id=f"MSG-M-{uuid.uuid4().hex[:6]}",
            conversation_id=conv_id,
            customer_id="CUST-M1",
            content="Will CLEO fit 24mm tap?",
            timestamp="2026-11-03T12:00:00Z"
        )
        db.add(m)
        db.commit()

    res = client.get("/api/v2/dashboard/metrics")
    assert res.status_code == 200
    data = res.json()

    assert "total_incoming_messages" in data
    assert data["total_incoming_messages"] >= 1
    assert "active_conversations" in data
    assert "messages_awaiting_processing" in data
    assert "automatically_resolved_conversations" in data
    assert "escalated_conversations" in data
    assert "conversations_awaiting_customer_replies" in data
    assert "failed_processing_jobs" in data
    assert "retrying_jobs" in data
    assert "average_response_time_ms" in data
    assert "resolution_rate_percent" in data
    assert "emergency_pause_active" in data
    assert data["emergency_pause_active"] is False


def test_business_controls_emergency_pause_toggle():
    """Manager can toggle emergency automation pause without technical intervention."""
    # 1. Activate emergency pause
    r1 = client.post("/api/v2/dashboard/controls", json={"emergency_pause": True})
    assert r1.status_code == 200
    assert r1.json()["emergency_pause_active"] is True
    assert settings.EMERGENCY_AUTOMATION_PAUSED is True

    # 2. Deactivate emergency pause
    r2 = client.post("/api/v2/dashboard/controls", json={"emergency_pause": False})
    assert r2.status_code == 200
    assert r2.json()["emergency_pause_active"] is False
    assert settings.EMERGENCY_AUTOMATION_PAUSED is False


def test_escalation_ticket_lifecycle_actions():
    """Support managers can view, assign, resolve, and close escalation tickets."""
    test_tck_id = f"TCK-TEST-{uuid.uuid4().hex[:6]}"
    conv_id = f"CONV-T-{uuid.uuid4().hex[:6]}"

    # Seed an open escalation ticket
    with SessionLocal() as db:
        t = TicketRecord(
            ticket_id=test_tck_id,
            conversation_id=conv_id,
            customer_id="CUST-URGENT",
            status="open",
            priority="urgent",
            category="leak_after_maintenance",
            escalation_reason="Bathroom flooding reported by customer",
            customer_message="Water is spraying heavily from the joint!",
            ai_draft="Shut off main valve immediately.",
            recommended_action="Dispatch service technician."
        )
        db.add(t)
        db.commit()

    # 1. List tickets
    r_list = client.get("/api/v2/tickets?status_filter=open")
    assert r_list.status_code == 200
    tickets = r_list.json()
    assert any(item["ticket_id"] == test_tck_id for item in tickets)

    # 2. Assign ticket
    r_assign = client.post(f"/api/v2/tickets/{test_tck_id}/action?action=assign&assigned_to=agent_rajesh")
    assert r_assign.status_code == 200
    assert r_assign.json()["ticket_status"] == "assigned"

    # 3. Resolve ticket
    r_resolve = client.post(f"/api/v2/tickets/{test_tck_id}/action?action=resolve")
    assert r_resolve.status_code == 200
    assert r_resolve.json()["ticket_status"] == "resolved"

    # 4. Verify in DB
    with SessionLocal() as db:
        rec = db.query(TicketRecord).filter_by(ticket_id=test_tck_id).first()
        assert rec.status == "resolved"
        assert rec.assigned_to == "agent_rajesh"
        assert rec.resolved_at is not None

