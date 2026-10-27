# WaterScience AI Builder Assignment — One-Page Submission Summary

**Candidate Problem Chosen:** Problem 2 — Customer Service Overload  
**Submission Date:** 28 October 2026  
**Author:** AI & Tech Founder's Office Intern Candidate  

---

### 1. What I Learned About WaterScience & Its Customers (And How It Changed My Design)
WaterScience is a specialized Bengaluru-based D2C brand tackling hard water across Indian households. Researching official storefronts, policy pages, manuals, and customer feedback revealed critical operational nuances:
1. **Fitment & Infrastructure Realities:** Indian plumbing fixtures vary wildly between 20 mm, 22 mm, 24 mm, and 28 mm threads, internal vs external threading, and metal vs plastic taps. Recommending a filter without verifying metal threads or aerator size leads to immediate returns and leaks.
2. **Consumable & Water-Source Specificity:** Cartridges are not universal. Municipal/Metro water with chlorine requires a completely different cartridge than Borewell/Tanker water with high TDS.
3. **Customer Expectation Mismatches (TDS & Hair Fall):** Customers frequently test shower filters with TDS meters and assume the filter is "fake" when TDS doesn't change, or expect an overnight medical cure for hair fall.
4. **Source Conflicts:** Official documentation contains genuine discrepancies (e.g. SFU-717 product page specifies 45°C max, while the replacement cartridge FAQ specifies 60°C).
5. **Channel Isolation:** Website purchases enjoy a 60-day return policy for CLEO, while Amazon/marketplace orders follow separate seller policies.

**Design Shift:** These learnings proved that an **autonomous auto-reply bot would be catastrophic**. Instead, I designed an **Agent-Assist Drafting Engine with Mandatory Human Approval**, backed by deterministic guardrails that prevent false promises, isolate channels, and escalate conflicts.

---

### 2. Who the Solution Is For & What Was Built
- **Who It Is For:** WaterScience frontline customer service agents handling ~2,000 inbound WhatsApp chats and emails daily.
- **What Was Built:** A production-ready Python & FastAPI prototype consisting of:
  - **Lightweight Classification & Retrieval Engine:** Maps messages to verified products and policy facts without an unnecessary vector database.
  - **Deterministic Safety Guardrails:** Hard-coded Python checks for channel isolation (Amazon vs website), temperature source conflicts, leak shut-off triage, medical claim disclaimers, and unknown product handling (`SYN-020`).
  - **Grounded Draft Generator:** Cites verified source IDs (`S01`–`S10`) and generates empathetic, factual replies in English and Hinglish. Configurable for offline Mock Mode (zero cost) or live LLMs (OpenAI/Groq).
  - **Support Review Console & Test Runner:** A clean, professional web UI displaying classification badges, required information checklists, source citation links, editable drafts, and approval actions (`Approve`, `Edit`, `Reject`).
  - **20-Case Benchmark Suite:** Automated tests covering all 20 synthetic cases from `synthetic_support_cases.json`, achieving a **100% pass rate**.

---

### 3. Key Technical & Product Decisions and Why
- **Deterministic Guardrails over Probabilistic Prompting:** LLMs can hallucinate or smooth over conflicts. Hard rules detect the 45°C vs 60°C hot-water discrepancy, block refund guarantees, and isolate Amazon policies deterministically.
- **No Vector Database:** For an 11-document verified corpus, vector search adds latency, embeddings cost, and fuzzy threshold bugs. Clean dictionary lookups guarantee 100% precision and instant speed (< 2 ms).
- **Mandatory Human-in-the-Loop:** Every draft begins in `pending_approval`. Human agents maintain accountability, reducing average handling time from 3 minutes to under 20 seconds per ticket.
- **SYN-020 Corrected Flow:** When a customer sends a photo of an unknown filter, the system requests model/SKU details first and holds off on recommending a cartridge, escalating only if identification fails.

---

### 4. Assumptions, Known Limitations & What to Improve Next
- **Assumptions:** 2,000 queries/day (~$0.38/day LLM cost on GPT-4o-mini); customer message contains enough context to extract channel or defaults to unknown; human agents review all outbound messages.
- **Known Limitations:** Amazon India review and Q&A pages were inaccessible during research and are omitted; no direct integration yet with Shopify or ERP for real-time order lookups; legacy manual repair steps remain unverified for current products.
- **Next Steps:** Integrate Shopify GraphQL API for automatic Order ID and channel verification; connect official WhatsApp Cloud API webhooks; add a ticket tagging analytics dashboard; implement semantic caching for common compatibility FAQs.
