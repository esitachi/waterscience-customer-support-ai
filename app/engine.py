import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.models import (
    CustomerQueryRequest,
    SupportCase,
    ReviewStatus,
    ApprovalStatus,
    ApprovalActionRequest
)
from app.knowledge import get_knowledge_base
from app.classifier import IssueClassifier
from app.policy_rules import PolicyRulesEngine
from app.response_generator import ResponseGenerator

class SupportEngine:
    def __init__(self):
        self.kb = get_knowledge_base()
        self.cases: Dict[str, SupportCase] = {}

    def process_query(self, query: CustomerQueryRequest) -> SupportCase:
        case_id = query.case_id or f"CASE-{uuid.uuid4().hex[:8].upper()}"
        created_at = datetime.now(timezone.utc).isoformat()

        # Step 1: Detect Channel
        channel = PolicyRulesEngine.detect_channel(query.message, query.purchase_channel)

        # Step 2: Classify issue, product, and source IDs
        issue_category, detected_product, source_ids = IssueClassifier.classify(
            query.message,
            product_hint=query.product_hint,
            explicit_channel=channel
        )

        # Step 3: Retrieve verified source records
        cited_sources = self.kb.get_sources(source_ids)

        # Step 4: Evaluate deterministic guardrails & policies
        (
            escalate,
            escalation_reason,
            needed_info,
            guardrails,
            review_status
        ) = PolicyRulesEngine.evaluate_rules(
            query.message,
            detected_product,
            issue_category,
            channel
        )

        # If escalation is required, review_status is ESCALATED_TO_HUMAN
        if escalate:
            review_status = ReviewStatus.ESCALATED_TO_HUMAN

        # Step 5: Generate grounded draft response
        draft = ResponseGenerator.generate_draft(
            customer_message=query.message,
            issue_category=issue_category,
            detected_product=detected_product,
            purchase_channel=channel,
            information_needed=needed_info,
            cited_sources=cited_sources,
            human_escalation_required=escalate,
            reason_for_escalation=escalation_reason
        )

        # Step 6: Formulate SupportCase with mandatory human approval pending
        case = SupportCase(
            case_id=case_id,
            created_at=created_at,
            customer_message=query.message,
            detected_product=detected_product,
            detected_variant=None,
            purchase_channel=channel,
            issue_category=issue_category,
            information_needed=needed_info,
            draft_response=draft,
            cited_sources=cited_sources,
            human_escalation_required=escalate,
            reason_for_escalation=escalation_reason,
            review_status=review_status,
            approval_status=ApprovalStatus.PENDING_APPROVAL,
            applied_guardrails=guardrails,
            reviewer_comment=None
        )

        self.cases[case_id] = case
        return case

    def get_case(self, case_id: str) -> Optional[SupportCase]:
        return self.cases.get(case_id)

    def list_cases(self) -> List[SupportCase]:
        return list(self.cases.values())

    def update_approval(self, case_id: str, action: ApprovalActionRequest) -> Optional[SupportCase]:
        case = self.cases.get(case_id)
        if not case:
            return None

        act = action.action.lower()
        if act == "approve":
            case.approval_status = ApprovalStatus.APPROVED
        elif act == "reject":
            case.approval_status = ApprovalStatus.REJECTED
        elif act == "edit":
            case.approval_status = ApprovalStatus.EDITED
            if action.edited_response:
                case.draft_response = action.edited_response

        if action.reviewer_comment:
            case.reviewer_comment = action.reviewer_comment

        self.cases[case_id] = case
        return case

_engine_instance = None

def get_support_engine() -> SupportEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = SupportEngine()
    return _engine_instance
