import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.models import (
    CustomerQueryRequest,
    SupportCase,
    ReviewStatus,
    ApprovalStatus,
    ApprovalActionRequest,
    ResolutionLevel,
    PurchaseChannel,
    ConversationContext,
    ConversationMessage,
    TroubleshootingState,
    AutonomousResolutionResult
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
        meta: Dict[str, Any] = {}
        draft = ResponseGenerator.generate_draft(
            customer_message=query.message,
            issue_category=issue_category,
            detected_product=detected_product,
            purchase_channel=channel,
            information_needed=needed_info,
            cited_sources=cited_sources,
            human_escalation_required=escalate,
            reason_for_escalation=escalation_reason,
            execution_metadata=meta
        )

        # Determine 3-tier resolution level
        res_level, _ = PolicyRulesEngine.determine_resolution_tier(
            escalate=escalate,
            review_status=review_status,
            information_needed=needed_info
        )

        # Step 6: Formulate SupportCase with mandatory human approval pending (Live Console mode)
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
            resolution_level=res_level,
            auto_dispatched=False,
            applied_guardrails=guardrails,
            reviewer_comment=None,
            execution_provider=meta.get("execution_provider", "mock"),
            provider_error=meta.get("provider_error"),
            provider_error_category=meta.get("provider_error_category")
        )

        self.cases[case_id] = case
        return case

    def process_autonomous_interaction(
        self,
        message: str,
        conversation_context: Optional[ConversationContext] = None,
        channel: Optional[str] = None,
        customer_id: Optional[str] = None,
        message_id: Optional[str] = None,
        product_hint: Optional[str] = None,
        fast_mode: bool = False
    ) -> AutonomousResolutionResult:
        """
        Autonomous 3-Tier Resolution Processing:
        - Level 1 (Automatic Resolution): Safe, verified queries resolved and dispatched without human sign-off.
        - Level 2 (Conditional Troubleshooting): Follow-up clarifications asked interactively with loop prevention.
        - Level 3 (Mandatory Human Escalation): Safety risks, policy disputes, and repeat failures routed to human agents.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        case_id = f"AUTO-{uuid.uuid4().hex[:8].upper()}"

        # 1. Manage Conversation Context
        if conversation_context is None:
            conversation_context = ConversationContext(
                conversation_id=f"CONV-{uuid.uuid4().hex[:8].upper()}",
                customer_id=customer_id or "anonymous_customer",
                channel=channel or PurchaseChannel.WATERSCIENCE_WEBSITE.value
            )

        detected_channel = PolicyRulesEngine.detect_channel(
            message,
            explicit_channel=channel or conversation_context.channel
        )
        conversation_context.channel = detected_channel

        # Append incoming message to conversation history
        conversation_context.messages.append(
            ConversationMessage(role="customer", content=message, timestamp=now_iso)
        )

        # 2. Check for circular troubleshooting / unresolved signals
        lower_msg = message.lower()
        loop_signals = [
            "still not working", "tried that already", "did not work",
            "no change", "problem persists", "still leaking",
            "still slow", "bhai nahi hua", "same problem"
        ]
        if any(sig in lower_msg for sig in loop_signals):
            conversation_context.troubleshooting.attempts_count += 1

        # 3. Classify issue & product (inheriting previous product if established in context)
        effective_product_hint = product_hint or conversation_context.identified_product
        issue_category, detected_product, source_ids = IssueClassifier.classify(
            message,
            product_hint=effective_product_hint,
            explicit_channel=detected_channel
        )
        if detected_product:
            conversation_context.identified_product = detected_product

        # 4. Retrieve verified source records
        cited_sources = self.kb.get_sources(source_ids)

        # 5. Evaluate deterministic guardrails & policies
        (
            escalate,
            escalation_reason,
            needed_info,
            guardrails,
            review_status
        ) = PolicyRulesEngine.evaluate_rules(
            message,
            detected_product,
            issue_category,
            detected_channel
        )

        # 6. Determine 3-Tier Resolution Level (with loop prevention)
        resolution_level, loop_reason = PolicyRulesEngine.determine_resolution_tier(
            escalate=escalate,
            review_status=review_status,
            information_needed=needed_info,
            troubleshooting_state=conversation_context.troubleshooting
        )

        if loop_reason:
            escalate = True
            escalation_reason = loop_reason
            resolution_level = ResolutionLevel.LEVEL_3_ESCALATED
            review_status = ReviewStatus.ESCALATED_TO_HUMAN
            guardrails.append("Circular Troubleshooting Protection: Escalated after repeated failed resolution attempts")

        # 7. Generate grounded draft response
        meta: Dict[str, Any] = {}
        draft = ResponseGenerator.generate_draft(
            customer_message=message,
            issue_category=issue_category,
            detected_product=detected_product,
            purchase_channel=detected_channel,
            information_needed=needed_info,
            cited_sources=cited_sources,
            human_escalation_required=escalate,
            reason_for_escalation=escalation_reason,
            execution_metadata=meta,
            fast_mode=fast_mode
        )

        # Append assistant response to context
        conversation_context.messages.append(
            ConversationMessage(role="assistant", content=draft, timestamp=now_iso)
        )

        # 8. Resolution Actions per Level:
        # Level 1: Auto-resolved and auto-dispatched through channel adapter
        # Level 2: Conditional clarification auto-dispatched to customer
        # Level 3: Mandatory human escalation, NOT auto-dispatched (queued in inbox)
        if resolution_level == ResolutionLevel.LEVEL_1_AUTOMATIC:
            status_str = "auto_resolved"
            auto_dispatched = True
        elif resolution_level == ResolutionLevel.LEVEL_2_CONDITIONAL:
            status_str = "awaiting_customer_reply"
            auto_dispatched = True
            conversation_context.troubleshooting.attempts_count += 1
            if needed_info:
                conversation_context.troubleshooting.suggested_steps.extend(needed_info)
        else:
            status_str = "escalated_to_human"
            auto_dispatched = False

        result = AutonomousResolutionResult(
            case_id=case_id,
            conversation_id=conversation_context.conversation_id,
            resolution_level=resolution_level,
            status=status_str,
            auto_dispatched=auto_dispatched,
            response_text=draft,
            cited_sources=cited_sources,
            applied_guardrails=guardrails,
            reason_for_escalation=escalation_reason,
            information_needed=needed_info,
            dispatch_timestamp=now_iso if auto_dispatched else None,
            channel=detected_channel,
            execution_provider=meta.get("execution_provider", "mock"),
            provider_error=meta.get("provider_error")
        )

        # Also store in self.cases so legacy API endpoints and Live Console can query it
        case = SupportCase(
            case_id=case_id,
            created_at=now_iso,
            customer_message=message,
            detected_product=detected_product,
            detected_variant=None,
            purchase_channel=detected_channel,
            issue_category=issue_category,
            information_needed=needed_info,
            draft_response=draft,
            cited_sources=cited_sources,
            human_escalation_required=escalate,
            reason_for_escalation=escalation_reason,
            review_status=review_status,
            approval_status=ApprovalStatus.APPROVED if auto_dispatched else ApprovalStatus.PENDING_APPROVAL,
            resolution_level=resolution_level,
            auto_dispatched=auto_dispatched,
            applied_guardrails=guardrails,
            reviewer_comment="Auto-resolved and dispatched via Level 1 pipeline" if resolution_level == ResolutionLevel.LEVEL_1_AUTOMATIC else None,
            execution_provider=meta.get("execution_provider", "mock"),
            provider_error=meta.get("provider_error"),
            provider_error_category=meta.get("provider_error_category")
        )
        self.cases[case_id] = case

        return result

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
