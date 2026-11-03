"""
WaterScience Support Platform — Persistent Database Layer
Provides durable storage for conversations, messages, jobs, tickets, and knowledge versions.
Supports SQLite (development/testing) and PostgreSQL (production).
"""

from datetime import datetime, timezone
import json
from typing import Generator, Optional, List, Dict, Any
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Index
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings

Base = declarative_base()

class CustomerRecord(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(128), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ConversationRecord(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(128), unique=True, index=True, nullable=False)
    customer_id = Column(String(128), index=True, nullable=False)
    channel = Column(String(64), default="waterscience_website")
    status = Column(String(64), default="active")  # active, auto_resolved, awaiting_customer_reply, escalated_to_human, closed
    resolution_level = Column(String(64), nullable=True)
    identified_product = Column(String(128), nullable=True)
    troubleshooting_attempts = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class MessageRecord(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String(128), unique=True, index=True, nullable=False)  # Enforces idempotency
    conversation_id = Column(String(128), index=True, nullable=False)
    customer_id = Column(String(128), index=True, nullable=False)
    channel = Column(String(64), default="waterscience_website")
    role = Column(String(32), default="customer")  # customer, assistant, system
    content = Column(Text, nullable=False)
    timestamp = Column(String(64), nullable=False)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ProcessingJobRecord(Base):
    __tablename__ = "processing_jobs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(128), unique=True, index=True, nullable=False)
    message_id = Column(String(128), index=True, nullable=False)
    conversation_id = Column(String(128), index=True, nullable=False)
    status = Column(String(32), default="queued")  # queued, processing, completed, failed, dead_letter
    attempts = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    resolution_level = Column(String(64), nullable=True)
    response_text = Column(Text, nullable=True)
    auto_dispatched = Column(Boolean, default=False)
    enqueued_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

class TicketRecord(Base):
    __tablename__ = "escalation_tickets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String(128), unique=True, index=True, nullable=False)
    conversation_id = Column(String(128), index=True, nullable=False)
    customer_id = Column(String(128), index=True, nullable=False)
    status = Column(String(32), default="open")  # open, assigned, in_progress, resolved, closed
    priority = Column(String(32), default="normal")  # urgent, high, normal
    category = Column(String(64), nullable=False)
    product = Column(String(128), nullable=True)
    escalation_reason = Column(Text, nullable=True)
    customer_message = Column(Text, nullable=True)
    ai_draft = Column(Text, nullable=True)
    recommended_action = Column(Text, nullable=True)
    assigned_to = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime, nullable=True)

class AuditLogRecord(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String(64), nullable=False)
    actor = Column(String(128), default="system")
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class KnowledgeSourceRecord(Base):
    __tablename__ = "knowledge_sources"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(String(64), unique=True, index=True, nullable=False)
    title = Column(String(256), nullable=False)
    url = Column(String(512), nullable=False)
    source_type = Column(String(64), default="official product page")
    content_hash = Column(String(64), nullable=True)  # SHA-256 of normalized text
    extracted_text = Column(Text, nullable=True)
    last_crawled_at = Column(DateTime, nullable=True)
    status = Column(String(32), default="valid")  # valid, modified, failed, pending
    last_error = Column(Text, nullable=True)

class KnowledgeVersionRecord(Base):
    __tablename__ = "knowledge_versions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    version_number = Column(Integer, unique=True, index=True, nullable=False)
    status = Column(String(32), default="draft")  # draft, published, archived
    change_summary = Column(Text, nullable=True)
    diff_json = Column(Text, nullable=True)
    created_by = Column(String(128), default="manager")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    published_at = Column(DateTime, nullable=True)


# Connection setup
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initializes tables and seeds initial source records if table is empty."""
    Base.metadata.create_all(bind=engine)
    
    # Seed initial knowledge sources from product_knowledge_base.json if empty
    with SessionLocal() as db:
        existing_sources = db.query(KnowledgeSourceRecord).count()
        if existing_sources == 0:
            from app.knowledge import get_knowledge_base
            kb = get_knowledge_base()
            kb.load()
            for sid, sdata in kb.sources.items():
                record = KnowledgeSourceRecord(
                    source_id=sid,
                    title=sdata.get("title", sid),
                    url=sdata.get("url", ""),
                    source_type=sdata.get("type", "official source"),
                    status="valid"
                )
                db.add(record)
            
            # Initial published version 1
            v1 = KnowledgeVersionRecord(
                version_number=1,
                status="published",
                change_summary="Initial verified baseline (14 official sources, 15 products)",
                published_at=datetime.now(timezone.utc)
            )
            db.add(v1)
            db.commit()

def get_db():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

