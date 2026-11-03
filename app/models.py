from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class PurchaseChannel(str, Enum):
    WATERSCIENCE_WEBSITE = "waterscience_website"
    AMAZON = "amazon"
    FLIPKART = "flipkart"
    QUICK_COMMERCE = "quick_commerce"
    RETAIL = "retail"
    UNKNOWN = "unknown"

class ReviewStatus(str, Enum):
    NEEDS_CLARIFICATION = "needs_clarification"
    ESCALATED_TO_HUMAN = "escalated_to_human"
    READY_FOR_APPROVAL = "ready_for_approval"

class ResolutionLevel(str, Enum):
    LEVEL_1_AUTOMATIC = "level_1_automatic"      # Safe, evidence-grounded queries resolved autonomously
    LEVEL_2_CONDITIONAL = "level_2_conditional"  # Clarification or conditional troubleshooting required
    LEVEL_3_ESCALATED = "level_3_escalated"      # Safety, warranty disputes, unverified facts, human escalation

class ApprovalStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"

class SourceReference(BaseModel):
    source_id: str
    title: str
    url: Optional[str] = None
    evidence_type: str = "official fact"

class CustomerQueryRequest(BaseModel):
    message: str = Field(..., description="Customer message in English or Hinglish")
    product_hint: Optional[str] = Field(None, description="Optional stated product, e.g. CLEO SFU-717")
    purchase_channel: Optional[str] = Field(None, description="Purchase channel: waterscience_website, amazon, etc.")
    order_id: Optional[str] = Field(None, description="Order ID if available")
    case_id: Optional[str] = Field(None, description="Optional case identifier, e.g. SYN-001")

class SupportCase(BaseModel):
    case_id: str
    created_at: str
    customer_message: str
    detected_product: Optional[str] = None
    detected_variant: Optional[str] = None
    purchase_channel: str = PurchaseChannel.UNKNOWN.value
    issue_category: str
    information_needed: List[str] = []
    draft_response: str
    cited_sources: List[SourceReference] = []
    human_escalation_required: bool = False
    reason_for_escalation: Optional[str] = None
    review_status: ReviewStatus = ReviewStatus.READY_FOR_APPROVAL
    approval_status: ApprovalStatus = ApprovalStatus.PENDING_APPROVAL
    resolution_level: ResolutionLevel = ResolutionLevel.LEVEL_1_AUTOMATIC
    auto_dispatched: bool = False
    applied_guardrails: List[str] = []
    reviewer_comment: Optional[str] = None
    execution_provider: str = "mock"
    provider_error: Optional[str] = None
    provider_error_category: Optional[str] = None

class ConversationMessage(BaseModel):
    role: str = Field(..., description="'customer', 'assistant', or 'system'")
    content: str
    timestamp: str

class TroubleshootingState(BaseModel):
    attempts_count: int = 0
    suggested_steps: List[str] = []
    customer_feedback: Optional[str] = None
    is_loop_detected: bool = False

class ConversationContext(BaseModel):
    conversation_id: str
    customer_id: Optional[str] = None
    channel: str = PurchaseChannel.WATERSCIENCE_WEBSITE.value
    messages: List[ConversationMessage] = []
    identified_product: Optional[str] = None
    troubleshooting: TroubleshootingState = Field(default_factory=TroubleshootingState)

class AutonomousResolutionResult(BaseModel):
    case_id: str
    conversation_id: Optional[str] = None
    resolution_level: ResolutionLevel
    status: str  # "auto_resolved", "awaiting_customer_reply", "escalated_to_human"
    auto_dispatched: bool
    response_text: str
    cited_sources: List[SourceReference] = []
    applied_guardrails: List[str] = []
    reason_for_escalation: Optional[str] = None
    information_needed: List[str] = []
    dispatch_timestamp: Optional[str] = None
    channel: str = PurchaseChannel.WATERSCIENCE_WEBSITE.value
    execution_provider: str = "mock"
    provider_error: Optional[str] = None

class ApprovalActionRequest(BaseModel):
    action: str = Field(..., description="approve, reject, or edit")
    edited_response: Optional[str] = None
    reviewer_comment: Optional[str] = None

class SyntheticCaseEvaluation(BaseModel):
    case_id: str
    customer_message: str
    expected_issue_category: str
    actual_issue_category: str
    expected_escalation: bool
    actual_escalation: bool
    escalation_reason: Optional[str]
    information_needed: List[str]
    draft_response: str
    cited_sources: List[str]
    pass_status: bool
    evaluation_notes: List[str]

class IngestMessageRequest(BaseModel):
    channel: str = Field(..., description="Purchase / ingestion channel, e.g. waterscience_website, amazon, whatsapp")
    customer_id: str = Field(..., description="Customer identifier")
    conversation_id: str = Field(..., description="Conversation / session identifier")
    message_id: str = Field(..., description="Unique message ID for deduplication / idempotency")
    message: str = Field(..., description="Customer inquiry or message text")
    timestamp: Optional[str] = Field(None, description="ISO timestamp of message arrival")

class IngestMessageResponse(BaseModel):
    status: str = Field(..., description="'accepted' or 'duplicate_ignored'")
    message_id: str
    conversation_id: str
    job_id: Optional[str] = None
    received_at: str

class ProcessingJobStatus(BaseModel):
    job_id: str
    message_id: str
    conversation_id: str
    status: str = Field(..., description="'queued', 'processing', 'completed', 'failed', 'dead_letter'")
    attempts: int = 0
    resolution_level: Optional[str] = None
    response_text: Optional[str] = None
    auto_dispatched: Optional[bool] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None

class TicketSummary(BaseModel):
    ticket_id: str
    conversation_id: str
    customer_id: str
    status: str = "open"  # "open", "assigned", "resolved", "closed"
    priority: str = "normal"  # "urgent", "high", "normal"
    category: str
    product: Optional[str] = None
    escalation_reason: Optional[str] = None
    assigned_to: Optional[str] = None
    customer_message: Optional[str] = None
    recommended_action: Optional[str] = None
    created_at: str
    resolved_at: Optional[str] = None
