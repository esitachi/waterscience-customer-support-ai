"""
WaterScience Support Platform — URL-Based Knowledge Management & Crawler Engine
Crawls official WaterScience website sources, normalizes HTML, computes SHA-256 hashes,
detects content modifications and policy conflicts, stages versioned drafts, and manages
one-click publish / rollback workflows for non-technical support managers.
"""

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.database import (
    SessionLocal,
    KnowledgeSourceRecord,
    KnowledgeVersionRecord,
    AuditLogRecord
)
from app.knowledge import get_knowledge_base

logger = logging.getLogger("crawler")

def normalize_html_content(html: str) -> Tuple[str, str, Dict[str, Any]]:
    """
    Extracts, cleans, and normalizes text from website HTML.
    Returns:
        normalized_text: str
        content_hash: str (SHA-256)
        metadata: Dict[str, Any]
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove script, style, nav, footer, and noscript elements
    for element in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
        element.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag and meta_tag.get("content"):
        meta_desc = meta_tag["content"].strip()

    # Extract all visible text
    raw_text = soup.get_text(separator=" ")
    # Normalize whitespace
    normalized_text = " ".join(raw_text.split()).strip()

    # Calculate SHA-256 hash of normalized text
    content_hash = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()

    # Extract key operational facts/specifications if present
    facts = {}
    lower_text = normalized_text.lower()
    
    # Check for thread sizes
    if "mm" in lower_text or "thread" in lower_text:
        thread_matches = re.findall(r'\b(20|22|24|28)\b', lower_text)
        if thread_matches:
            facts["thread_sizes_mm"] = sorted(list(set(thread_matches)))

    # Check for temperature limits
    temp_matches = re.findall(r'\b(40|45|50|55|60|65)\s*(?:°c|celsius|degree)\b', lower_text)
    if temp_matches:
        facts["temperature_max_c"] = sorted(list(set(temp_matches)))

    # Check for warranty duration
    warranty_matches = re.findall(r'\b(90[- ]day|6[- ]month|1[- ]year|2[- ]year|5[- ]year)\b', lower_text)
    if warranty_matches:
        facts["warranty_terms"] = sorted(list(set(warranty_matches)))

    metadata = {
        "title": title,
        "description": meta_desc,
        "detected_facts": facts,
        "text_length": len(normalized_text)
    }

    return normalized_text, content_hash, metadata


class KnowledgeSyncEngine:
    """Orchestrates URL crawling, diff detection, staging, and version publishing."""

    @staticmethod
    def crawl_source(url: str, timeout_seconds: float = 10.0) -> Dict[str, Any]:
        """Fetches and normalizes a single URL using httpx."""
        headers = {
            "User-Agent": "WaterScience-Knowledge-Sync/2.0 (Customer Support Knowledge Verification Bot)"
        }
        try:
            with httpx.Client(timeout=timeout_seconds, follow_redirects=True, headers=headers) as client:
                resp = client.get(url)
                if resp.status_code >= 400:
                    return {
                        "success": False,
                        "error": f"HTTP {resp.status_code}: {resp.reason_phrase}"
                    }
                norm_text, chash, meta = normalize_html_content(resp.text)
                return {
                    "success": True,
                    "normalized_text": norm_text,
                    "content_hash": chash,
                    "metadata": meta
                }
        except Exception as e:
            logger.warning(f"Failed to crawl {url}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def sync_all_sources(
        db: Session,
        simulated_contents: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Crawls all registered official sources:
        - Detects unchanged pages (no version bump)
        - Detects modified pages (generates draft version with change summary)
        - Handles crawl failures gracefully (preserves existing valid facts)
        """
        sources = db.query(KnowledgeSourceRecord).all()
        now_dt = datetime.now(timezone.utc)

        unchanged_sources: List[str] = []
        modified_sources: List[Dict[str, Any]] = []
        failed_sources: List[Dict[str, Any]] = []

        for src in sources:
            # 1. Fetch content (or use simulated mock content for offline tests)
            if simulated_contents and src.source_id in simulated_contents:
                raw_html = simulated_contents[src.source_id]
                norm_text, chash, meta = normalize_html_content(raw_html)
                crawl_res = {
                    "success": True,
                    "normalized_text": norm_text,
                    "content_hash": chash,
                    "metadata": meta
                }
            elif src.url.startswith("http://") or src.url.startswith("https://"):
                crawl_res = KnowledgeSyncEngine.crawl_source(src.url)
            else:
                # Mock / legacy local record
                crawl_res = {
                    "success": True,
                    "normalized_text": src.title,
                    "content_hash": hashlib.sha256(src.title.encode("utf-8")).hexdigest(),
                    "metadata": {"title": src.title, "detected_facts": {}}
                }

            # 2. Handle failure scenario (retain existing valid knowledge)
            if not crawl_res.get("success"):
                src.status = "failed"
                src.last_error = crawl_res.get("error", "Unknown crawl failure")
                failed_sources.append({
                    "source_id": src.source_id,
                    "url": src.url,
                    "error": src.last_error
                })
                continue

            new_hash = crawl_res["content_hash"]
            norm_text = crawl_res["normalized_text"]
            src.last_crawled_at = now_dt
            src.last_error = None

            # 3. Compare with stored hash
            if src.content_hash == new_hash:
                # No-change scenario
                src.status = "valid"
                unchanged_sources.append(src.source_id)
            else:
                # Website change scenario!
                is_first_sync = (src.content_hash is None)
                old_hash = src.content_hash
                src.content_hash = new_hash
                src.extracted_text = norm_text[:2000]  # Store preview
                src.status = "valid" if is_first_sync else "modified"

                if not is_first_sync:
                    # Detect potential conflicts or changes
                    detected_facts = crawl_res.get("metadata", {}).get("detected_facts", {})
                    modified_sources.append({
                        "source_id": src.source_id,
                        "title": src.title,
                        "url": src.url,
                        "old_hash": old_hash,
                        "new_hash": new_hash,
                        "detected_facts": detected_facts,
                        "change_note": f"Content updated on official page ({len(norm_text)} chars)."
                    })
                else:
                    unchanged_sources.append(src.source_id)

        db.commit()

        # 4. Versioning Decision
        if len(modified_sources) == 0:
            # No changes detected: do not create unnecessary new version
            return {
                "sync_status": "unchanged",
                "total_sources": len(sources),
                "unchanged_count": len(unchanged_sources),
                "modified_count": 0,
                "failed_count": len(failed_sources),
                "failed_sources": failed_sources,
                "message": f"All {len(unchanged_sources)} active sources are up-to-date. Current published knowledge remains active.",
                "proposed_version": None
            }
        else:
            # Changes detected: prepare a Draft Knowledge Version for manager review
            max_v = db.query(KnowledgeVersionRecord).order_by(KnowledgeVersionRecord.version_number.desc()).first()
            next_version = (max_v.version_number + 1) if max_v else 2

            summary_lines = [
                f"Sync detected changes in {len(modified_sources)} source(s):",
            ]
            for m in modified_sources:
                facts_str = f" | Detected: {m['detected_facts']}" if m['detected_facts'] else ""
                summary_lines.append(f"• [{m['source_id']}] {m['title']}{facts_str}")

            change_summary_text = "\n".join(summary_lines)

            draft_v = KnowledgeVersionRecord(
                version_number=next_version,
                status="draft",
                change_summary=change_summary_text,
                diff_json=json.dumps(modified_sources),
                created_by="system_crawler",
                created_at=now_dt
            )
            db.add(draft_v)
            db.commit()

            return {
                "sync_status": "draft_proposed",
                "total_sources": len(sources),
                "unchanged_count": len(unchanged_sources),
                "modified_count": len(modified_sources),
                "failed_count": len(failed_sources),
                "failed_sources": failed_sources,
                "proposed_version": next_version,
                "change_summary": change_summary_text,
                "modified_details": modified_sources,
                "message": f"Detected updates across {len(modified_sources)} sources. Draft Version {next_version} ready for manager publication."
            }

    @staticmethod
    def publish_version(db: Session, version_number: int, approved_by: str = "support_manager", notes: Optional[str] = None) -> Dict[str, Any]:
        """Publishes a validated draft knowledge version and invalidates caches."""
        draft = db.query(KnowledgeVersionRecord).filter_by(version_number=version_number).first()
        if not draft:
            raise ValueError(f"Knowledge version {version_number} does not exist.")

        # Archive any currently published versions
        published_versions = db.query(KnowledgeVersionRecord).filter_by(status="published").all()
        for pv in published_versions:
            pv.status = "archived"

        # Publish the new version
        now_dt = datetime.now(timezone.utc)
        draft.status = "published"
        draft.published_at = now_dt
        draft.created_by = approved_by

        # Mark all sources back to valid
        for s in db.query(KnowledgeSourceRecord).all():
            if s.status == "modified":
                s.status = "valid"

        # Log audit action
        audit = AuditLogRecord(
            action="publish_knowledge_version",
            actor=approved_by,
            details_json=json.dumps({
                "version": version_number,
                "notes": notes,
                "published_at": now_dt.isoformat()
            })
        )
        db.add(audit)
        db.commit()

        # Invalidate in-memory knowledge base cache
        kb = get_knowledge_base()
        kb.load()

        return {
            "status": "success",
            "published_version": version_number,
            "published_at": now_dt.isoformat(),
            "approved_by": approved_by,
            "message": f"Knowledge Version {version_number} is now active in production. Stale retrieval caches invalidated."
        }

    @staticmethod
    def rollback_version(db: Session, target_version_number: int, reason: Optional[str] = None, actor: str = "support_manager") -> Dict[str, Any]:
        """Rolls back production knowledge to a previously valid version."""
        target = db.query(KnowledgeVersionRecord).filter_by(version_number=target_version_number).first()
        if not target:
            raise ValueError(f"Target knowledge version {target_version_number} not found.")

        # Archive current published versions
        for pv in db.query(KnowledgeVersionRecord).filter_by(status="published").all():
            pv.status = "archived"

        now_dt = datetime.now(timezone.utc)
        target.status = "published"
        target.published_at = now_dt

        audit = AuditLogRecord(
            action="rollback_knowledge_version",
            actor=actor,
            details_json=json.dumps({
                "target_version": target_version_number,
                "reason": reason or "Emergency rollback to verified version",
                "timestamp": now_dt.isoformat()
            })
        )
        db.add(audit)
        db.commit()

        # Invalidate cache
        kb = get_knowledge_base()
        kb.load()

        return {
            "status": "success",
            "active_version": target_version_number,
            "rollback_at": now_dt.isoformat(),
            "reason": reason,
            "message": f"Successfully rolled back to Knowledge Version {target_version_number}."
        }

    @staticmethod
    def add_source_url(db: Session, source_id: str, title: str, url: str, source_type: str = "official product page") -> Dict[str, Any]:
        """Registers a new official website URL into the Knowledge Base."""
        existing = db.query(KnowledgeSourceRecord).filter_by(source_id=source_id).first()
        if existing:
            raise ValueError(f"Source ID '{source_id}' is already registered.")

        # Crawl and hash immediately
        crawl_res = KnowledgeSyncEngine.crawl_source(url) if (url.startswith("http://") or url.startswith("https://")) else {"success": True, "content_hash": hashlib.sha256(title.encode()).hexdigest(), "normalized_text": title}

        rec = KnowledgeSourceRecord(
            source_id=source_id,
            title=title,
            url=url,
            source_type=source_type,
            content_hash=crawl_res.get("content_hash"),
            extracted_text=crawl_res.get("normalized_text", "")[:2000],
            status="valid" if crawl_res.get("success") else "failed",
            last_crawled_at=datetime.now(timezone.utc),
            last_error=crawl_res.get("error") if not crawl_res.get("success") else None
        )
        db.add(rec)
        db.commit()

        return {
            "status": "registered",
            "source_id": source_id,
            "title": title,
            "url": url,
            "content_hash": rec.content_hash,
            "crawl_status": rec.status
        }
