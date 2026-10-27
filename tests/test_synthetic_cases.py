import json
import pytest
from pathlib import Path
from app.config import settings
from app.models import CustomerQueryRequest, ApprovalActionRequest, ApprovalStatus
from app.engine import get_support_engine

@pytest.fixture
def engine():
    return get_support_engine()

@pytest.fixture
def synthetic_cases():
    with open(settings.SYNTHETIC_CASES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["cases"]

def test_kb_loaded(engine):
    assert len(engine.kb.sources) >= 10
    assert len(engine.kb.products) >= 6
    assert "CLEO_SFU_717" in engine.kb.products
    assert "IRIS_WMF_325" in engine.kb.products

def test_all_20_synthetic_cases_execute(engine, synthetic_cases):
    assert len(synthetic_cases) == 20
    for c in synthetic_cases:
        req = CustomerQueryRequest(
            case_id=c["case_id"],
            message=c["synthetic_customer_message"],
            product_hint=c.get("product")
        )
        case = engine.process_query(req)
        assert case.case_id == c["case_id"]
        assert case.approval_status == ApprovalStatus.PENDING_APPROVAL
        assert len(case.draft_response) > 20
        assert len(case.cited_sources) > 0

def test_syn_001_cleo_tap_fitment(engine):
    req = CustomerQueryRequest(
        case_id="SYN-001",
        message="Hi, will CLEO SFU-717 fit my 24 mm metal kitchen tap?",
        product_hint="CLEO SFU-717"
    )
    case = engine.process_query(req)
    assert not case.human_escalation_required
    assert "24 mm" in case.draft_response
    assert "metal" in case.draft_response.lower()
    assert "plastic" in case.draft_response.lower()
    assert any(s.source_id == "S01" for s in case.cited_sources)

def test_syn_002_plastic_tap_limitation(engine):
    req = CustomerQueryRequest(
        case_id="SYN-002",
        message="Mera tap plastic hai, CLEO lag jayega kya?",
        product_hint="CLEO SFU-717"
    )
    case = engine.process_query(req)
    assert not case.human_escalation_required
    assert "plastic" in case.draft_response.lower()
    assert "nahi" in case.draft_response.lower() or "not" in case.draft_response.lower()
    assert any(s.source_id == "S01" for s in case.cited_sources)

def test_syn_003_cartridge_selection_chlorine_clarification(engine):
    req = CustomerQueryRequest(
        case_id="SYN-003",
        message="Borewell water hai, TDS 900 aa raha hai. Metro cartridge loon ya borewell wala?",
        product_hint="CLEO replacement cartridge"
    )
    case = engine.process_query(req)
    assert not case.human_escalation_required
    assert len(case.information_needed) > 0
    assert "chlorine" in case.draft_response.lower()
    assert any(s.source_id == "S02" for s in case.cited_sources)

def test_syn_004_tds_expectation(engine):
    req = CustomerQueryRequest(
        case_id="SYN-004",
        message="Filter laga diya but TDS meter same hai. Product fake hai kya?",
        product_hint="CLEO SFU-717"
    )
    case = engine.process_query(req)
    assert not case.human_escalation_required
    assert "tds" in case.draft_response.lower()
    assert "not" in case.draft_response.lower() or "nahi" in case.draft_response.lower()
    assert "safe to drink" not in case.draft_response.lower()

def test_syn_005_low_flow_guidance(engine):
    req = CustomerQueryRequest(
        case_id="SYN-005",
        message="CLEO ka flow bahut slow ho gaya after 2 weeks, what to do?",
        product_hint="CLEO SFU-717"
    )
    case = engine.process_query(req)
    assert not case.human_escalation_required
    assert "reverse flush" in case.draft_response.lower()
    assert "sediment" in case.draft_response.lower()

def test_syn_006_leak_safety_and_escalation(engine):
    req = CustomerQueryRequest(
        case_id="SYN-006",
        message="Cartridge change ke baad filter ke beech se paani leak ho raha hai.",
        product_hint="CLEO replacement cartridge"
    )
    case = engine.process_query(req)
    assert case.human_escalation_required
    assert "leak" in case.reason_for_escalation.lower()
    assert any("photo" in x.lower() or "video" in x.lower() for x in case.information_needed)
    assert "shut off" in case.draft_response.lower()

def test_syn_007_temperature_conflict_escalation(engine):
    req = CustomerQueryRequest(
        case_id="SYN-007",
        message="Can I run 55 degree hot water through SFU-717 daily?",
        product_hint="CLEO SFU-717"
    )
    case = engine.process_query(req)
    assert case.human_escalation_required
    assert "conflict" in case.reason_for_escalation.lower()
    assert "45" in case.draft_response
    assert "60" in case.draft_response
    source_ids = [s.source_id for s in case.cited_sources]
    assert "S01" in source_ids and "S02" in source_ids

def test_syn_008_warranty_claim_no_automatic_confirmation(engine):
    req = CustomerQueryRequest(
        case_id="SYN-008",
        message="My CLEO body cracked within warranty. Replace it now please.",
        product_hint="CLEO SFU-717"
    )
    case = engine.process_query(req)
    assert case.human_escalation_required
    assert "invoice" in case.draft_response.lower()
    assert "photo" in case.draft_response.lower()

def test_syn_009_website_return_conditional(engine):
    req = CustomerQueryRequest(
        case_id="SYN-009",
        message="Bought CLEO from your website 30 days ago. It is not suitable for my tap. Refund chahiye.",
        product_hint="CLEO SFU-717"
    )
    case = engine.process_query(req)
    assert case.human_escalation_required
    assert "60-day" in case.draft_response
    assert "order" in case.draft_response.lower()

def test_syn_010_amazon_channel_isolation(engine):
    req = CustomerQueryRequest(
        case_id="SYN-010",
        message="Amazon se filter aaya broken. WaterScience 60-day refund do.",
        product_hint="CLEO SFU-717"
    )
    case = engine.process_query(req)
    assert case.human_escalation_required
    assert "amazon" in case.draft_response.lower()
    assert "exclusively" in case.draft_response.lower() or "marketplace" in case.draft_response.lower()

def test_syn_011_damaged_on_arrival(engine):
    req = CustomerQueryRequest(
        case_id="SYN-011",
        message="Parcel abhi khola, body damaged hai. Please send replacement today."
    )
    case = engine.process_query(req)
    assert case.human_escalation_required
    assert any("photo" in x.lower() for x in case.information_needed)

def test_syn_012_delivery_tracking_no_false_eta(engine):
    req = CustomerQueryRequest(
        case_id="SYN-012",
        message="Order 4 days se stuck hai. Kab aayega?"
    )
    case = engine.process_query(req)
    assert not case.human_escalation_required
    assert "2-3" in case.draft_response
    assert "tracking" in case.draft_response.lower()

def test_syn_013_iris_washing_machine_compatibility(engine):
    req = CustomerQueryRequest(
        case_id="SYN-013",
        message="IRIS filter meri front-load LG machine par fit hoga?",
        product_hint="IRIS-WMF-325"
    )
    case = engine.process_query(req)
    assert not case.human_escalation_required
    assert "automatic" in case.draft_response.lower()
    assert "adapter" in case.draft_response.lower()

def test_syn_014_iris_cartridge_life(engine):
    req = CustomerQueryRequest(
        case_id="SYN-014",
        message="Top load machine ke IRIS cartridge ko sirf 2 months hue, ab replace karna hoga?",
        product_hint="IRIS-WMF-325"
    )
    case = engine.process_query(req)
    assert not case.human_escalation_required
    assert "3-4" in case.draft_response
    assert "top-load" in case.draft_response.lower()

def test_syn_015_kitchen_filter_incompatible_tap(engine):
    req = CustomerQueryRequest(
        case_id="SYN-015",
        message="KTF filter 26 mm plastic tap pe fit hoga?",
        product_hint="KTF variant unknown"
    )
    case = engine.process_query(req)
    assert case.human_escalation_required
    assert "26 mm" in case.draft_response

def test_syn_016_kitchen_filter_potable_safety(engine):
    req = CustomerQueryRequest(
        case_id="SYN-016",
        message="KTF se paani filter hone ke baad direct peena safe hai?",
        product_hint="KTF Kitchen Tap Extender"
    )
    case = engine.process_query(req)
    assert case.human_escalation_required
    assert "not certify" in case.draft_response.lower() or "advise against" in case.draft_response.lower()

def test_syn_017_whole_home_consultation(engine):
    req = CustomerQueryRequest(
        case_id="SYN-017",
        message="RENO 2 bathroom ke liye total installation cost batao and kal install kar do.",
        product_hint="RENO Cygnus"
    )
    case = engine.process_query(req)
    assert case.human_escalation_required
    assert "consultation" in case.draft_response.lower() or "cannot" in case.draft_response.lower()

def test_syn_018_puro_health_faucet_fault(engine):
    req = CustomerQueryRequest(
        case_id="SYN-018",
        message="PURO health faucet leak kar raha hai and trigger work nahi kar raha.",
        product_hint="PURO HFS-625"
    )
    case = engine.process_query(req)
    assert case.human_escalation_required
    assert "shut off" in case.draft_response.lower() or "valve" in case.draft_response.lower()

def test_syn_019_medical_claims_rejection(engine):
    req = CustomerQueryRequest(
        case_id="SYN-019",
        message="Will CLEO stop my hair fall in one week? Doctor nahi jaana padega na?",
        product_hint="CLEO SFU-717"
    )
    case = engine.process_query(req)
    assert case.human_escalation_required
    assert "not medical" in case.draft_response.lower() or "not a medical" in case.draft_response.lower()
    assert "dermatologist" in case.draft_response.lower() or "doctor" in case.draft_response.lower()

def test_syn_020_unknown_product_identification_no_immediate_escalation(engine):
    req = CustomerQueryRequest(
        case_id="SYN-020",
        message="Need replacement filter urgently. Old one photo bhej diya, model yaad nahi."
    )
    case = engine.process_query(req)
    # SYN-020 specification: Requests product identification first and escalates only if product cannot subsequently be identified
    assert not case.human_escalation_required
    assert case.review_status == "needs_clarification"
    assert "photo" in case.draft_response.lower() or "sku" in case.draft_response.lower() or "model" in case.draft_response.lower()
    assert any("model" in x.lower() or "photo" in x.lower() for x in case.information_needed)

def test_human_approval_workflow(engine):
    req = CustomerQueryRequest(
        case_id="TEST-APPROVAL-01",
        message="Will CLEO SFU-717 fit my 24 mm metal kitchen tap?",
        product_hint="CLEO SFU-717"
    )
    case = engine.process_query(req)
    assert case.approval_status == ApprovalStatus.PENDING_APPROVAL

    # Reviewer approves
    updated = engine.update_approval(case.case_id, ApprovalActionRequest(
        action="approve",
        reviewer_comment="Verified against S01"
    ))
    assert updated.approval_status == ApprovalStatus.APPROVED
    assert updated.reviewer_comment == "Verified against S01"

    # Reviewer edits
    updated2 = engine.update_approval(case.case_id, ApprovalActionRequest(
        action="edit",
        edited_response="Edited custom response for customer.",
        reviewer_comment="Tailored tone"
    ))
    assert updated2.approval_status == ApprovalStatus.EDITED
    assert updated2.draft_response == "Edited custom response for customer."
