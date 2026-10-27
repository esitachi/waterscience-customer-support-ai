from typing import List, Dict, Any, Optional, Tuple
from app.models import PurchaseChannel, ReviewStatus

class PolicyRulesEngine:
    """
    Deterministic rule engine implementing WaterScience safety, channel,
    and evidence guardrails.
    """

    @staticmethod
    def detect_channel(text: str, explicit_channel: Optional[str] = None) -> str:
        if explicit_channel:
            return explicit_channel.lower()
        t = text.lower()
        if "amazon" in t:
            return PurchaseChannel.AMAZON.value
        if "flipkart" in t:
            return PurchaseChannel.FLIPKART.value
        if "website" in t or "waterscience.in" in t or "store" in t:
            return PurchaseChannel.WATERSCIENCE_WEBSITE.value
        if "zepto" in t or "blinkit" in t or "instamart" in t:
            return PurchaseChannel.QUICK_COMMERCE.value
        return PurchaseChannel.UNKNOWN.value

    @staticmethod
    def evaluate_rules(
        text: str,
        detected_product: Optional[str],
        issue_category: str,
        channel: str
    ) -> Tuple[bool, Optional[str], List[str], List[str], ReviewStatus]:
        """
        Returns:
            human_escalation_required: bool
            reason_for_escalation: Optional[str]
            information_needed: List[str]
            applied_guardrails: List[str]
            review_status: ReviewStatus
        """
        t = text.lower()
        applied_guardrails = []
        information_needed = []
        escalate = False
        escalation_reason = None
        review_status = ReviewStatus.READY_FOR_APPROVAL

        # Guardrail 1: Temperature limit conflict for CLEO SFU-717
        if ("hot water" in t or "degree" in t or "55" in t or "temperature" in t or "garam paani" in t) and (
            detected_product in ["CLEO_SFU_717", "CLEO SFU-717", "CLEO replacement cartridge"] or "sfu" in t or "cleo" in t
        ):
            applied_guardrails.append("Conflict Rule: SFU-717 hot water maximum conflict (S01: 45°C vs S02: 60°C)")
            escalate = True
            escalation_reason = "Official-source conflict: SFU-717 product page specifies 45°C max whereas replacement cartridge FAQ states up to 60°C."
            information_needed.append("Exact unit/variant and current manual if available")
            return escalate, escalation_reason, information_needed, applied_guardrails, ReviewStatus.ESCALATED_TO_HUMAN

        # Guardrail 2: Medical / Health claims
        if any(w in t for w in ["hair fall", "hairfall", "hair loss", "doctor", "skin", "dandruff", "medical", "cure"]):
            applied_guardrails.append("Medical Claim Guardrail: Filter is not a medical device; avoid medical outcome promises")
            escalate = True
            escalation_reason = "Medical-outcome request and potential care avoidance."
            return escalate, escalation_reason, information_needed, applied_guardrails, ReviewStatus.ESCALATED_TO_HUMAN

        # Guardrail 3: Potable water safety
        if any(w in t for w in ["drink", "peena", "peene", "potable", "safe to drink", "purity"]):
            applied_guardrails.append("Potable Water Guardrail: No verified potable-water certification collected")
            escalate = True
            escalation_reason = "No verified potable-water certification or use claim was collected for this product/variant."
            information_needed.extend(["Exact model", "intended use", "local water-quality context"])
            return escalate, escalation_reason, information_needed, applied_guardrails, ReviewStatus.ESCALATED_TO_HUMAN

        # Guardrail 4: Leakage / Physical Damage / Product Fault
        if any(w in t for w in ["leak", "leaking", "paani leak", "broken", "cracked", "crack", "damage", "damaged", "trigger work nahi"]):
            applied_guardrails.append("Safety & Damage Guardrail: Collect evidence (photo/video), instruct shut-off if needed, escalate to human")
            escalate = True
            if "leak" in t and "cartridge" in t:
                escalation_reason = "Leak and repair instruction require product-specific confirmation; detailed troubleshooting source is legacy/unverified for current applicability."
                information_needed.extend(["Photo/video", "model", "invoice/purchase date", "whether water can be safely shut off"])
            elif "crack" in t or "body cracked" in t:
                escalation_reason = "Warranty coverage and cause of damage must be determined by the support team."
                information_needed.extend(["Invoice or registration", "serial number", "photos/video", "purchase channel", "description of damage"])
            elif "parcel" in t or "damaged" in t:
                escalation_reason = "Damage and replacement require evidence and channel-specific decisioning."
                information_needed.extend(["Product/model", "purchase channel", "order number", "delivery date", "photos/video of item and packaging"])
            else:
                escalation_reason = "Reported leak/fault requires physical assessment and evidence; warranty outcome is not automatic."
                information_needed.extend(["Photo/video", "invoice/order", "purchase channel", "whether water can safely be shut off"])
            return escalate, escalation_reason, information_needed, applied_guardrails, ReviewStatus.ESCALATED_TO_HUMAN

        # Guardrail 5: Whole-home water softeners (RENO Cygnus)
        if detected_product == "RENO_CYGNUS" or "reno" in t or "cygnus" in t or "softener" in t:
            applied_guardrails.append("Consultation Guardrail: Whole-home softener sizing, serviceability, and pricing require consultation")
            escalate = True
            escalation_reason = "Whole-home system sizing, serviceability, installation and pricing are consultation-dependent."
            information_needed.extend(["City/location", "home plumbing configuration", "chosen size/model", "site readiness", "quote confirmation"])
            return escalate, escalation_reason, information_needed, applied_guardrails, ReviewStatus.ESCALATED_TO_HUMAN

        # Guardrail 6: Return & Refund Requests
        if any(w in t for w in ["refund", "return", "wapas", "refund chahiye", "replace it now"]):
            if channel == PurchaseChannel.AMAZON.value or "amazon" in t:
                applied_guardrails.append("Marketplace Policy Isolation: Never apply website return policy to Amazon")
                escalate = True
                escalation_reason = "Marketplace policy and seller/fulfilment details were not verified in this research."
                information_needed.extend(["Amazon order ID", "delivery date", "photos/video", "Amazon order/return status"])
                return escalate, escalation_reason, information_needed, applied_guardrails, ReviewStatus.ESCALATED_TO_HUMAN
            else:
                applied_guardrails.append("Return Policy Guardrail: Return eligibility and refund outcome are conditional and require human approval")
                escalate = True
                escalation_reason = "Return eligibility and outcome must be determined by the company; policy is conditional."
                information_needed.extend(["Order number", "delivery date", "condition/packaging", "why it is unsuitable", "tap details"])
                return escalate, escalation_reason, information_needed, applied_guardrails, ReviewStatus.ESCALATED_TO_HUMAN

        # Guardrail 7: Kitchen Filter Incompatible Tap (e.g. 26 mm plastic tap)
        if ("ktf" in t or detected_product == "KTF_WIDE_CERAMIC") and ("26 mm" in t or "26mm" in t or "plastic" in t):
            applied_guardrails.append("Fitment Scope Guardrail: 26 mm / plastic tap is outside KTF Wide cited sizes (20/22/24 mm)")
            escalate = True
            escalation_reason = "Fitment is outside the cited variant's listed sizes and the exact variant is unknown."
            information_needed.extend(["Exact KTF variant", "photo of aerator/tap", "whether an aerator is present"])
            return escalate, escalation_reason, information_needed, applied_guardrails, ReviewStatus.ESCALATED_TO_HUMAN

        # Guardrail 8: Unknown Product Identification (SYN-020 rule)
        # "Correct SYN-020 so that the system requests product identification first and escalates only if the product cannot subsequently be identified."
        if (detected_product is None or "unknown" in str(detected_product).lower()) and (
            "replacement" in t or "cartridge" in t or "photo bhej diya" in t or "model yaad nahi" in t
        ):
            applied_guardrails.append("Identification Guardrail: Request product identification details before any replacement recommendation; do not escalate immediately")
            escalate = False
            escalation_reason = None
            information_needed.extend([
                "Model/SKU on product body, invoice, or order history",
                "Purchase channel",
                "Clear photo of label and connectors",
                "What fixture or appliance it serves"
            ])
            review_status = ReviewStatus.NEEDS_CLARIFICATION
            return escalate, escalation_reason, information_needed, applied_guardrails, review_status

        # Standard non-escalated cases requiring specific information:
        if issue_category == "cartridge_selection" or ("borewell" in t and "metro" in t):
            information_needed.extend(["Whether chlorine is present/expected", "exact CLEO model"])
            applied_guardrails.append("Cartridge Selection Guardrail: Require chlorine/water-source context; do not rely solely on TDS")
            review_status = ReviewStatus.NEEDS_CLARIFICATION

        elif issue_category == "compatibility" and "metal" in t and "24 mm" in t:
            information_needed.append("Confirm the tap is metal-threaded, not plastic.")
            applied_guardrails.append("Compatibility Guardrail: Metal-thread tap verified for 22, 24, 28 mm; plastic taps unsupported")

        elif issue_category == "delivery_tracking" or ("stuck" in t and "order" in t):
            information_needed.extend(["Purchase channel", "order date", "pincode", "tracking ID/dispatch notification"])
            applied_guardrails.append("Shipping Guardrail: Website shipping estimates (2-3 day dispatch, 3-6 day delivery) do not guarantee delivery dates")

        elif issue_category == "washing_machine_compatibility":
            information_needed.extend(["Confirm it is an automatic front-load machine", "tap/thread setup if installation fit is uncertain"])
            applied_guardrails.append("IRIS Fitment Guardrail: Supplied adapter supports automatic machines; requires 1/2-inch BSP or 24-mm external thread")

        elif issue_category == "cartridge_life":
            information_needed.extend(["Observed problem", "water quality/sediment context", "whether flow/performance changed"])
            applied_guardrails.append("Consumable Lifecycle Guardrail: Top-load 3-4 months, front-load 4-6 months; depends on water quality and usage")

        elif issue_category == "low_flow":
            information_needed.extend(["Cartridge age", "whether the drop is gradual", "water/sediment condition", "whether a leak is also present"])
            applied_guardrails.append("Low Flow Guardrail: Sediment clogging can cause flow drop; refer to reverse flushing FAQ; do not use unverified legacy repair steps")

        return escalate, escalation_reason, information_needed, applied_guardrails, review_status
