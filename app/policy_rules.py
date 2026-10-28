import re
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
            c = explicit_channel.lower()
            if c in [PurchaseChannel.AMAZON.value, PurchaseChannel.FLIPKART.value, PurchaseChannel.QUICK_COMMERCE.value, PurchaseChannel.RETAIL.value, PurchaseChannel.WATERSCIENCE_WEBSITE.value]:
                return c
            if "amazon" in c:
                return PurchaseChannel.AMAZON.value
            if "flipkart" in c:
                return PurchaseChannel.FLIPKART.value
            if "retail" in c or "shop" in c:
                return PurchaseChannel.RETAIL.value
            if "website" in c:
                return PurchaseChannel.WATERSCIENCE_WEBSITE.value

        t = text.lower()
        if "amazon" in t:
            return PurchaseChannel.AMAZON.value
        if "flipkart" in t:
            return PurchaseChannel.FLIPKART.value
        if any(w in t for w in ["retail", "sanitary shop", "offline shop", "hardware shop", "local shop"]):
            return PurchaseChannel.RETAIL.value
        if any(w in t for w in ["zepto", "blinkit", "instamart"]):
            return PurchaseChannel.QUICK_COMMERCE.value
        if any(w in t for w in ["waterscience.in", "official website", "your site", "your website"]):
            return PurchaseChannel.WATERSCIENCE_WEBSITE.value
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

        # Guardrail 1: Temperature limit conflict for CLEO SFU-717 / shower filters
        if issue_category == "temperature_limit_conflict" or (
            any(w in t for w in ["hot water", "degree", "celsius", "temperature", "geyser", "solar water", "garam paani", "75", "55", "50"]) and (
                detected_product in ["CLEO_SFU_717", "CLEO SFU-717", "CLEO replacement cartridge"] or "sfu" in t or "cleo" in t or "shower" in t
            )
        ):
            applied_guardrails.append("Conflict Rule: SFU-717 hot water maximum conflict (S01: 45°C vs S02: 60°C)")
            escalate = True
            escalation_reason = "Official-source conflict: SFU-717 product page specifies 45°C max whereas replacement cartridge FAQ states up to 60°C."
            information_needed.append("Exact unit/variant and current manual if available")
            return escalate, escalation_reason, information_needed, applied_guardrails, ReviewStatus.ESCALATED_TO_HUMAN

        # Guardrail 2: Medical / Health claims
        if issue_category == "medical_expectation" or any(w in t for w in ["hair fall", "hairfall", "hair loss", "doctor", "dandruff", "medical", "alopecia", "minoxidil"]) or re.search(r'\b(skin|cure)\b', t):
            applied_guardrails.append("Medical Claim Guardrail: Filter is not a medical device; avoid medical outcome promises")
            escalate = True
            escalation_reason = "Medical-outcome request and potential care avoidance."
            information_needed.append("Confirm customer is consulting a qualified medical specialist/dermatologist.")
            return escalate, escalation_reason, information_needed, applied_guardrails, ReviewStatus.ESCALATED_TO_HUMAN

        # Guardrail 3: Potable water safety (Direct drinking / Infant food)
        if issue_category == "potable_water_safety" or any(w in t for w in ["direct peena", "peena", "peene", "safe to drink", "drink", "drinking", "potable", "baby milk", "infant"]):
            applied_guardrails.append("Potable Water Guardrail: No verified potable-water certification collected")
            escalate = True
            escalation_reason = "No verified potable-water certification or use claim was collected for this product/variant."
            information_needed.extend(["Exact model", "intended use", "local water-quality context"])
            return escalate, escalation_reason, information_needed, applied_guardrails, ReviewStatus.ESCALATED_TO_HUMAN

        # Guardrail 4: Leakage / Physical Damage / Product Fault / Electrical Hazard / Warranty Claim / Social Engineering
        if issue_category in ["leak_after_maintenance", "product_fault", "damaged_on_arrival", "warranty_claim"] or any(
            w in t for w in ["leak", "leaking", "spraying", "drip", "seeping", "burst", "paani leak", "broken", "cracked", "crack", "damage", "damaged", "trigger work nahi", "electrical socket", "replacement unit", "send a replacement"]
        ):
            applied_guardrails.append("Safety & Damage Guardrail: Collect evidence (photo/video), instruct shut-off if needed, escalate to human")
            escalate = True
            if "electrical" in t or "socket" in t or "spraying" in t:
                escalation_reason = "Urgent water leak near electrical connection or appliance; safety shut-off required."
                information_needed.extend(["Instruct immediate power and water shut-off", "Photos/video of connection point"])
            elif "leak" in t and ("cartridge" in t or "joint" in t or "thread" in t):
                escalation_reason = "Leak and repair instruction require product-specific confirmation; detailed troubleshooting source is legacy/unverified for current applicability."
                information_needed.extend(["Photo/video", "model", "invoice/purchase date", "whether water can be safely shut off"])
            elif "crack" in t or "cracked" in t or "warranty" in t or "replacement" in t:
                escalation_reason = "Warranty coverage, defect cause, and replacement requests must be verified with proof of purchase and defect documentation."
                information_needed.extend(["Invoice or registration", "order number", "serial number", "photos/video of defective unit", "purchase channel"])
            elif "parcel" in t or "damaged" in t or "box" in t:
                escalation_reason = "Damage and replacement require evidence and channel-specific decisioning."
                information_needed.extend(["Product/model", "purchase channel", "order number", "delivery date", "photos/video of item and packaging"])
            else:
                escalation_reason = "Reported leak/fault requires physical assessment and evidence; warranty outcome is not automatic."
                information_needed.extend(["Photo/video", "invoice/order", "purchase channel", "whether water can safely be shut off"])
            return escalate, escalation_reason, information_needed, applied_guardrails, ReviewStatus.ESCALATED_TO_HUMAN

        # Guardrail 5: Whole-home water softeners & Industrial consultation (RENO Cygnus)
        if issue_category == "whole_home_consultation" or detected_product in ["RENO Cygnus", "RENO_CYGNUS"] or any(w in t for w in ["reno", "cygnus", "whole home", "softener", "textile", "plant", "effluent"]):
            applied_guardrails.append("Consultation Guardrail: Whole-home softener sizing, serviceability, and pricing require consultation")
            escalate = True
            escalation_reason = "Whole-home system sizing, serviceability, installation and pricing are consultation-dependent."
            information_needed.extend(["City/location", "home plumbing configuration", "chosen size/model", "site readiness", "quote confirmation"])
            return escalate, escalation_reason, information_needed, applied_guardrails, ReviewStatus.ESCALATED_TO_HUMAN

        # Guardrail 6: Return & Refund Requests
        if issue_category in ["marketplace_return_request", "website_return_request"] or any(w in t for w in ["refund", "return", "wapas", "refund chahiye", "replace it now", "money back"]):
            is_external = (
                channel in [PurchaseChannel.AMAZON.value, PurchaseChannel.FLIPKART.value, PurchaseChannel.QUICK_COMMERCE.value, PurchaseChannel.RETAIL.value]
                or any(w in t for w in ["amazon", "flipkart", "blinkit", "zepto", "retail", "shop", "sanitary shop", "offline"])
            )
            if is_external:
                applied_guardrails.append("Marketplace Policy Isolation: Never apply website return policy to Amazon, Flipkart, or Retail")
                escalate = True
                escalation_reason = "Marketplace/Retail policy and seller/fulfilment details were not verified in this research."
                information_needed.extend(["Marketplace/Store invoice or Order ID", "delivery date", "photos/video", "marketplace return status"])
                return escalate, escalation_reason, information_needed, applied_guardrails, ReviewStatus.ESCALATED_TO_HUMAN
            else:
                applied_guardrails.append("Return Policy Guardrail: Return eligibility and refund outcome are conditional and require human approval")
                escalate = True
                escalation_reason = "Return eligibility and outcome must be determined by the company; policy is conditional."
                information_needed.extend(["Order number", "delivery date", "condition/packaging", "why it is unsuitable", "tap details"])
                return escalate, escalation_reason, information_needed, applied_guardrails, ReviewStatus.ESCALATED_TO_HUMAN

        # Guardrail 7: Kitchen Filter Incompatible Tap / Variant Confusion (KTF Mini vs Wide)
        if ("ktf" in t or "kitchen tap" in t or detected_product in ["KTF_WIDE_CERAMIC", "KTF variant unknown"]) and (
            any(w in t for w in ["26 mm", "26mm", "plastic", "mini", "wide ceramic"])
        ):
            applied_guardrails.append("Fitment Scope Guardrail: 26 mm / plastic tap or cross-variant compatibility is outside KTF Wide cited sizes")
            escalate = True
            escalation_reason = "Fitment is outside the cited variant's listed sizes or involves cross-variant cartridge confusion."
            information_needed.extend(["Exact KTF variant", "photo of aerator/tap", "whether an aerator is present"])
            return escalate, escalation_reason, information_needed, applied_guardrails, ReviewStatus.ESCALATED_TO_HUMAN

        # Guardrail 8: Unknown Product Identification (SYN-020 rule)
        if (detected_product is None or "unknown" in str(detected_product).lower()) and (
            issue_category == "product_identification" or any(w in t for w in ["replacement", "cartridge", "photo bhej diya", "model yaad nahi", "filter at home"])
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

        # Guardrail 9: Low Flow Troubleshooting vs Persistent Blockage
        if issue_category == "low_flow":
            if any(w in t for w in ["already did", "already tried", "done reverse flush", "still weak", "still very slow", "still low"]):
                # If reverse flush was already attempted and failed, escalate to technical support
                applied_guardrails.append("Low Flow Technical Escalation: Persistent blockage after reverse flush requires technical inspection")
                escalate = True
                escalation_reason = "Persistent low flow after reverse flush indicates heavy internal sediment fouling or cartridge exhaustion."
                information_needed.extend(["Water source sediment levels", "cartridge age/installation date", "photo of cartridge inlet mesh"])
                return escalate, escalation_reason, information_needed, applied_guardrails, ReviewStatus.ESCALATED_TO_HUMAN
            else:
                information_needed.extend(["Cartridge age", "whether the drop is gradual", "water/sediment condition", "whether a leak is also present"])
                applied_guardrails.append("Low Flow Guardrail: Sediment clogging can cause flow drop; refer to reverse flushing FAQ; do not use unverified legacy repair steps")

        # Standard non-escalated cases requiring specific information:
        elif issue_category == "cartridge_selection" or ("borewell" in t and "metro" in t):
            information_needed.extend(["Whether chlorine is present/expected", "exact CLEO model"])
            applied_guardrails.append("Cartridge Selection Guardrail: Require chlorine/water-source context; do not rely solely on TDS")
            review_status = ReviewStatus.NEEDS_CLARIFICATION

        elif issue_category == "compatibility":
            information_needed.append("Confirm the tap is metal-threaded (22, 24, or 28 mm), not plastic.")
            applied_guardrails.append("Compatibility Guardrail: Metal-thread tap verified for 22, 24, 28 mm; plastic taps unsupported")

        elif issue_category == "delivery_tracking":
            information_needed.extend(["Purchase channel", "order date", "pincode", "tracking ID/dispatch notification"])
            applied_guardrails.append("Shipping Guardrail: Website shipping estimates (2-3 day dispatch, 3-6 day delivery) do not guarantee delivery dates")

        elif issue_category == "washing_machine_compatibility":
            information_needed.extend(["Confirm it is an automatic machine", "tap/thread setup if installation fit is uncertain"])
            applied_guardrails.append("IRIS Fitment Guardrail: Supplied adapter supports automatic machines; requires 1/2-inch BSP or 24-mm external thread")

        elif issue_category == "cartridge_life":
            information_needed.extend(["Observed problem", "water quality/sediment context", "whether flow/performance changed"])
            applied_guardrails.append("Consumable Lifecycle Guardrail: Top-load 3-4 months, front-load 4-6 months; depends on water quality and usage")

        return escalate, escalation_reason, information_needed, applied_guardrails, review_status
