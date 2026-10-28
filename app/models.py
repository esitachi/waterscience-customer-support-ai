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
    applied_guardrails: List[str] = []
    reviewer_comment: Optional[str] = None
    execution_provider: str = "mock"
    provider_error: Optional[str] = None
    provider_error_category: Optional[str] = None

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
