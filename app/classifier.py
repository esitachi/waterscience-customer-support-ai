import re
from typing import Tuple, List, Optional
from app.models import PurchaseChannel

class IssueClassifier:
    """
    Classifies incoming customer messages into standard categories,
    detects mentioned products, and maps relevant verified source IDs.
    """

    @staticmethod
    def classify(
        text: str,
        product_hint: Optional[str] = None,
        explicit_channel: Optional[str] = None
    ) -> Tuple[str, Optional[str], List[str]]:
        """
        Returns:
            issue_category: str
            detected_product: Optional[str]
            relevant_source_ids: List[str]
        """
        t = text.lower()
        
        # 1. Product detection
        detected_product = None
        if product_hint:
            hint_lower = product_hint.lower()
            if "sfu" in hint_lower or "717" in hint_lower:
                detected_product = "CLEO SFU-717"
            elif "iris" in hint_lower or "wmf" in hint_lower:
                detected_product = "IRIS-WMF-325"
            elif "ktf" in hint_lower:
                if "wide" in hint_lower or "ceramic" in hint_lower:
                    detected_product = "KTF Kitchen Tap Extender"
                else:
                    detected_product = "KTF variant unknown"
            elif "reno" in hint_lower or "cygnus" in hint_lower:
                detected_product = "RENO Cygnus"
            elif "puro" in hint_lower or "hfs" in hint_lower:
                detected_product = "PURO HFS-625"
            elif "cartridge" in hint_lower:
                detected_product = "CLEO replacement cartridge"

        if not detected_product:
            if "sfu-717" in t or "sfu 717" in t or "sfu717" in t:
                detected_product = "CLEO SFU-717"
            elif "iris" in t or "wmf-325" in t or "wmf 325" in t or "washing machine" in t or "front load" in t or "top load" in t or "top loader" in t or "front-load" in t:
                detected_product = "IRIS-WMF-325"
            elif ("ktf" in t or "kitchen tap extender" in t) and ("cleo" not in t and "sfu" not in t):
                if any(w in t for w in ["direct peena", "peena", "drink", "milk", "baby", "infant", "formula", "potable", "consume"]):
                    detected_product = "KTF Kitchen Tap Extender"
                else:
                    detected_product = "KTF variant unknown"
            elif "reno" in t or "cygnus" in t or "whole home" in t or "softener" in t:
                detected_product = "RENO Cygnus"
            elif "puro" in t or "health faucet" in t or "hfs-625" in t:
                detected_product = "PURO HFS-625"
            elif "cleo" in t:
                if "cartridge" in t or "borewell" in t or "metro" in t or "municipal" in t:
                    detected_product = "CLEO replacement cartridge"
                else:
                    detected_product = "CLEO SFU-717"
            elif any(w in t for w in ["model yaad nahi", "send me two new cartridges", "cartridge for my filter at home", "replacement cartridge"]):
                detected_product = "unknown WaterScience filter"
            elif any(w in t for w in ["parcel", "order", "package", "where is my", "tracking"]):
                detected_product = "unknown WaterScience product"

        # 2. Issue Category Classification (Safety-First Ordering)
        category = "general_inquiry"
        source_ids = []

        # Temperature limit conflict (Safety critical)
        if any(w in t for w in ["hot water", "degree", "celsius", "temperature", "geyser", "solar water", "garam paani", "75 degree", "55 degree"]):
            category = "temperature_limit_conflict"
            detected_product = detected_product or "CLEO SFU-717"
            source_ids = ["S01", "S02"]

        # Potable water safety (Health / Ingestion critical)
        elif any(w in t for w in ["direct peena", "peena", "peene", "safe to drink", "drink", "drinking", "potable", "baby milk", "infant", "pure for drinking", "viruses"]):
            category = "potable_water_safety"
            detected_product = detected_product or (
                "KTF Kitchen Tap Extender" if "ktf" in t or "kitchen" in t else (detected_product or "CLEO SFU-717")
            )
            source_ids = ["S07"] if "ktf" in t or "kitchen" in t else ["S01", "S02"]

        # Medical expectation (Health critical) - use word boundary for short words like skin/cure
        elif any(w in t for w in ["hair fall", "hairfall", "hair loss", "doctor", "dandruff", "alopecia", "minoxidil"]) or re.search(r'\b(skin|cure)\b', t):
            category = "medical_expectation"
            detected_product = detected_product or "CLEO SFU-717"
            source_ids = ["S02"]

        # Product fault / faucet trigger fault (check before generic filter leak)
        elif "puro" in t or ("health faucet" in t and any(w in t for w in ["leak", "trigger", "fault"])) or "trigger work nahi" in t:
            category = "product_fault"
            detected_product = "PURO HFS-625"
            source_ids = ["S09", "S03"]

        # Leak after maintenance / plumbing & electrical hazard (Safety critical)
        elif any(w in t for w in ["leak", "leaking", "spraying", "drip", "seeping", "burst", "paani leak", "beech se paani", "leakage"]):
            category = "leak_after_maintenance"
            source_ids = ["S02", "M01", "S03"]

        # Damaged on arrival
        elif any(w in t for w in ["damaged", "tuta", "broken", "smashed", "broke box"]) and any(w in t for w in ["parcel", "package", "delivered", "box"]):
            category = "damaged_on_arrival"
            source_ids = ["S04", "S03"]

        # Warranty claim (including replacement requests and social engineering override attempts)
        elif any(w in t for w in ["warranty", "guarantee", "shell cracked", "body cracked", "cracked", "replace it under warranty", "replacement unit", "send a replacement", "replacement without"]):
            category = "warranty_claim"
            source_ids = ["S03"]
            if detected_product == "CLEO SFU-717" or "cartridge" in t:
                source_ids.append("S02")

        # Return & Refund requests: Marketplace vs Website
        elif any(w in t for w in ["refund", "wapas", "not suitable", "return", "money back"]):
            is_marketplace = (
                explicit_channel in [PurchaseChannel.AMAZON.value, PurchaseChannel.FLIPKART.value, PurchaseChannel.QUICK_COMMERCE.value, PurchaseChannel.RETAIL.value]
                or any(w in t for w in ["amazon", "flipkart", "blinkit", "zepto", "retail", "shop", "sanitary shop", "offline"])
            )
            if is_marketplace:
                category = "marketplace_return_request"
                source_ids = ["S04"]
            else:
                category = "website_return_request"
                source_ids = ["S04", "S01"]

        # Delivery tracking & Shipping Inquiries (including domestic policy and international inquiries)
        elif any(w in t for w in ["tracking", "trackin", "stuck", "kab aayega", "dispatch", "delivering", "where is my", "when will it arrive", "ship to", "shipping to", "international", "dubai"]):
            category = "delivery_tracking"
            detected_product = detected_product or "unknown WaterScience product"
            source_ids = ["S05"]

        # Low flow troubleshooting (prioritize over routine cartridge queries when operational flow is impaired)
        elif any(w in t for w in ["flow", "pressure", "trickle", "slow", "kam", "weak", "choke"]):
            category = "low_flow"
            detected_product = detected_product or "CLEO SFU-717"
            source_ids = ["S02"]

        # Cartridge Life / Duration (appliance or general - requires lifecycle/duration query)
        elif ("cartridge" in t or "cylinder" in t) and any(w in t for w in ["months", "life", "expire", "longevity", "how long", "lifespan", "duration"]):
            category = "cartridge_life"
            detected_product = detected_product or "IRIS-WMF-325"
            source_ids = ["S06"]

        # Cartridge Selection & Media Inquiries (Municipal vs Borewell, KDF/composition)
        elif any(w in t for w in ["borewell", "metro", "municipal", "tanker", "cauvery", "chlorine", "cartridge loon", "which cartridge", "kdf", "zinc and copper", "chemical percentage", "proprietary chemical"]):
            category = "cartridge_selection"
            detected_product = "CLEO replacement cartridge"
            source_ids = ["S01", "S02"]

        # Whole home consultation (RENO Cygnus - check before general TDS if whole home/softener is mentioned)
        elif detected_product == "RENO Cygnus" or any(w in t for w in ["reno", "cygnus", "whole home", "softener", "plant", "effluent"]):
            category = "whole_home_consultation"
            detected_product = "RENO Cygnus"
            source_ids = ["S08"]

        # TDS expectation
        elif "tds" in t and any(w in t for w in ["same", "reduce", "fake", "meter", "ppm", "600", "drop", "nakli"]):
            category = "tds_expectation"
            detected_product = detected_product or "CLEO SFU-717"
            source_ids = ["S01", "S02"]

        # Unknown product identification (SYN-020 & general)
        elif (detected_product is None or detected_product in ["unknown WaterScience filter", "unknown WaterScience product"]) and (
            any(w in t for w in ["cartridge", "replacement", "model", "photo", "send me", "which filter"])
        ):
            category = "product_identification"
            detected_product = "unknown WaterScience filter"
            source_ids = ["S02", "S10"]

        # Kitchen filter compatibility
        elif (detected_product in ["KTF variant unknown", "KTF Kitchen Tap Extender"] or "ktf" in t or "kitchen tap extender" in t) and (detected_product != "CLEO SFU-717" and "sfu" not in t and "cleo" not in t):
            category = "kitchen_filter_compatibility"
            source_ids = ["S07"]

        # Washing machine compatibility
        elif detected_product == "IRIS-WMF-325" or any(w in t for w in ["washing machine", "top load", "front load", "laundromat", "washer"]):
            category = "washing_machine_compatibility"
            detected_product = detected_product or "IRIS-WMF-325"
            source_ids = ["S06"]

        # General Compatibility & DIY Installation (including plumber requests)
        elif any(w in t for w in ["fit", "fitting", "lag jayega", "plastic", "tap", "metal", "steel", "thread", "chudi", "aerator", "plumber", "installation", "install"]):
            category = "compatibility"
            detected_product = detected_product or "CLEO SFU-717"
            source_ids = ["S01"]

        return category, detected_product, source_ids
