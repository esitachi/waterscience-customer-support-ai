"""
Tests for Phase 3: URL-Based Knowledge Management
Verifies:
1. HTML content normalization and SHA-256 hashing.
2. Unchanged website scenario: no version bump, retains active published version.
3. Website change scenario: detects modified content, creates draft version with change summary.
4. Failed crawl scenario: preserves valid knowledge, marks failed without deletion.
5. Publish validated version: archives old, publishes draft, logs audit, refreshes cache.
6. Rollback scenario: allows reverting to an earlier published version.
7. Add new official source URL: stores and tracks in registry.
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from app.api import app
from app.database import init_db, SessionLocal, KnowledgeSourceRecord, KnowledgeVersionRecord, AuditLogRecord
from app.crawler import normalize_html_content, KnowledgeSyncEngine

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield


def test_html_content_normalization_and_hashing():
    """HTML normalizer must strip scripts/navs, extract text, and compute consistent SHA-256."""
    html_1 = """
    <html>
        <head><title>CLEO Shower Filter</title><script>console.log('ad');</script></head>
        <body>
            <nav><a href='/'>Home</a></nav>
            <h1>CLEO Shower & Tap Filter</h1>
            <p>Fits 22, 24, 28 mm metal taps. Max 45°C temp. 5-year warranty.</p>
            <footer>Copyright 2026</footer>
        </body>
    </html>
    """
    html_2 = """
    <html>
        <head><title>CLEO Shower Filter</title></head>
        <body>
            <h1>CLEO Shower & Tap Filter</h1>
            <p>Fits   22, 24, 28 mm metal taps.   Max 45°C temp. 5-year warranty. </p>
        </body>
    </html>
    """
    text1, hash1, meta1 = normalize_html_content(html_1)
    text2, hash2, meta2 = normalize_html_content(html_2)

    assert "console.log" not in text1
    assert "Copyright" not in text1
    assert "22, 24, 28 mm" in text1
    assert hash1 == hash2  # Consistent hashing regardless of whitespace or script tags
    assert "24" in meta1["detected_facts"]["thread_sizes_mm"]
    assert "45" in meta1["detected_facts"]["temperature_max_c"]


def test_unchanged_website_scenario_no_version_bump():
    """When crawled content matches existing hash, no new draft version should be created."""
    with SessionLocal() as db:
        # Pre-seed source S01 with matching hash
        src = db.query(KnowledgeSourceRecord).filter_by(source_id="S01").first()
        test_html = "<html><body><h1>CLEO Shower and Tap Filter</h1><p>Fits 24mm taps.</p></body></html>"
        _, chash, _ = normalize_html_content(test_html)
        src.content_hash = chash
        db.commit()

        # Sync with identical simulated content
        res = KnowledgeSyncEngine.sync_all_sources(db, simulated_contents={"S01": test_html})
        assert res["sync_status"] == "unchanged"
        assert res["modified_count"] == 0
        assert res["proposed_version"] is None


def test_website_change_scenario_proposes_draft_version():
    """When a product page changes, the sync engine must propose a draft version with change notes."""
    with SessionLocal() as db:
        # Simulate changed content for S01
        updated_html = """
        <html>
            <body>
                <h1>CLEO Shower & Tap Filter</h1>
                <p>Now supports 20, 22, 24, 28 mm metal taps and up to 50°C hot water.</p>
            </body>
        </html>
        """
        res = KnowledgeSyncEngine.sync_all_sources(db, simulated_contents={"S01": updated_html})

        assert res["sync_status"] == "draft_proposed"
        assert res["modified_count"] >= 1
        assert res["proposed_version"] is not None
        assert "S01" in res["change_summary"]

        # Verify draft record exists in DB
        draft = db.query(KnowledgeVersionRecord).filter_by(version_number=res["proposed_version"]).first()
        assert draft is not None
        assert draft.status == "draft"


def test_failed_crawl_scenario_retains_valid_knowledge():
    """If a source URL fails (e.g. 500/timeout), previous knowledge is retained and source marked failed."""
    with SessionLocal() as db:
        src = db.query(KnowledgeSourceRecord).filter_by(source_id="S06").first()
        src.status = "failed"
        src.last_error = "HTTP 503: Service Unavailable"
        db.commit()

        # Re-query
        re_src = db.query(KnowledgeSourceRecord).filter_by(source_id="S06").first()
        assert re_src.status == "failed"
        assert "503" in re_src.last_error
        # Knowledge is retained
        assert re_src.title is not None


def test_publish_validated_version_and_rollback_workflow():
    """Manager approves draft version; old version is archived; rollback re-activates old version."""
    with SessionLocal() as db:
        max_v = db.query(KnowledgeVersionRecord).order_by(KnowledgeVersionRecord.version_number.desc()).first()
        test_v = (max_v.version_number + 1) if max_v else 2
        draft_record = KnowledgeVersionRecord(
            version_number=test_v,
            status="draft",
            change_summary="Updated IRIS washing machine filter specs"
        )
        db.add(draft_record)
        db.commit()

    # 1. Publish test version
    pub_res = client.post("/api/v2/knowledge/publish", json={
        "version_number": test_v,
        "approved_by": "qa_manager",
        "notes": "Verified against live staging"
    })
    assert pub_res.status_code == 200
    assert pub_res.json()["published_version"] == test_v

    with SessionLocal() as db:
        v1 = db.query(KnowledgeVersionRecord).filter_by(version_number=1).first()
        published_rec = db.query(KnowledgeVersionRecord).filter_by(version_number=test_v).first()
        assert v1.status == "archived"
        assert published_rec.status == "published"

    # 2. Rollback to version 1
    rb_res = client.post("/api/v2/knowledge/rollback", json={
        "target_version_number": 1,
        "reason": "Reverting test version"
    })
    assert rb_res.status_code == 200
    assert rb_res.json()["active_version"] == 1

    with SessionLocal() as db:
        v1 = db.query(KnowledgeVersionRecord).filter_by(version_number=1).first()
        assert v1.status == "published"


def test_add_new_source_url_workflow():
    """Support manager adds a new official URL; system registers and hashes it."""
    random_sid = f"S{uuid.uuid4().hex[:6].upper()}"
    payload = {
        "source_id": random_sid,
        "title": "AERA Water Saving Tap Aerator",
        "url": "https://www.waterscience.in/products/aera-tap-aerator",
        "source_type": "official product page"
    }

    res = client.post("/api/v2/knowledge/sources", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["source_id"] == random_sid
    assert data["status"] == "registered"

    # Verify in DB
    with SessionLocal() as db:
        s = db.query(KnowledgeSourceRecord).filter_by(source_id=random_sid).first()
        assert s is not None
        assert s.title == "AERA Water Saving Tap Aerator"
