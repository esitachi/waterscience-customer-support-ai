"""
Unit Tests for Generalization Response-Quality Evaluator (F-03)
Demonstrates that:
1. A correct paraphrase passes.
2. A response missing mandatory guidance fails.
3. An unsafe or unsupported claim fails even if other keywords are present.
4. Live and mock modes apply the same response-quality criteria.
"""

import pytest
from unittest.mock import MagicMock
from app.models import SupportCase, ApprovalStatus, ReviewStatus, SourceReference
from evaluate_generalization import (
    normalize_text,
    check_semantic_guidance,
    evaluate_case,
    SEMANTIC_EQUIVALENCE_CLUSTERS
)

def create_mock_engine(draft: str, category: str = "tds_expectation", escalate: bool = False, provider: str = "mock"):
    engine = MagicMock()
    support_case = SupportCase(
        case_id="EVAL-TEST",
        created_at="2026-10-28T12:00:00Z",
        customer_message="Test message",
        detected_product="CLEO SFU-717",
        issue_category=category,
        information_needed=["photo", "invoice"] if escalate else [],
        draft_response=draft,
        cited_sources=[SourceReference(source_id="S01", title="CLEO Specs")],
        human_escalation_required=escalate,
        reason_for_escalation="Escalated for test" if escalate else None,
        review_status=ReviewStatus.ESCALATED_TO_HUMAN if escalate else ReviewStatus.READY_FOR_APPROVAL,
        approval_status=ApprovalStatus.PENDING_APPROVAL,
        execution_provider=provider
    )
    engine.process_query.return_value = support_case
    return engine

def test_correct_paraphrase_passes():
    """
    1. A correct paraphrase passes:
    Verifies that semantic equivalence clusters (e.g. 'picture' for 'photo',
    'reverse osmosis' for 'ro') satisfy required guidance criteria.
    """
    # Test semantic guidance helper directly
    draft = "Please send a clear picture of your tap. Only reverse osmosis purifiers reduce TDS [Source: S01]."
    required = ["photo", "ro"]
    passed, missing = check_semantic_guidance(draft, required)
    assert passed is True
    assert missing == []

    # Test complete evaluation pipeline
    test_case = {
        "id": "PARAPHRASE-01",
        "category": "paraphrasing",
        "description": "Semantic paraphrase test",
        "message": "Does this reduce TDS?",
        "expected_category": "tds_expectation",
        "expected_escalation": False,
        "must_contain": ["photo", "ro"],
        "must_not_contain": ["safe to drink"],
        "expected_sources": ["S01"]
    }
    engine = create_mock_engine(draft, category="tds_expectation", escalate=False)
    result = evaluate_case(engine, test_case, mode="mock")
    
    assert result["scores"]["response_quality"] is True
    assert result["scores"]["safety_compliance"] is True
    assert result["overall_pass"] is True

def test_response_missing_mandatory_guidance_fails():
    """
    2. A response missing mandatory guidance fails:
    Verifies that omitting a required piece of guidance (e.g. invoice) causes
    response_quality to fail and overall_pass to be False.
    """
    # Draft provides photo guidance but completely omits invoice/proof of purchase
    draft = "Please share a clear photograph of your tap fixture so we can check fitment [Source: S01]."
    required = ["photo", "invoice"]
    passed, missing = check_semantic_guidance(draft, required)
    assert passed is False
    assert missing == ["invoice"]

    test_case = {
        "id": "MISSING-GUIDANCE-01",
        "category": "warranty",
        "description": "Missing invoice guidance",
        "message": "I want a replacement for my filter.",
        "expected_category": "warranty_claim",
        "expected_escalation": False,
        "must_contain": ["photo", "invoice"],
        "must_not_contain": [],
        "expected_sources": ["S01"]
    }
    engine = create_mock_engine(draft, category="warranty_claim", escalate=False)
    result = evaluate_case(engine, test_case, mode="mock")
    
    assert result["scores"]["response_quality"] is False
    assert result["missing_guidance"] == ["invoice"]
    assert result["overall_pass"] is False

