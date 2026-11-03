# Architecture Audit & Scalability Gap Analysis
**Project:** WaterScience AI Customer Support Platform Upgrade  
**Branch:** `feature/autonomous-support-platform`  
**Date:** November 2026  
**Scope:** Evolution from Problem 2 Agent-Assist Prototype to Autonomous Support Platform (Handling 2,000+ messages)

---

## 1. Executive Summary

This audit evaluates the current WaterScience Customer Support AI prototype (Problem 2) against the requirements of an **Autonomous, Scalable Customer Support Platform**. 

The current system is a well-structured, evidence-grounded agent-assist tool featuring deterministic policy guardrails, live Groq LLM generation, an official source registry (14 sources, 15 products), and a live browser console. However, it was architected as an interactive desktop review console requiring mandatory human approval for every draft. To handle 2,000+ concurrent messages with minimal human intervention, self-service knowledge updates, and carrier-grade reliability, the architecture must transition from **synchronous in-memory agent-assist** to an **asynchronous, persistent, multi-tiered autonomous resolution platform**.

---

## 2. Existing System Inspection

### 2.1 Backend API & FastAPI Application (`app/api.py`)
* **Current State:**
  * Clean FastAPI application serving static assets (`/static`), health status (`/health`), knowledge base registry (`/api/knowledge-base`), query processing (`/api/query`), case retrieval (`/api/cases`, `/api/cases/{case_id}`), approval actions (`/api/cases/{case_id}/approve`), and synthetic benchmarking (`/api/synthetic-cases`, `/api/run-synthetic-tests`).
* **Strengths:** Clear separation of concerns, Pydantic request/response models, CORS enabled, no-cache headers for static files.
* **Limitations:**
  * Synchronous query processing: `/api/query` blocks while executing classification, policy evaluation, and external LLM API calls.
  * No standardized message-ingestion endpoint supporting channel, `customer_id`, `conversation_id`, and `message_id`.
  * Lacks batch processing, rate-limiting, and webhook idempotency.

### 2.2 AI Processing & LLM Integration (`app/engine.py`, `app/response_generator.py`)
* **Current State:**
  * `SupportEngine.process_query()` orchestrates the 6-step pipeline: Channel Detection → Classification → Knowledge Retrieval → Policy Rules Evaluation → Grounded Generation → `SupportCase` formation.
  * `ResponseGenerator` supports dual modes: Live Groq (`llama-3.3-70b-versatile` or OpenAI) with automatic fallback to deterministic grounded templates.
* **Strengths:** 
  * Strict grounding: passes verified product facts and negative rules into prompt context.
  * Fault-tolerant fallback prevents total outage if LLM provider fails.
* **Limitations:**
  * Single-turn focus: does not maintain persistent multi-turn conversation threads or stateful troubleshooting histories.
  * Synchronous blocking HTTP calls to Groq API (1-2s latency per request) cannot support 2,000+ concurrent incoming messages without a queue.

### 2.3 Policy Rules Engine & Guardrails (`app/policy_rules.py`)
* **Current State:**
  * Deterministic rule evaluation covering safety leaks (R04), compatibility (R02), warranty/returns (R03), medical disclaimers (R05), source conflicts (R06), negative cartridge rules (R07 PURO HFS-625 NeverBlock, R08 RENO Cygnus softener salt), and unverified mapping restraints (R09 KTF Wide).
* **Strengths:**
  * Flawless deterministic enforcement: overrides LLM output on safety-critical domains.
  * 100% recall on hazardous cases.
* **Limitations:**
  * Policy engine currently marks all safe cases as `READY_FOR_APPROVAL` instead of distinguishing between **Level 1 (Autonomous Resolution)**, **Level 2 (Conditional Troubleshooting)**, and **Level 3 (Mandatory Human Escalation)**.

### 2.4 Knowledge Base & Data Storage (`app/knowledge.py`, `research/product_knowledge_base.json`)
* **Current State:**
  * 14 verified sources (`S01`–`S14`, `M01`), 15 product records, routing rules, guardrails, and policy facts stored in static JSON on disk.
  * In-memory singleton `KnowledgeBase` class loads JSON with `.load()` cache.
