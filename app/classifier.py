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
                detected_product = "KTF variant unknown"
            elif "reno" in hint_lower:
                detected_product = "RENO Cygnus"
            elif "puro" in hint_lower:
                detected_product = "PURO HFS-625"

        if not detected_product:
            if "sfu-717" in t or "sfu 717" in t:
                detected_product = "CLEO SFU-717"
            elif "iris" in t or "wmf-325" in t or "wmf 325" in t or "front-load" in t or "front load" in t or "top load" in t or "washing machine" in t:
                detected_product = "IRIS-WMF-325"
            elif "ktf" in t or "kitchen tap" in t:
                if "direct peena" in t or "peena" in t or "drink" in t:
                    detected_product = "KTF Kitchen Tap Extender"
                else:
                    detected_product = "KTF variant unknown"
            elif "reno" in t or "cygnus" in t or "softener" in t:
                detected_product = "RENO Cygnus"
            elif "puro" in t or "health faucet" in t or "hfs-625" in t:
                detected_product = "PURO HFS-625"
            elif "cleo" in t:
                if "cartridge" in t or "borewell water" in t or "metro" in t:
                    detected_product = "CLEO replacement cartridge"
                else:
                    detected_product = "CLEO SFU-717"
            elif "model yaad nahi" in t or ("replacement" in t and "filter" in t and "photo" in t):
                detected_product = "unknown WaterScience filter"
            elif "parcel" in t or "order" in t:
                detected_product = "unknown WaterScience product"

        # 2. Issue Category Classification
        category = "general_inquiry"
        source_ids = []

        # Temperature limit conflict
        if ("hot water" in t or "55 degree" in t or "temperature" in t or "degree hot water" in t) and ("sfu" in t or "cleo" in t):
            category = "temperature_limit_conflict"
            source_ids = ["S01", "S02"]

        # Medical expectation
        elif any(w in t for w in ["hair fall", "hairfall", "hair loss", "doctor", "skin", "dandruff"]):
            category = "medical_expectation"
            source_ids = ["S02"]

        # Potable water safety
        elif any(w in t for w in ["direct peena", "peena", "peene", "safe to drink", "drink", "potable"]):
            category = "potable_water_safety"
            source_ids = ["S07"]

        # Leak after maintenance
        elif "leak" in t and ("cartridge change" in t or "beech se paani" in t or "filter ke beech" in t):
            category = "leak_after_maintenance"
            source_ids = ["S02", "M01", "S03"]

        # Product fault / faucet leak
        elif "puro" in t or ("health faucet" in t and "leak" in t) or "trigger work nahi" in t:
            category = "product_fault"
            source_ids = ["S09", "S03"]

        # Warranty claim (body cracked)
        elif ("body cracked" in t or "cracked" in t) and ("warranty" in t or "replace it" in t):
            category = "warranty_claim"
            source_ids = ["S03"]

        # Damaged on arrival
        elif ("parcel" in t or "package" in t) and ("damaged" in t or "tuta" in t or "broken" in t):
            category = "damaged_on_arrival"
            source_ids = ["S04", "S03"]

        # Return requests: Marketplace vs Website
        elif "refund" in t or "wapas" in t or "not suitable" in t or "return" in t:
            if "amazon" in t or explicit_channel == PurchaseChannel.AMAZON.value:
                category = "marketplace_return_request"
                source_ids = ["S04"]
            else:
                category = "website_return_request"
                source_ids = ["S04", "S01"]

        # Delivery tracking
        elif ("order" in t or "parcel" in t) and ("stuck" in t or "kab aayega" in t or "tracking" in t or "dispatch" in t or "delivery" in t):
            category = "delivery_tracking"
            source_ids = ["S05"]

        # Washing machine compatibility & life
        elif detected_product == "IRIS-WMF-325" or "iris" in t:
            if "cartridge" in t and ("months" in t or "replace" in t or "life" in t):
                category = "cartridge_life"
                source_ids = ["S06"]
            else:
                category = "washing_machine_compatibility"
                source_ids = ["S06"]

        # Kitchen filter compatibility
        elif detected_product in ["KTF variant unknown", "KTF Kitchen Tap Extender"] or "ktf" in t:
            category = "kitchen_filter_compatibility"
            source_ids = ["S07"]

        # Whole home consultation
        elif detected_product == "RENO Cygnus" or "reno" in t or "softener" in t:
            category = "whole_home_consultation"
            source_ids = ["S08"]

        # Unknown product identification (SYN-020)
        elif "model yaad nahi" in t or ("replacement" in t and "photo" in t and (not detected_product or "unknown" in detected_product)):
            category = "product_identification"
            detected_product = "unknown WaterScience filter"
            source_ids = ["S02", "S10"]

        # Cartridge selection
        elif ("metro" in t or "borewell" in t or "cartridge loon" in t) and "cartridge" in t:
            category = "cartridge_selection"
            detected_product = "CLEO replacement cartridge"
            source_ids = ["S01", "S02"]

        # TDS expectation
        elif "tds" in t and ("same" in t or "reduce" in t or "fake" in t or "meter" in t):
            category = "tds_expectation"
            detected_product = "CLEO SFU-717"
            source_ids = ["S01", "S02"]

        # Low flow
        elif "flow" in t and ("slow" in t or "kam" in t or "drop" in t):
            category = "low_flow"
            detected_product = "CLEO SFU-717"
            source_ids = ["S02"]

        # Compatibility (CLEO)
        elif "fit" in t or "lag jayega" in t or "plastic" in t or "tap" in t:
            category = "compatibility"
            detected_product = detected_product or "CLEO SFU-717"
            source_ids = ["S01"]

        return category, detected_product, source_ids