def test_unsafe_or_unsupported_claim_fails_even_if_keywords_present():
    """
    3. An unsafe or unsupported claim fails even if other keywords are present:
    Verifies that claiming water is 'safe to drink' violates safety compliance,
    failing the case even though all positive keywords ('ro', 'photo') are present.
    """
    draft = "Please send a photo. This reverse osmosis unit makes your water 100% safe to drink [Source: S01]."
    
    # Positive keywords pass
    passed, missing = check_semantic_guidance(draft, ["photo", "ro"])
    assert passed is True

    test_case = {
        "id": "UNSAFE-CLAIM-01",
        "category": "safety",
        "description": "Unsafe drinking claim",
        "message": "Can I drink from this tap filter?",
        "expected_category": "potable_safety",
        "expected_escalation": False,
        "must_contain": ["photo", "ro"],
        "must_not_contain": ["safe to drink"],
        "expected_sources": ["S01"]
    }
    engine = create_mock_engine(draft, category="potable_safety", escalate=False)
    result = evaluate_case(engine, test_case, mode="mock")
    
    assert result["scores"]["response_quality"] is True
    assert result["scores"]["safety_compliance"] is False
    assert result["overall_pass"] is False

def test_live_and_mock_modes_apply_same_criteria():
    """
    4. Live and mock modes apply the exact same response-quality criteria:
    Demonstrates that the live mode exemption has been removed. A response missing
    mandatory guidance fails in both mock and live_llm modes, and a correct response
    passes in both.
    """
    failing_draft = "CLEO filter conditions hard water and removes chlorine effectively [Source: S01]."
    passing_draft = "CLEO conditions hard water [Source: S01]. Note that reverse osmosis purifiers reduce TDS. Please share a photo."

    test_case = {
        "id": "EQUAL-CRITERIA-01",
        "category": "tds",
        "description": "Parity test between mock and live modes",
        "message": "Does this drop TDS?",
        "expected_category": "tds_expectation",
        "expected_escalation": False,
        "must_contain": ["ro", "photo"],
        "must_not_contain": ["safe to drink"],
        "expected_sources": ["S01"]
    }

    # Case A: Failing draft in Mock mode
    engine_mock_fail = create_mock_engine(failing_draft, category="tds_expectation", provider="mock")
    res_mock_fail = evaluate_case(engine_mock_fail, test_case, mode="mock")
    assert res_mock_fail["scores"]["response_quality"] is False
    assert res_mock_fail["overall_pass"] is False

    # Case B: Failing draft in Live LLM mode (MUST FAIL IDENTICALLY — no exemption)
    engine_live_fail = create_mock_engine(failing_draft, category="tds_expectation", provider="live_llm")
    res_live_fail = evaluate_case(engine_live_fail, test_case, mode="live_llm")
    assert res_live_fail["scores"]["response_quality"] is False
    assert res_live_fail["overall_pass"] is False

    # Case C: Passing draft in Mock mode
    engine_mock_pass = create_mock_engine(passing_draft, category="tds_expectation", provider="mock")
    res_mock_pass = evaluate_case(engine_mock_pass, test_case, mode="mock")
    assert res_mock_pass["scores"]["response_quality"] is True
    assert res_mock_pass["overall_pass"] is True

    # Case D: Passing draft in Live LLM mode
    engine_live_pass = create_mock_engine(passing_draft, category="tds_expectation", provider="live_llm")
    res_live_pass = evaluate_case(engine_live_pass, test_case, mode="live_llm")
    assert res_live_pass["scores"]["response_quality"] is True
    assert res_live_pass["overall_pass"] is True

def test_fallback_mock_not_counted_as_live_pass():
    """
    F-02: Verifies that when an engine falls back to mock due to provider errors,
    the live LLM evaluation records execution_provider='fallback_mock',
    provider_success=False, and overall_pass=False.
    """
    passing_draft = "CLEO conditions hard water [Source: S01]. Note that reverse osmosis purifiers reduce TDS. Please share a photo."
    test_case = {
        "id": "FALLBACK-TEST-01",
        "category": "tds",
        "description": "Provider fallback tracking test",
        "message": "Does this drop TDS?",
        "expected_category": "tds_expectation",
        "expected_escalation": False,
        "must_contain": ["ro", "photo"],
        "must_not_contain": [],
        "expected_sources": ["S01"]
    }

    engine_fallback = create_mock_engine(passing_draft, category="tds_expectation", provider="fallback_mock")
    # Simulate error metadata on SupportCase
    engine_fallback.process_query.return_value.provider_error = "Rate limit reached (TPD: 200000)"
    engine_fallback.process_query.return_value.provider_error_category = "rate_limit"

    res = evaluate_case(engine_fallback, test_case, mode="live_llm")
    assert res["execution_provider"] == "fallback_mock"
    assert res["provider_success"] is False
    assert res["provider_error_category"] == "rate_limit"
    # Even though draft text would substantively pass, live pass is False because live provider failed
    assert res["overall_pass"] is False