* **Strengths:**
  * High factual accuracy with URLs, access dates, and model-specific compatibility matrices.
* **Limitations:**
  * Static file storage: updating knowledge requires modifying JSON or Python code.
  * No automated web crawler to sync with official URLs, detect changed HTML/text, compare hashes, or version knowledge updates.
  * No Redis caching layer or staging/rollback mechanism for non-technical managers.

### 2.5 Storage & Persistence (`app/engine.py`)
* **Current State:**
  * In-memory dictionary: `self.cases: Dict[str, SupportCase] = {}`.
* **Critical Flaw:**
  * All case histories, agent edits, approval actions, and customer queries are wiped whenever the server process restarts.
  * Cannot support horizontal worker scaling across multiple processes or containers.

### 2.6 Frontend & Review Console (`app/static/`)
* **Current State:**
  * Modern single-page app with Live Query Console, Synthetic Test Benchmark (20 Cases), and Evidence & Knowledge Base tabs.
* **Strengths:**
  * Clean UI, live AI badge, sub-navigation for Sources, Products, and Negative Rules, grounded citation cards.
* **Limitations:**
  * Built exclusively for 1-by-1 manual agent approval.
  * No Support Operations Dashboard (no visibility into incoming queue depth, resolution rate, worker status, or escalation inbox).
  * No URL-based Knowledge Base Management interface.
  * No Scale & Performance Center to simulate and benchmark 2,000+ messages.

### 2.7 Test Harnesses & Synthetic Benchmark
* **Current State:**
  * 39 automated tests across `test_evaluator.py`, `test_synthetic_cases.py`, and `test_new_cartridge_knowledge.py`.
  * 40 generalization cases in `test_generalization_cases.py`.
  * 20 ground-truth cases in `synthetic_support_cases.json`.
* **Strengths:** 100% test pass rate on core logic, high coverage of Hinglish idioms and edge cases.
* **Limitations:** No load tests, queue concurrency tests, crawler tests, or worker failure recovery tests.

---

## 3. Component Reusability & Modification Matrix

| Component | Current File(s) | Assessment | Required Action |
| :--- | :--- | :--- | :--- |
| **Issue Classifier** | `app/classifier.py` | **High Reuse** | Reuse core intent extraction and Hinglish matching. Extend to support multi-turn intent tracking and conversation state. |
| **Policy Engine** | `app/policy_rules.py` | **High Reuse** | Reuse all safety, leak, and negative rules. Extend to emit 3-Tier Resolution levels (`AUTONOMOUS_RESOLVE`, `CLARIFICATION_TROUBLESHOOT`, `HUMAN_ESCALATE`). |
| **Grounded Generator** | `app/response_generator.py` | **High Reuse** | Reuse prompt grounding and mock fallback. Add asynchronous execution and multi-turn context formatting. |
| **Knowledge Base** | `app/knowledge.py`, `product_knowledge_base.json` | **Reuse & Extend** | Preserve all 14 sources and 15 products as initial seed data. Add database persistence, URL crawler, content hashing, diff engine, and versioning. |
| **Support Engine** | `app/engine.py` | **Major Modification** | Replace in-memory dictionary with persistent database repository while maintaining backward compatibility for the Live Console. |
| **Data Models** | `app/models.py` | **Extend** | Add models for `NormalizedMessage`, `Conversation`, `Ticket`, `ProcessingJob`, `ResolutionLevel`, `KnowledgeSource`, and `KnowledgeVersion`. |
| **Database Storage** | *None (In-memory)* | **Missing** | Implement SQLAlchemy / PostgreSQL durable persistence with migrations and graceful local fallback. |
| **Message Queue / Workers** | *None (Synchronous)* | **Missing** | Implement asynchronous background queue worker architecture (Redis/Celery or high-throughput async worker pool) with retries, dead-letter queue, and idempotency. |
| **URL Knowledge Manager** | *None* | **Missing** | Implement background crawler, HTML content extractor, hash comparison, diff engine, and non-technical publishing workflow. |
| **Operations Dashboard** | *None* | **Missing** | Add Manager Overview metrics (resolution rate, active workers, queue depth) and Escalation Inbox. |
| **Scale & Performance Center**| *None* | **Missing** | Add realistic traffic simulator (100 to 5,000 messages) measuring real throughput, latency (p95/p99), and queue bottlenecks. |

