import json
import csv
from typing import Dict, Any, Optional, List
from pathlib import Path
from app.config import settings
from app.models import SourceReference

class KnowledgeBase:
    _instance = None

    def __init__(self, kb_path: Optional[Path] = None, register_path: Optional[Path] = None):
        self.kb_path = kb_path or settings.KNOWLEDGE_BASE_PATH
        self.register_path = register_path or settings.RESEARCH_REGISTER_PATH
        self.data: Dict[str, Any] = {}
        self.sources: Dict[str, Dict[str, Any]] = {}
        self.products: Dict[str, Dict[str, Any]] = {}
        self.policy_facts: Dict[str, Dict[str, Any]] = {}
        self.guardrails: List[str] = []
        self.routing_rules: List[Dict[str, Any]] = []
        self.findings: List[Dict[str, Any]] = []
        self.load()

    def load(self):
        if not self.kb_path.exists():
            raise FileNotFoundError(f"Knowledge base not found at: {self.kb_path}")

        with open(self.kb_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.sources = self.data.get("sources", {})
        self.products = self.data.get("products", {})
        self.policy_facts = self.data.get("policy_facts", {})
        self.guardrails = self.data.get("guardrails", [])
        self.routing_rules = self.data.get("routing_rules", [])

        if self.register_path.exists():
            with open(self.register_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self.findings = list(reader)

    def get_source(self, source_id: str) -> Optional[SourceReference]:
        raw = self.sources.get(source_id)
        if not raw:
            return None
        return SourceReference(
            source_id=source_id,
            title=raw.get("title", f"Source {source_id}"),
            url=raw.get("url"),
            evidence_type=raw.get("type", "official source")
        )

    def get_sources(self, source_ids: List[str]) -> List[SourceReference]:
        refs = []
        for sid in source_ids:
            s = self.get_source(sid)
            if s:
                refs.append(s)
        return refs

    def get_product(self, product_key: str) -> Optional[Dict[str, Any]]:
        return self.products.get(product_key)

    def find_product_by_name(self, text: str) -> Optional[tuple[str, Dict[str, Any]]]:
        text_lower = text.lower()
        # Specific model matching first
        if "sfu-717" in text_lower or "sfu 717" in text_lower:
            return "CLEO_SFU_717", self.products["CLEO_SFU_717"]
        if "iris" in text_lower or "wmf-325" in text_lower or "wmf 325" in text_lower or "washing machine" in text_lower:
            return "IRIS_WMF_325", self.products["IRIS_WMF_325"]
        if "puro" in text_lower or "hfs-625" in text_lower or "health faucet" in text_lower:
            return "PURO_HFS_625", self.products["PURO_HFS_625"]
        if "reno" in text_lower or "cygnus" in text_lower or "softener" in text_lower:
            return "RENO_CYGNUS", self.products["RENO_CYGNUS"]
        if "ktf" in text_lower or "kitchen tap extender" in text_lower or "ceramic cartridge" in text_lower:
            return "KTF_WIDE_CERAMIC", self.products["KTF_WIDE_CERAMIC"]
        if "cleo" in text_lower and ("cartridge" in text_lower or "replacement" in text_lower or "refill" in text_lower):
            return "CLEO_REPLACEMENT_CARTRIDGE", self.products["CLEO_REPLACEMENT_CARTRIDGE"]
        if "cleo" in text_lower:
            return "CLEO_SFU_717", self.products["CLEO_SFU_717"]
        return None

# Singleton accessor
_kb_instance = None

def get_knowledge_base() -> KnowledgeBase:
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = KnowledgeBase()
    return _kb_instance
