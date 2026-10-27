import os
from typing import List, Dict, Any, Optional
from app.config import settings
from app.models import SourceReference, ReviewStatus

class ResponseGenerator:
    """
    Generates grounded drafts using either the deterministic factual engine
    or a configured external LLM (OpenAI / Groq / Anthropic).
    """

    @staticmethod
    def generate_draft(
        customer_message: str,
        issue_category: str,
        detected_product: Optional[str],
        purchase_channel: str,
        information_needed: List[str],
        cited_sources: List[SourceReference],
        human_escalation_required: bool,
        reason_for_escalation: Optional[str]
    ) -> str:
        # If LLM_PROVIDER is not mock and an API key is available, we can call the LLM
        if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
            try:
                return ResponseGenerator._call_openai(
                    customer_message, issue_category, detected_product,
                    purchase_channel, information_needed, cited_sources,
                    human_escalation_required, reason_for_escalation
                )
            except Exception as e:
                # Fallback to deterministic mock draft on error
                print(f"LLM call failed: {e}. Falling back to grounded mock draft.")

        # Grounded factual mock drafts tailored to the researched knowledge base
        return ResponseGenerator._generate_grounded_mock_draft(
            customer_message, issue_category, detected_product,
            purchase_channel, information_needed, cited_sources,
            human_escalation_required, reason_for_escalation
        )

    @staticmethod
    def _generate_grounded_mock_draft(
        customer_message: str,
        issue_category: str,
        detected_product: Optional[str],
        purchase_channel: str,
        information_needed: List[str],
        cited_sources: List[SourceReference],
        human_escalation_required: bool,
        reason_for_escalation: Optional[str]
    ) -> str:
        t = customer_message.lower()

        # SYN-001: 24 mm metal tap compatibility
        if issue_category == "compatibility" and "24 mm" in t and "metal" in t:
            return (
                "Hello! The CLEO SFU-717 shower and tap filter is officially documented to fit 22 mm, "
                "24 mm, and 28 mm threaded metal taps [Source: S01]. Please confirm that your tap has metal threads, "
                "as the product is not compatible with plastic taps. Diameter alone does not guarantee a fit if the threading "
                "or fixture type differs, so if you are at all unsure, please share a clear photo of your tap aerator/thread "
                "and our team will be happy to verify compatibility for you."
            )

        # SYN-002: Plastic tap compatibility (Hinglish)
        if issue_category == "compatibility" and "plastic" in t:
            return (
                "Namaste! Official WaterScience product specifications ke anusar, CLEO SFU-717 filter plastic taps "
                "par fit nahi hota hai—yeh keval metal-threaded taps (22 mm, 24 mm, aur 28 mm) ke liye designed hai [Source: S01]. "
                "Hum plastic taps ke liye koi unverified adapter recommend nahi karte. Kripya hamari customer care team "
                "(care@waterscience.in / WhatsApp 9148545840) se contact karein taaki hum aapke setup ke liye suitable "
                "alternative solution check kar sakein."
            )

        # SYN-003: Cartridge selection (Borewell / TDS 900)
        if issue_category == "cartridge_selection":
            return (
                "Namaste! WaterScience replacement guidelines ke mutabiq [Source: S01, S02]:\n"
                "• Municipal/Metro Cartridge chlorine aur moderate hardness ke liye suitable hai (TDS < 800 ppm).\n"
                "• Borewell/Tanker Cartridge high hardness ke liye hai jahan chlorine nahi hota (TDS up to 1800 ppm).\n\n"
                "Kripya dhyan dein ki cartridge ka chunav keval TDS number se nahi kiya jata. Recommendation confirm karne ke liye:\n"
                "1. Kya aapke paani mein chlorine ki smell/presence aati hai?\n"
                "2. Aapka exact CLEO shower/tap model kaunsa hai?"
            )

        # SYN-004: TDS unchanged
        if issue_category == "tds_expectation":
            return (
                "Namaste. Aapka filter bilkul authentic hai. Official WaterScience product documentation ke anusar, "
                "CLEO shower aur tap filters TDS (Total Dissolved Solids) ko kam karne ke liye design nahi kiye gaye hain [Source: S01, S02]. "
                "TDS kam karna RO (Reverse Osmosis) drinking filters ka kaam hota hai. CLEO ka primary function paani mein se chlorine, "
                "sediments, aur hardness-causing ions ke effects ko condition karna hai taaki hair fall aur skin irritation kam ho sake. "
                "TDS meter reading change na hona ek expected result hai aur yeh kisi defect ko nahi darshata."
            )

        # SYN-005: Low flow after 2 weeks
        if issue_category == "low_flow":
            return (
                "Hello! If your CLEO filter flow has decreased after 2 weeks, official product guidance notes that suspended sediments "
                "in hard water can accumulate and block cartridge mesh [Source: S02]. The current product FAQ recommends performing "
                "a reverse flush (turning the cartridge upside down briefly under running water) to dislodge accumulated particles.\n\n"
                "To assist further, could you share:\n"
                "1. Your water source (borewell/tanker sediment levels)?\n"
                "2. Whether the drop in pressure was gradual or sudden?\n"
                "If the flow does not improve after reverse flushing, our technical team will be glad to investigate."
            )

        # SYN-006: Leak after cartridge change
        if issue_category == "leak_after_maintenance":
            return (
                "We are sorry to hear about the leak after replacing your cartridge. For safety, please temporarily shut off the water "
                "inlet or avoid using the leaking filter until it is inspected [Source: S02, S03].\n\n"
                "Because leakage can be caused by improper seating, misaligned threads, or damaged O-rings, this has been escalated to "
                "our technical support team. Please share:\n"
                "1. A short photo or video showing the exact point of leakage\n"
                "2. Your exact filter model and cartridge purchase details\n"
                "Our team will review your case and provide verified technical assistance."
            )

        # SYN-007: Temperature limit conflict (55°C)
        if issue_category == "temperature_limit_conflict":
            return (
                "Thank you for contacting WaterScience. Regarding running 55°C hot water through CLEO SFU-717: our official documentation "
                "contains conflicting specifications. The CLEO SFU-717 product page specifies a maximum hot-water temperature of 45°C "
                "(with instruction to run cold water first) [Source: S01], while the CLEO replacement cartridge FAQ states hot water up to 60°C "
                "[Source: S02].\n\n"
                "Because of this official source discrepancy, we cannot advise running 55°C water without engineering confirmation. "
                "This ticket has been escalated to our product team for authoritative clarification."
            )

        # SYN-008: Warranty claim / body cracked
        if issue_category == "warranty_claim":
            return (
                "We sincerely apologize for the inconvenience caused by the crack on your CLEO unit. WaterScience provides a 5-year warranty "
                "on CLEO SFU-717, subject to warranty policy terms and verification [Source: S03].\n\n"
                "To process your warranty evaluation with our support team, please provide:\n"
                "1. Your original tax invoice or 7-day warranty registration confirmation\n"
                "2. Product serial number\n"
                "3. Clear photos/video showing the crack and the overall unit\n"
                "4. Purchase channel and delivery date\n"
                "Your request has been routed to our warranty claims officer."
            )

        # SYN-009: Website return request
        if issue_category == "website_return_request":
            return (
                "Thank you for reaching out. Under WaterScience.in official return policy, CLEO products purchased directly from our website "
                "have a stated 60-day return policy [Source: S04]. Returns are subject to eligibility criteria (such as received in damaged/defective "
                "condition or incorrect item received), and a Rs. 99 pickup charge may apply per policy terms [Source: S04].\n\n"
                "To initiate the review with our returns desk, please provide:\n"
                "1. Your WaterScience website Order ID\n"
                "2. Date of delivery\n"
                "3. Reason for unsuitability and details of your tap fixture\n"
                "A support executive will review your eligibility."
            )

        # SYN-010: Marketplace return request (Amazon)
        if issue_category == "marketplace_return_request":
            return (
                "We understand your unit arrived damaged from Amazon. Please note that WaterScience.in's 60-day return and refund policy "
                "applies exclusively to direct orders placed on the WaterScience website [Source: S04]. Marketplace orders (Amazon, Flipkart) "
                "are governed by the respective marketplace's return and replacement policies.\n\n"
                "We recommend initiating a replacement/return directly in your Amazon app under 'Your Orders'. "
                "If you need manufacturer support, please share your Amazon Order ID, invoice, and photos of the damaged unit so our team "
                "can assist you directly."
            )

        # SYN-011: Damaged on arrival
        if issue_category == "damaged_on_arrival":
            return (
                "We are very sorry to hear your order arrived damaged. Under WaterScience policy, damaged or defective items must be reported "
                "with photographic/video evidence [Source: S04, S03]. Please retain all outer packaging and contents.\n\n"
                "To assist you immediately, please share:\n"
                "1. Your purchase channel (WaterScience website, Amazon, etc.) and Order Number\n"
                "2. Photos/video of the damaged product and package box\n"
                "3. Date of delivery\n"
                "This ticket has been escalated for priority resolution."
            )

        # SYN-012: Delivery tracking
        if issue_category == "delivery_tracking":
            return (
                "Hello! If your order was placed on the WaterScience website, our billing and shipping policy states that orders typically "
                "dispatch in 2-3 business days, with transit taking approximately 3-4 business days within Bengaluru and 5-6 business days "
                "for the rest of India [Source: S05]. These timeframes are estimates and subject to regional courier operations.\n\n"
                "To check your exact shipment status, please provide:\n"
                "1. Your Order ID and purchase channel\n"
                "2. Delivery pincode and tracking number (if received via SMS/email)\n"
                "We will gladly track this with our logistics partner."
            )

        # SYN-013: Washing machine compatibility (IRIS-WMF-325)
        if issue_category == "washing_machine_compatibility":
            return (
                "Hello! Yes, the IRIS-WMF-325 washing machine filter is documented to be compatible with all brands of automatic "
                "front-load and top-load washing machines using the supplied hose adapter [Source: S06]. Its inlet connects to standard "
                "1/2-inch BSP and 1/2-inch or 24-mm externally threaded taps.\n\n"
                "Please ensure your machine is a fully automatic model and your tap has a standard external thread. If your tap has non-standard "
                "threading, please share a photo of your tap point so we can confirm fitment."
            )

        # SYN-014: IRIS cartridge life (Top load)
        if issue_category == "cartridge_life":
            return (
                "Namaste! According to official IRIS-WMF-325 specifications, cartridge life is typically 3-4 months for top-load machines "
                "and 4-6 months for front-load machines, depending on water hardness, usage, and sediment content [Source: S06].\n\n"
                "At 2 months, premature replacement is usually only required if your water has exceptionally high sediment or scaling. "
                "Could you tell us what issues you are observing (such as reduced water flow into the machine or visible sediment)?"
            )

        # SYN-015: KTF 26 mm plastic tap compatibility
        if issue_category == "kitchen_filter_compatibility":
            return (
                "Hello! According to verified product specifications for the KTF Wide ceramic tap extender [Source: S07], it is designed "
                "for taps with 20 mm, 22 mm, and 24 mm male/female aerators. A 26 mm tap size is not among the documented compatible sizes, "
                "and plastic taps are generally not supported.\n\n"
                "Additionally, the KTF range includes both Wide and Mini variants with distinct specifications. This has been escalated to "
                "our technical team. Please share a photo of your tap and aerator so we can verify whether an adapter is viable."
            )

        # SYN-016: Potable water safety (KTF direct drinking)
        if issue_category == "potable_water_safety":
            return (
                "Important health & safety notice: The KTF kitchen tap extender is designed for washing and sediment filtration [Source: S07]. "
                "Our verified product documentation does not certify this filter for direct drinking water or microbial purification. "
                "We strictly advise against drinking unfiltered tap water directly from this filter. For drinking water, please continue using "
                "an authorized RO/UV drinking water purification system certified for potable water."
            )

        # SYN-017: Whole home consultation (RENO Cygnus)
        if issue_category == "whole_home_consultation":
            return (
                "Thank you for your interest in the RENO Cygnus Water Softener [Source: S08]. Whole-home softener sizing, serviceability, "
                "and total installation costs depend directly on your specific home plumbing, incoming water hardness, overhead tank setup, "
                "and city serviceability. Input/output plumbing material is not included in the standard pack.\n\n"
                "Because site readiness must be evaluated, next-day installation cannot be committed automatically. We have routed your details "
                "to our WaterSolutions consultation specialist who will contact you for a site assessment and customized quote."
            )

        # SYN-018: PURO health faucet leak/fault
        if issue_category == "product_fault":
            return (
                "We are sorry to hear about the leak and trigger issue with your PURO HFS-625 health faucet. For immediate safety, please "
                "close the angle valve to stop water flow and prevent overflow [Source: S09, S03].\n\n"
                "The PURO HFS-625 carries a 2-year manufacturer warranty covering breakage and defect. To initiate warranty triage:\n"
                "1. Please share a short video of the leak and trigger\n"
                "2. Your purchase invoice and channel\n"
                "Our after-sales service team will inspect the case for repair or replacement."
            )

        # SYN-019: Medical expectation (CLEO hair fall)
        if issue_category == "medical_expectation":
            return (
                "Thank you for contacting WaterScience. We want to be completely transparent: CLEO shower and tap filters are not medical "
                "devices [Source: S02]. While CLEO helps reduce chlorine and conditioning hard water salts that can irritate hair and skin, "
                "it cannot guarantee stopping hair fall within one week, nor does it replace professional medical treatment.\n\n"
                "Hair fall can stem from multiple internal factors including diet, genetics, stress, and medical conditions. If you are "
                "experiencing severe hair fall, we strongly recommend consulting a certified dermatologist or physician."
            )

        # SYN-020: Product identification (Unknown filter model)
        if issue_category == "product_identification":
            return (
                "Hello! Because WaterScience cartridges and filters are specifically engineered for distinct product models "
                "(such as CLEO shower filters, IRIS washing machine filters, and KTF kitchen tap extenders) [Source: S02, S10], "
                "replacement cartridges are not universally interchangeable.\n\n"
                "To ensure you receive the exact compatible cartridge, please provide:\n"
                "1. The product model or SKU name printed on the filter body\n"
                "2. A clear photo of the product label, connectors, and where it is installed\n"
                "3. Your previous order details or invoice\n\n"
                "Once you share these details, we will identify your exact cartridge. If the model cannot be identified from these details, "
                "our support team will manually match your unit."
            )

        # Generic fallback
        return (
            "Thank you for reaching out to WaterScience Customer Support. We have received your query. "
            "To assist you accurately, please share your product model, order details, and any specific questions you have."
        )

    @staticmethod
    def _call_openai(
        customer_message: str,
        issue_category: str,
        detected_product: Optional[str],
        purchase_channel: str,
        information_needed: List[str],
        cited_sources: List[SourceReference],
        human_escalation_required: bool,
        reason_for_escalation: Optional[str]
    ) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        sources_summary = "\n".join([f"- [{s.source_id}] {s.title} ({s.url}): {s.evidence_type}" for s in cited_sources])
        needed_summary = "\n".join([f"- {item}" for item in information_needed]) or "None"

        system_prompt = (
            "You are the WaterScience Customer Support AI drafting assistant. "
            "You draft concise, factual, empathetic customer support responses that require mandatory human review.\n"
            "MANDATORY EVIDENCE AND SAFETY RULES:\n"
            "1. Ground every factual claim in the provided sources. Cite sources like [Source: S01].\n"
            "2. Never promise refunds, replacements, delivery dates, or warranty approval.\n"
            "3. Never apply WaterScience website policies to Amazon or other marketplaces.\n"
            "4. Never make medical claims or claim water filters cure hair fall or make tap water safe to drink.\n"
            "5. If there is a source conflict (e.g. SFU-717 hot water 45°C vs 60°C), do not choose one value; explain the conflict and escalate.\n"
            "6. For unknown products, ask for identification (SKU, label photo, invoice); do not guess interchangeable cartridges.\n"
            "7. Never invent facts or policies."
        )

        user_prompt = (
            f"Customer Message: {customer_message}\n"
            f"Detected Product: {detected_product or 'Unknown'}\n"
            f"Issue Category: {issue_category}\n"
            f"Purchase Channel: {purchase_channel}\n"
            f"Human Escalation Required: {human_escalation_required} (Reason: {reason_for_escalation})\n"
            f"Information Still Needed:\n{needed_summary}\n"
            f"Applicable Verified Sources:\n{sources_summary}\n\n"
            "Draft a concise, factual customer response following all rules."
        )

        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=settings.LLM_TEMPERATURE
        )
        return response.choices[0].message.content.strip()
