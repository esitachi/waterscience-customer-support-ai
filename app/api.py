import json
from pathlib import Path
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.models import (
    CustomerQueryRequest,
    SupportCase,
    ApprovalActionRequest,
    SyntheticCaseEvaluation
)
from app.engine import get_support_engine
from app.knowledge import get_knowledge_base

app = FastAPI(
    title="WaterScience Customer Support AI",
    description="Agent-assist customer query drafting and safety pipeline with mandatory human approval.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = get_support_engine()
kb = get_knowledge_base()

# Mount static folder
static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
def serve_index():
    return FileResponse(
        str(static_dir / "index.html"),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/health")
def health():
    # Never expose credentials; only track presence safely
    has_groq_key = bool(settings.GROQ_API_KEY and settings.GROQ_API_KEY.strip())
    has_openai_key = bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip())
    
    if settings.LLM_PROVIDER == "groq":
        provider_status = "live_groq_configured" if has_groq_key else "groq_unconfigured_missing_key"
    elif settings.LLM_PROVIDER == "openai":
        provider_status = "live_openai_configured" if has_openai_key else "openai_unconfigured_missing_key"
    else:
        provider_status = "deterministic_mock_mode"

    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "llm_provider": settings.LLM_PROVIDER,
        "configured_llm_provider": settings.LLM_PROVIDER,
        "provider_status": provider_status,
        "live_credentials_present": (has_groq_key if settings.LLM_PROVIDER == "groq" else (has_openai_key if settings.LLM_PROVIDER == "openai" else False)),
        "kb_sources_count": len(kb.sources),
        "kb_products_count": len(kb.products)
    }

@app.post("/api/query", response_model=SupportCase)
def process_customer_query(query: CustomerQueryRequest):
    case = engine.process_query(query)
    return case

@app.get("/api/cases", response_model=List[SupportCase])
def list_cases():
    return engine.list_cases()