---

## 4. Scalability Bottlenecks & Critical Gaps

1. **Synchronous Request-Response Coupling:**
   A synchronous API endpoint (`/api/query`) calling an external LLM API takes 1,200ms–2,500ms per request. At 2,000 incoming messages, synchronous processing would either exhaust worker threads, encounter gateway timeouts (HTTP 504), or crash uvicorn. An asynchronous message-ingestion queue is mandatory.
2. **Volatile In-Memory Storage:**
   Storing support cases in `self.cases: Dict[str, SupportCase]` means data loss on server restarts and zero ability to share state across multiple worker processes.
3. **Mandatory Approval Bottleneck:**
   Requiring human approval for every trivial query (e.g. *"Will CLEO fit my 24mm tap?"*) creates a human bottleneck that defeats the purpose of an automated platform. Level 1 safe queries must resolve autonomously.
4. **Static Knowledge Management:**
   Currently, any product specification or policy change requires a developer to edit `research/product_knowledge_base.json`. Business managers require a self-service URL crawler that checks website pages, shows visual diffs, and publishes versioned updates.
5. **Lack of Operational Visibility:**
   There is currently no way to monitor queue depth, active worker concurrency, failure rates, or system health in real time.

---

## 5. Architectural Blueprint for the Upgrade

```text
                                  +---------------------------------------+
                                  | Inbound Messages (Web, WhatsApp, API) |
                                  +---------------------------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  | 1. Fast Ingestion API (/api/v2/messages)|
                                  |    - Idempotency check                |
                                  |    - Store in PostgreSQL/DB           |
                                  |    - Enqueue job in Queue (Redis)     |
                                  |    - Fast ACK (<50ms)                 |
                                  +---------------------------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  | 2. Asynchronous Background Workers    |
                                  |    - Configurable concurrency (4-16)  |
                                  |    - Rate-limit & exponential retry   |
                                  |    - Dead-letter queue (DLQ)          |
                                  +---------------------------------------+
                                                      |
                         +----------------------------+----------------------------+
                         |                                                         |
                         v                                                         v
         +-------------------------------+                         +-------------------------------+
         | 3. Autonomous AI Engine       |                         | 4. Knowledge Management Subsys|
         |    - Context & History Loader |                         |    - URL Web Crawler (BS4)    |
         |    - IssueClassifier (Reused) |                         |    - Content Normalizer & Hash|
         |    - Knowledge Retrieval (DB) |                         |    - Staging, Diff & Review   |
         |    - PolicyRules (3-Tier)     |                         |    - Versioning & Rollback    |
         |    - Grounded LLM Generator   |                         |    - Redis Cache Invalidation |
         +-------------------------------+                         +-------------------------------+
                         |
         +---------------+---------------+
         |                               |
         v                               v                               v
+------------------+           +--------------------+          +---------------------+
| Level 1: Auto-   |           | Level 2: Multi-Turn|          | Level 3: Mandatory  |
| Resolved (Safe)  |           | Troubleshooting    |          | Human Escalation    |
| - Outbound ACK   |           | - Clarification Qs |          | - Escalation Inbox  |
| - Log Resolution |           | - Loop Prevention  |          | - Manager Action    |
+------------------+           +--------------------+          +---------------------+
```

---

## 6. Implementation Principles
1. **Preserve Legacy Prototypes:** The existing Live Query Console (`/api/query`), Synthetic Benchmark (`/api/synthetic-cases`), and 14 sources / 15 products must remain 100% functional and backward-compatible.
2. **Deterministic Governance:** LLMs are never permitted to authorize refunds, bypass warranty invoices, or guess plumbing fits.
3. **No Fake Simulation:** The Scale & Performance Center will execute actual ingestion, queueing, classification, policy checking, and response generation for all test volumes.
4. **Dual Database/Queue Compatibility:** Support standard PostgreSQL + Redis in production/Docker, with zero-dependency SQLite + Async Queue fallback for local development environments so that tests run seamlessly anywhere.

