"""
Evaluation Test Suite for Newly Added WaterScience Cartridge Knowledge:
- VERSA STF-1025 -> VERSA-STF-RC-1025-HHC (pack of 2)
- VERSA SCF-725 -> VERSA-SCF-RC-725 (pack of 3)
- PURO HFF-526-N and PURO HFF-626-N -> Shared pack of 6
- PURO HFS-625 -> Negative compatibility rule (no replacement cartridge; do not recommend HFF)
- RENO Cygnus -> Negative rule (salt regeneration, not a cartridge product)
- RIO-MLF-119 -> RIO-RC-119 (model-specific)
- RIO universal 10"/20" -> Model-specific requirement guardrail
- KTF Wide / FLO-KTF-723 -> Unverified pending vendor confirmation
- CLEO normalized aliases search (CLEO-RC-100-SC / CLEO-RC-100-HHC)
"""

import pytest
from app.config import settings
from app.models import CustomerQueryRequest, ApprovalStatus, ReviewStatus
from app.engine import get_support_engine

@pytest.fixture
def engine(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")
    eng = get_support_engine()
    eng.kb.load()
    return eng

def test_kb_has_all_14_sources_and_15_products(engine):
    assert len(engine.kb.sources) >= 13, f"Expected at least 13 sources, got {len(engine.kb.sources)}"
    assert "S11" in engine.kb.sources
    assert "S12" in engine.kb.sources
    assert "S13" in engine.kb.sources
    assert len(engine.kb.products) >= 15, f"Expected at least 15 products, got {len(engine.kb.products)}"
    assert "VERSA_STF_1025" in engine.kb.products
    assert "VERSA_SCF_725" in engine.kb.products
    assert "PURO_HFF_526_N" in engine.kb.products
    assert "PURO_HFF_626_N" in engine.kb.products
    assert "RIO_MLF_119" in engine.kb.products

def test_query_versa_stf_1025_cartridge(engine):
    req = CustomerQueryRequest(
        message="Which replacement cartridge should I buy for my VERSA STF-1025 shower and tap filter?",
        product_hint="VERSA STF-1025"
    )
    res = engine.process_query(req)
    assert res.approval_status == ApprovalStatus.PENDING_APPROVAL
    assert not res.human_escalation_required
    assert "VERSA-STF-RC-1025-HHC" in res.draft_response
    assert "pack of 2" in res.draft_response.lower()
    assert any(s.source_id in ["S10", "S11"] for s in res.cited_sources)

def test_query_versa_scf_725_cartridge(engine):
    req = CustomerQueryRequest(
        message="Need cartridge replacement for VERSA SCF-725 shower filter",
        product_hint="VERSA SCF-725"
    )
    res = engine.process_query(req)
    assert res.approval_status == ApprovalStatus.PENDING_APPROVAL
    assert not res.human_escalation_required
    assert "VERSA-SCF-RC-725" in res.draft_response
    assert "pack of 3" in res.draft_response.lower()
    assert any(s.source_id in ["S10", "S11"] for s in res.cited_sources)

def test_query_puro_hff_shared_cartridge(engine):
    req = CustomerQueryRequest(
        message="Where can I order replacement cartridges for PURO HFF-526-N health faucet?",
        product_hint="PURO HFF-526-N"
    )
    res = engine.process_query(req)
    assert res.approval_status == ApprovalStatus.PENDING_APPROVAL
    assert not res.human_escalation_required
    assert "pack of 6" in res.draft_response.lower()
    assert any(s.source_id in ["S10", "S12"] for s in res.cited_sources)
    assert "not compatible with the puro hfs-625" in res.draft_response.lower() or "not compatible with puro hfs-625" in res.draft_response.lower()

def test_query_puro_hfs_625_negative_compatibility(engine):
    # Customer asks for replacement cartridge for PURO HFS-625
    req = CustomerQueryRequest(
        message="I have PURO HFS-625 health faucet. Can I use the PURO HFF cartridge pack of 6 for it?",
        product_hint="PURO HFS-625"
    )
    res = engine.process_query(req)
    assert res.approval_status == ApprovalStatus.PENDING_APPROVAL
    # Must explicitly state NO replacement cartridge and warn against PURO HFF
    assert "no replacement cartridge" in res.draft_response.lower()
    assert "not compatible" in res.draft_response.lower()
    assert "hff" in res.draft_response.lower()
    assert any(s.source_id == "S09" for s in res.cited_sources)
    assert any("PURO HFS-625 has no replacement cartridge" in g for g in res.applied_guardrails)

def test_query_reno_cygnus_negative_cartridge_rule(engine):
    # Customer asks about replacement cartridge for RENO Cygnus
    req = CustomerQueryRequest(
        message="When do I need to change the cartridge for RENO Cygnus water softener?",
        product_hint="RENO Cygnus"
    )
    res = engine.process_query(req)
    assert res.approval_status == ApprovalStatus.PENDING_APPROVAL
    # Must state it uses salt regeneration and is NOT a replacement cartridge product
    assert "not a replacement-cartridge product" in res.draft_response.lower() or "not a replacement cartridge product" in res.draft_response.lower()
    assert "salt" in res.draft_response.lower()
    assert any("RENO Cygnus uses salt regeneration" in g for g in res.applied_guardrails)

def test_query_rio_mlf_119_model_specific(engine):
    req = CustomerQueryRequest(
        message="What is the replacement cartridge for RIO-MLF-119 mainline filter?",
        product_hint="RIO-MLF-119"
    )
    res = engine.process_query(req)
    assert res.approval_status == ApprovalStatus.PENDING_APPROVAL
    assert "RIO-RC-119" in res.draft_response
    assert "model-specific" in res.draft_response.lower()
    assert any(s.source_id in ["S10", "S13"] for s in res.cited_sources)

def test_query_rio_universal_assumption_escalates(engine):
    # Customer asks if any universal 10-inch cartridge fits
    req = CustomerQueryRequest(
        message="Can I use any universal 10 inch mainline cartridge inside my RIO filter?",
        product_hint="RIO-MLF-119"
    )
    res = engine.process_query(req)
    assert res.approval_status == ApprovalStatus.PENDING_APPROVAL
    assert res.human_escalation_required is True
    assert any("10-inch/20-inch RIO cartridges are not universal" in g for g in res.applied_guardrails)

def test_query_ktf_wide_ceramic_unverified_mapping(engine):
    # Customer asks to buy ceramic replacement cartridge for KTF Wide / FLO-KTF-723
    req = CustomerQueryRequest(
        message="I want to buy replacement ceramic cartridge for my KTF Wide FLO-KTF-723 tap extender.",
        product_hint="FLO-KTF-723"
    )
    res = engine.process_query(req)
    assert res.approval_status == ApprovalStatus.PENDING_APPROVAL
    assert res.human_escalation_required is True
    assert "unverified" in res.draft_response.lower()
    assert "pending vendor confirmation" in res.draft_response.lower()
    assert any("unverified" in g.lower() for g in res.applied_guardrails)

def test_query_cleo_normalized_alias_search(engine):
    # Search by normalized alias CLEO-RC-100-SC or CLEO-RC-100-HHC
    prod_sc = engine.kb.find_product_by_name("CLEO-RC-100-SC")
    assert prod_sc is not None
    assert prod_sc[0] == "CLEO_REPLACEMENT_CARTRIDGE"

    prod_hhc = engine.kb.find_product_by_name("CLEO-RC-100-HHC")
    assert prod_hhc is not None
    assert prod_hhc[0] == "CLEO_REPLACEMENT_CARTRIDGE"