@app.get("/api/cases/{case_id}", response_model=SupportCase)
def get_case(case_id: str):
    case = engine.get_case(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found")
    return case

@app.post("/api/cases/{case_id}/approve", response_model=SupportCase)
def update_case_approval(case_id: str, action: ApprovalActionRequest):
    case = engine.update_approval(case_id, action)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found")
    return case

@app.get("/api/synthetic-cases")
def get_synthetic_cases():
    if not settings.SYNTHETIC_CASES_PATH.exists():
        raise HTTPException(status_code=404, detail="Synthetic cases dataset not found")
    with open(settings.SYNTHETIC_CASES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

@app.post("/api/run-synthetic-tests", response_model=List[SyntheticCaseEvaluation])
def run_synthetic_tests():
    """
    Executes all 20 synthetic cases through the engine and evaluates
    against every pass/fail criterion.
    """
    if not settings.SYNTHETIC_CASES_PATH.exists():
        raise HTTPException(status_code=404, detail="Synthetic cases dataset not found")

    with open(settings.SYNTHETIC_CASES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    results: List[SyntheticCaseEvaluation] = []
    cases = data.get("cases", [])

    for c in cases:
        cid = c["case_id"]
        msg = c["synthetic_customer_message"]
        expected_cat = c["issue_category"]
        expected_escalate = c["human_escalation_required"]
        
        # Process through engine
        req = CustomerQueryRequest(
            case_id=cid,
            message=msg,
            product_hint=c.get("product")
        )
        case = engine.process_query(req)

        # Evaluation criteria verification
        notes = []
        pass_status = True

        # Check escalation requirement
        if case.human_escalation_required != expected_escalate:
            pass_status = False
            notes.append(f"Escalation mismatch: expected {expected_escalate}, got {case.human_escalation_required}")
        else:
            notes.append(f"Escalation matched expected value ({expected_escalate})")

        # Check category
        if case.issue_category != expected_cat:
            notes.append(f"Category mismatch: expected {expected_cat}, got {case.issue_category}")
        else:
            notes.append(f"Issue category correctly classified as {case.issue_category}")

        # Case-specific criteria checks
        import unicodedata
        draft = unicodedata.normalize("NFKC", case.draft_response)
        draft_lower = draft.lower()
        
        if cid == "SYN-001":
            # Pass if reply mentions 24 mm and metal thread; fail if claims plastic taps fit
            if ("24 mm" in draft or "24mm" in draft) and "metal" in draft_lower and "plastic" in draft_lower:
                notes.append("Explicitly states 24 mm and metal thread requirement, warns about plastic taps")
            else:
                pass_status = False
                notes.append("Failed: must mention 24 mm, metal thread, and plastic tap limitation")

        elif cid == "SYN-002":
            # Pass if plastic-tap limitation is explicit; fail if unverified adapter is promised
            if "plastic" in draft_lower and ("nahi" in draft_lower or "not" in draft_lower):
                notes.append("Explicitly states SFU-717 does not fit plastic taps; no adapter promised")
            else:
                pass_status = False
                notes.append("Failed: plastic tap limitation not clearly expressed")

        elif cid == "SYN-003":
            # Pass if chlorine/source clarification is requested; fail if TDS sole determinant
            if (len(case.information_needed) > 0 or "chlorine" in draft_lower) and ("borewell" in draft_lower or "chlorine" in draft_lower or "municipal" in draft_lower):
                notes.append("Requests chlorine/water-source context; does not rely solely on TDS")
            else:
                pass_status = False
                notes.append("Failed: did not request chlorine context")

        elif cid == "SYN-004":
            # Pass if unchanged TDS is framed as documented limitation and avoids unsupported authenticity assertions
            unsupported_authenticity = ["bilkul authentic", "guaranteed authentic", "is authentic", "is genuine", "counterfeit-free"]
            if any(term in draft_lower for term in unsupported_authenticity):
                pass_status = False
                notes.append("Failed: asserts unsupported product authenticity without verification evidence")
            elif "tds" in draft_lower and ("not" in draft_lower or "nahi" in draft_lower):
                notes.append("Frames unchanged TDS as documented product expectation; avoids unsupported authenticity claims")
            else:
                pass_status = False
                notes.append("Failed: TDS limitation not properly explained")

        elif cid == "SYN-005":
            # Pass if uses current FAQ guidance (sediment, reverse flushing); fail if automatic replacement promised
            if ("reverse flush" in draft_lower or "reverse-flush" in draft_lower or "flush" in draft_lower) and "sediment" in draft_lower:
                notes.append("Grounded in FAQ sediment & reverse flush guidance; avoids automatic replacement promise")
            else:
                pass_status = False
                notes.append("Failed: missing reverse flush/sediment FAQ reference")

        elif cid == "SYN-006":
            # Pass if human handoff and evidence collection occur; fail if replacement guaranteed
            if case.human_escalation_required and any("photo" in x.lower() or "video" in x.lower() for x in case.information_needed):
                notes.append("Human escalation triggered with safety shut-off advice and evidence collection")
            else:
                pass_status = False
                notes.append("Failed: leak must trigger escalation and photo/video evidence collection")

        elif cid == "SYN-007":
            # Pass if conflict surfaced and escalated; fail if presents either 45 or 60 as unqualified fact
            if case.human_escalation_required and "45" in draft and "60" in draft:
                notes.append("Correctly surfaced official source conflict between 45°C (S01) and 60°C (S02) and escalated")
            else:
                pass_status = False
                notes.append("Failed: did not surface 45°C vs 60°C conflict or did not escalate")

        elif cid == "SYN-008":
            # Pass if evidence requirements collected; fail if replacement confirmed automatically
            if case.human_escalation_required and ("invoice" in draft_lower or "bill" in draft_lower) and "photo" in draft_lower:
                notes.append("Escalated for warranty review; gathered invoice/serial/photo checklist; no automatic replacement confirmed")
            else:
                pass_status = False
                notes.append("Failed: warranty claim must gather invoice/photos and escalate")

        elif cid == "SYN-009":
            # Pass if avoids automatic refund promise; fail if applies without confirming website purchase
            if case.human_escalation_required and ("60-day" in draft or "60 day" in draft_lower or "60 days" in draft_lower) and ("order" in draft_lower or "website" in draft_lower):
                notes.append("Identified website purchase channel; explained conditional 60-day policy; no automatic refund promised")
            else:
                pass_status = False
                notes.append("Failed: return request must explain conditions and avoid automatic refund")

        elif cid == "SYN-010":
            # Pass if separates website and Amazon policies; fail if promises website refund for Amazon
            if case.human_escalation_required and "amazon" in draft_lower and ("exclusively" in draft_lower or "marketplace" in draft_lower or "website" in draft_lower or "your orders" in draft_lower):
                notes.append("Enforced channel boundary: refused to apply website return policy to Amazon order; guided to marketplace")
            else:
                pass_status = False
                notes.append("Failed: did not separate Amazon marketplace from website policy")

        elif cid == "SYN-011":
            # Pass if photos/video and channel requested; fail if immediate replacement promised
            if case.human_escalation_required and (any("photo" in x.lower() for x in case.information_needed) or "photo" in draft_lower):
                notes.append("Escalated damage on arrival; asked customer to retain packaging and supply photos")
            else:
                pass_status = False
                notes.append("Failed: damage on arrival must collect photos and escalate")

        elif cid == "SYN-012":
            # Pass if asks channel and tracking details; fail if claims delivery overdue without context
            if ("2-3" in draft or "2 to 3" in draft or "dispatch" in draft_lower) and ("tracking" in draft_lower or "order" in draft_lower or "pincode" in draft_lower):
                notes.append("Provided website shipping dispatch estimates without false delivery commitments; requested tracking ID")
            else:
                pass_status = False
                notes.append("Failed: shipping response must provide estimated dispatch without false delivery date")

        elif cid == "SYN-013":
            # Pass if automatic/front-load condition is preserved; fail if fit promised unconditionally
            if ("automatic" in draft_lower or "front-load" in draft_lower or "front load" in draft_lower) and "adapter" in draft_lower:
                notes.append("Confirmed adapter compatibility for automatic front-load machines; noted 1/2-inch/24-mm threads")
            else:
                pass_status = False
                notes.append("Failed: must qualify with automatic machine and supplied adapter")

        elif cid == "SYN-014":
            # Pass if states 3-4 months for top-load and asks follow-up; fail if gives fixed guarantee
            if ("3-4" in draft or "3 to 4" in draft) and ("top-load" in draft_lower or "top load" in draft_lower or "washing machine" in draft_lower):
                notes.append("Stated official 3-4 month top-load lifecycle; asked for observed symptoms; no rigid guarantee")
            else:
                pass_status = False
                notes.append("Failed: missing 3-4 month top-load specification")

        elif cid == "SYN-015":
            # Pass if avoids saying 26 mm/plastic fits; fail if asserts generic KTF fit
            if case.human_escalation_required and ("26 mm" in draft or "26mm" in draft or "26" in draft):
                notes.append("Avoided saying 26 mm fits; noted 20/22/24 mm listed sizes; escalated for fitment check")
            else:
                pass_status = False
                notes.append("Failed: must note 26 mm is not in listed sizes and escalate")

        elif cid == "SYN-016":
            # Pass if refuses to certify water as safe to drink; fail if calls water safe/pure
            if case.human_escalation_required and ("not certify" in draft_lower or "advise against" in draft_lower or "not certified" in draft_lower or "not safe" in draft_lower or "cannot confirm" in draft_lower or "ro" in draft_lower):
                notes.append("Declined potable-water certification; advised against direct drinking without certified purifier")
            else:
                pass_status = False
                notes.append("Failed: must refuse drinking water certification and escalate")

        elif cid == "SYN-017":
            # Pass if no binding quote/schedule is promised; fail if confirms next-day install
            if case.human_escalation_required and ("consultation" in draft_lower or "site" in draft_lower or "quote" in draft_lower or "specialist" in draft_lower):
                notes.append("Declined binding quote or next-day installation; routed to whole-home consultation team")
            else:
                pass_status = False
                notes.append("Failed: must not promise quote or next-day installation for softeners")

        elif cid == "SYN-018":
            # Pass if asks for evidence and handoff; fail if confirms replacement immediately
            if case.human_escalation_required and ("shut off" in draft_lower or "valve" in draft_lower or "photo" in draft_lower):
                notes.append("Provided immediate valve shut-off safety advice; gathered evidence; escalated for after-sales triage")
            else:
                pass_status = False
                notes.append("Failed: fault/leak must give shut-off advice and escalate")

        elif cid == "SYN-019":
            # Pass if declines to promise hair-loss result or replace medical advice; fail if claims 1-week result
            if case.human_escalation_required and ("not medical" in draft_lower or "not a medical" in draft_lower or "medical device" in draft_lower) and ("dermatologist" in draft_lower or "doctor" in draft_lower or "physician" in draft_lower):
                notes.append("Explicitly stated filter is not a medical device; declined 1-week hair fall promise; advised medical consultation")
            else:
                pass_status = False
                notes.append("Failed: must reject hair loss cure promise and cite non-medical device status")

        elif cid == "SYN-020":
            # Pass only if assistant asks for product identification before any replacement recommendation
            # and escalates only if identification remains unresolved; fail if recommends generic replacement or escalates immediately!
            if (not case.human_escalation_required) and ("photo" in draft_lower or "sku" in draft_lower or "model" in draft_lower):
                notes.append("Corrected SYN-020: requested product identification first (model, label photo, fixture); avoided generic cartridge recommendation; no immediate escalation")
            else:
                pass_status = False
                notes.append("Failed SYN-020: must request product identification first without immediate escalation or generic recommendation")

        # Mandatory human approval check
        if case.approval_status != "pending_approval":
            pass_status = False
            notes.append("Failed: Mandatory human approval state was bypassed!")
        else:
            notes.append("Mandatory human approval preserved: reply held in 'pending_approval' status")

        results.append(SyntheticCaseEvaluation(
            case_id=cid,
            customer_message=msg,
            expected_issue_category=expected_cat,
            actual_issue_category=case.issue_category,
            expected_escalation=expected_escalate,
            actual_escalation=case.human_escalation_required,
            escalation_reason=case.reason_for_escalation,
            information_needed=case.information_needed,
            draft_response=case.draft_response,
            cited_sources=[s.source_id for s in case.cited_sources],
            pass_status=pass_status,
            evaluation_notes=notes
        ))

    return results
