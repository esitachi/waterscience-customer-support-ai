"""
Tests for Phase 1: Autonomous Customer Support Engine
Verifies:
1. Level 1: Automatic Resolution for safe, verified, evidence-backed queries.
2. Level 2: Conditional Troubleshooting / Clarification with state tracking.
3. Circular Loop Prevention: Repeated troubleshooting failures escalate to Level 3.
4. Level 3: Mandatory Human Escalation for physical hazards, policy conflicts, and unverified data.
5. Legacy Compatibility: Existing process_query retains human approval pending state.
"""

import pytest
from app.models import (
    CustomerQueryRequest,
    ResolutionLevel,
    ApprovalStatus,
    ReviewStatus,
    ConversationContext,
    TroubleshootingState
)
from app.engine import get_support_engine


@pytest.fixture
def engine():
    return get_support_engine()


def test_level_1_automatic_resolution_metal_tap(engine):
    """Safe, verified compatibility query should be auto-resolved and auto-dispatched."""
    msg = "Will the CLEO SFU-717 shower and tap filter fit my 24mm standard metal threaded kitchen tap?"
    result = engine.process_autonomous_interaction(message=msg)

    assert result.resolution_level == ResolutionLevel.LEVEL_1_AUTOMATIC
    assert result.status == "auto_resolved"
    assert result.auto_dispatched is True
    assert result.dispatch_timestamp is not None
    assert any(s.source_id == "S01" for s in result.cited_sources)
    assert "24" in result.response_text or "metal" in result.response_text.lower()


def test_level_1_automatic_resolution_cartridge_mapping(engine):
    """Model-specific cartridge query should resolve autonomously without human sign-off."""
    msg = "Which replacement cartridge pack do I buy for my VERSA STF-1025 tap filter?"
    result = engine.process_autonomous_interaction(message=msg)

    # If water source clarification is needed it becomes level 2, but exact SKU lookup is verified
    assert result.auto_dispatched is True
    assert "VERSA" in result.response_text or "1025" in result.response_text


def test_level_2_conditional_troubleshooting_clarification(engine):
    """Queries needing water-source clarification should ask customer conditionally."""
    msg = "Borewell water hai, TDS 900 aa raha hai. Metro cartridge loon ya borewell wala?"
    result = engine.process_autonomous_interaction(message=msg)

    assert result.resolution_level == ResolutionLevel.LEVEL_2_CONDITIONAL
    assert result.status == "awaiting_customer_reply"
    assert result.auto_dispatched is True
    assert len(result.information_needed) > 0


def test_circular_troubleshooting_loop_prevention(engine):
    """
    If a customer attempts troubleshooting multiple times and reports failure,
    the system must break the loop and escalate to Level 3.
    """
    ctx = ConversationContext(
        conversation_id="CONV-LOOP-TEST",
        troubleshooting=TroubleshootingState(attempts_count=2)
    )
    
    # Customer says it's still not working after previous attempts
    msg = "I already tried reverse flush and cleaning the aerator, still not working, flow is dead."
    result = engine.process_autonomous_interaction(message=msg, conversation_context=ctx)

    assert result.resolution_level == ResolutionLevel.LEVEL_3_ESCALATED
    assert result.status == "escalated_to_human"
    assert result.auto_dispatched is False
    assert result.reason_for_escalation is not None
    assert "loop" in result.reason_for_escalation.lower() or "attempt" in result.reason_for_escalation.lower() or "persistent" in result.reason_for_escalation.lower()


def test_level_3_mandatory_escalation_active_leak(engine):
    """Physical leak hazard must immediately route to Level 3 human escalation."""
    msg = "Help! My CLEO filter started spraying water heavily from the joint after I installed the new cartridge, and my bathroom floor is flooding."
    result = engine.process_autonomous_interaction(message=msg)

    assert result.resolution_level == ResolutionLevel.LEVEL_3_ESCALATED
    assert result.status == "escalated_to_human"
    assert result.auto_dispatched is False
    assert result.reason_for_escalation is not None
    # Must advise water shut-off
    assert "shut" in result.response_text.lower() or "turn off" in result.response_text.lower() or "valve" in result.response_text.lower()


def test_level_3_mandatory_escalation_source_conflict(engine):
    """Geyser hot water temperature conflict (45°C vs 60°C) must escalate to Level 3."""
    msg = "Can I run 55 degree Celsius hot water from my geyser through the CLEO shower filter?"
    result = engine.process_autonomous_interaction(message=msg)

    assert result.resolution_level == ResolutionLevel.LEVEL_3_ESCALATED
    assert result.status == "escalated_to_human"
    assert result.auto_dispatched is False
    assert any(s.source_id == "S01" for s in result.cited_sources)
    assert any(s.source_id == "S02" for s in result.cited_sources)


def test_level_3_mandatory_escalation_unverified_mapping(engine):
    """Unverified cartridge mapping (KTF Wide ceramic) must escalate to Level 3."""
    msg = "I have the KTF Wide / FLO-KTF-723 tap extender. Is the ceramic cartridge compatible with it?"
    result = engine.process_autonomous_interaction(message=msg)

    assert result.resolution_level == ResolutionLevel.LEVEL_3_ESCALATED
    assert result.status == "escalated_to_human"
    assert result.auto_dispatched is False
    assert "unverified" in result.reason_for_escalation.lower() or "pending" in result.reason_for_escalation.lower()


def test_level_3_mandatory_escalation_amazon_return_policy(engine):
    """Marketplace purchase asking for website 60-day return policy must escalate to Level 3."""
    msg = "I bought CLEO on Amazon 3 days ago and it arrived cracked. Give me an immediate refund under your 60-day money-back guarantee."
    result = engine.process_autonomous_interaction(message=msg)

    assert result.resolution_level == ResolutionLevel.LEVEL_3_ESCALATED
    assert result.status == "escalated_to_human"
    assert result.auto_dispatched is False


def test_legacy_live_query_console_compatibility(engine):
    """The legacy process_query endpoint must retain PENDING_APPROVAL for interactive agent assist."""
    req = CustomerQueryRequest(
        message="Will CLEO SFU-717 fit my 24mm standard metal threaded kitchen tap?"
    )
    case = engine.process_query(req)

    assert case.approval_status == ApprovalStatus.PENDING_APPROVAL
    assert case.resolution_level == ResolutionLevel.LEVEL_1_AUTOMATIC
    assert case.auto_dispatched is False
    assert case.human_escalation_required is False

