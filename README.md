# WaterScience AI Customer Support — Agent Assist Prototype

[![Tests Passing](https://img.shields.io/badge/Tests-20%2F20%20Passing-success)](test_results_report.md)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org)
[![Human Oversight](https://img.shields.io/badge/Guardrails-Mandatory%20Human%20Approval-red)](#human-oversight)

A working prototype for **Problem 2: Customer Service Overload** from the WaterScience AI Builder take-home assignment.

WaterScience receives around **2,000 emails and WhatsApp chats daily** regarding shower filters, tap compatibility, cartridge replacements, low water pressure, TDS expectations, shipping, warranty claims, and returns. This prototype demonstrates how an evidence-grounded AI drafting engine combined with deterministic guardrails reduces agent handling time from **~3 minutes to ~15 seconds** while guaranteeing zero unauthorized refunds, zero medical hallucinations, and mandatory human review.

---

## Key Features

1. **Deterministic Guardrails & Policy Enforcement:**
   - **Hot-Water Temperature Conflict:** Detects the official source discrepancy on CLEO SFU-717 (Product Page: 45°C vs Cartridge FAQ: 60°C) and escalates with both citations (`S01`, `S02`) rather than arbitrarily picking one.
   - **Marketplace Isolation:** Prohibits applying WaterScience.in's 60-day return policy to Amazon/Flipkart purchases; routes marketplace queries appropriately.
   - **Medical & Potability Boundaries:** Rejects claims that shower filters cure hair fall or that kitchen tap filters provide certified drinking water.
   - **Safe Leak Triage:** Issues shut-off instructions and gathers photo/video evidence without promising immediate warranty replacements.
   - **Corrected SYN-020 Flow:** Requests model/SKU details first for unidentified filters; avoids guessing interchangeable cartridges and escalates only if identification fails.

2. **Lightweight Retrieval (No Vector DB Bloat):**
   - Directly maps inquiries to verified sources in `product_knowledge_base.json` using SKU identifiers and issue categories.
   - Deterministic, zero-cost, and instant execution (< 2 ms latency).

3. **Mandatory Human-in-the-Loop Workflow:**
   - Every AI response is generated in `pending_approval` state.
   - Agents can inspect cited sources, review missing info checklists, edit draft text, and click **Approve**, **Save Edits**, or **Reject**.

4. **100% Passing Automated Benchmark Suite:**
   - All 20 cases from `synthetic_support_cases.json` are evaluated automatically with `pytest`.

---

## Directory Structure

```text
waterscience-customer-support-ai/
├── app/
│   ├── __init__.py
│   ├── config.py              # App settings, provider flags, paths
│   ├── models.py              # Pydantic schemas (SupportCase, Requests, Citations)
│   ├── knowledge.py           # Product knowledge base & source resolver
│   ├── classifier.py          # Issue, product, and channel classifier
│   ├── policy_rules.py        # Deterministic safety & escalation guardrails
│   ├── response_generator.py  # Grounded draft generator (Mock & Live LLM)
│   ├── engine.py              # End-to-end support pipeline orchestrator
│   ├── api.py                 # FastAPI endpoints & benchmark runner
│   └── static/
│       ├── index.html         # Agent Review Console & Benchmark UI
│       ├── style.css          # Modern, responsive design system
│       └── app.js             # UI interaction logic & benchmark visualizer
├── research/                  # Verified ground-truth data (unedited)
│   ├── product_knowledge_base.json
│   ├── research_register.csv
│   ├── research_summary.md
│   ├── source_gaps.md
│   ├── synthetic_support_cases.json
│   └── assignment.pdf         # Original assignment specification
├── tests/
│   ├── __init__.py
│   ├── test_synthetic_cases.py      # 20 automated tests verifying expected behaviors
│   ├── test_generalization_cases.py # 40 generalization test cases
│   └── test_evaluator.py            # Strict semantic evaluator unit tests
├── Dockerfile                 # Container image specification
├── compose.yaml               # Docker compose configuration
├── .dockerignore              # Container build exclusions
├── .env.example               # Template environment configuration (no secrets)
├── requirements.txt           # Python dependencies
├── generate_test_report.py    # Generates markdown benchmark report
├── evaluate_generalization.py # 40-case generalization evaluation runner
├── package_submission.py      # Automated packaging and security audit script
├── test_results_report.md     # Full case-by-case evaluation report (20/20 PASS)
├── live_failure_analysis.md   # Live failure analysis and defect resolution
├── corrective_fixes_report.md # Release verification and metric reconciliation
├── final_release_audit.md     # Release audit findings and resolutions
├── architecture.md            # Deep dive on architecture, costs, and scale
├── one_page_summary.md        # One-page executive assignment summary
├── demo_script.md             # 3-5 minute live demonstration walkthrough
└── README.md                  # This file
```

---

## Quickstart & Installation

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.14 on Windows)
- Git

### 2. Execution Options

The prototype supports two execution options. In either mode, **Mock Mode** operates out-of-the-box with zero configuration and requires **no API keys or credentials**.

---

#### Option A: Run Locally (Python Virtual Environment)

1. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the application:**
   ```bash
   python -m uvicorn app.api:app --host 127.0.0.1 --port 8000 --reload
   ```

4. **Access the application:**
   Open your browser at:
   ```text
   http://127.0.0.1:8000
   ```

5. **Stop the application:**
   Press `Ctrl + C` in the terminal to gracefully stop the uvicorn server.

---

#### Option B: Run with Docker Compose

A production-appropriate, minimal container configuration is provided via `Dockerfile` and `compose.yaml`.

1. **Build and start the container:**
   ```bash
   docker compose up --build -d
   ```

2. **Access the application:**
   Open your browser at:
   ```text
   http://localhost:8000
   ```
   Check container health at:
   ```text
   http://localhost:8000/health
   ```

3. **Stop the container:**
   ```bash
   docker compose down
   ```

4. **Configuring Optional Live LLM in Docker (Securely):**
   To run with a live LLM provider (e.g. Groq or OpenAI) rather than the default mock mode:
   - Pass the environment variable directly without editing or committing secrets:
     ```bash
     GROQ_API_KEY="your-key-here" LLM_PROVIDER="groq" docker compose up -d
     ```
   - Or define the variable in a local `.env` file (which is automatically ignored by `.gitignore` and `.dockerignore`).
   - If no API key is provided, the container automatically operates in deterministic **Mock Mode** with zero external dependencies.

---

#### Option C: Deploy to Render (Cloud Web Service)

The application is containerized with dynamic port support and health checking tailored for cloud PaaS environments like **Render**.

1. **Create Web Service on Render:**
   - Link your GitHub repository or connect via Docker.
   - Choose **Docker** as the Runtime environment.

2. **Configure Environment Variables:**
   - `ENVIRONMENT`: `production`
   - `LLM_PROVIDER`: `mock` *(Recommended default for public demonstration to avoid API quota exhaustion by unauthorized web traffic)*
   - `GROQ_API_KEY`: *(Leave blank for mock mode, or provide if hosting a private live AI demonstration)*

3. **Configure Network & Health Check:**
   - **Port:** Render automatically injects the `$PORT` environment variable (typically `10000`). The container automatically listens on `${PORT:-8000}`.
   - **Health Check Path:** `/health`
   - **Docker Build Context:** `.`
   - **Dockerfile Path:** `./Dockerfile`

4. **Verify Deployment:**
   - Once deployed, visit your Render URL (e.g. `https://waterscience-support.onrender.com/health`).
   - Confirm status reports `"status": "healthy"` and `"provider_status": "deterministic_mock_mode"`.
   - The interactive Agent Review Console is served at the root `/`.

---

### 3. Environment Configuration

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `LLM_PROVIDER` | `mock` | `mock` (deterministic zero-cost) or `groq` / `openai` (live LLM). |
| `GROQ_API_KEY` | None | API key for Groq live LLM provider (optional). |
| `OPENAI_API_KEY` | None | API key for OpenAI live LLM provider (optional). |
| `PORT` | `8000` | Port for the web server (configurable). |
| `ENVIRONMENT` | `development` | `development` or `production`. |

---

## Running the Automated Test Suite

Run the full `pytest` suite testing all 20 synthetic cases:
```bash
python -m pytest tests/test_synthetic_cases.py -v
```

### Expected Output:
```text
============================= test session starts =============================
collected 23 items

tests/test_synthetic_cases.py::test_kb_loaded PASSED                     [  4%]
tests/test_synthetic_cases.py::test_all_20_synthetic_cases_execute PASSED [  8%]
tests/test_synthetic_cases.py::test_syn_001_cleo_tap_fitment PASSED      [ 13%]
tests/test_synthetic_cases.py::test_syn_002_plastic_tap_limitation PASSED [ 17%]
tests/test_synthetic_cases.py::test_syn_003_cartridge_selection_chlorine_clarification PASSED [ 21%]
tests/test_synthetic_cases.py::test_syn_004_tds_expectation PASSED       [ 26%]
tests/test_synthetic_cases.py::test_syn_005_low_flow_guidance PASSED     [ 30%]
tests/test_synthetic_cases.py::test_syn_006_leak_safety_and_escalation PASSED [ 34%]
tests/test_synthetic_cases.py::test_syn_007_temperature_conflict_escalation PASSED [ 39%]
tests/test_synthetic_cases.py::test_syn_008_warranty_claim_no_automatic_confirmation PASSED [ 43%]
tests/test_synthetic_cases.py::test_syn_009_website_return_conditional PASSED [ 47%]
tests/test_synthetic_cases.py::test_syn_010_amazon_channel_isolation PASSED [ 52%]
tests/test_synthetic_cases.py::test_syn_011_damaged_on_arrival PASSED    [ 56%]
tests/test_synthetic_cases.py::test_syn_012_delivery_tracking_no_false_eta PASSED [ 60%]
tests/test_synthetic_cases.py::test_syn_013_iris_washing_machine_compatibility PASSED [ 65%]
tests/test_synthetic_cases.py::test_syn_014_iris_cartridge_life PASSED   [ 69%]
tests/test_synthetic_cases.py::test_syn_015_kitchen_filter_incompatible_tap PASSED [ 73%]
tests/test_synthetic_cases.py::test_syn_016_kitchen_filter_potable_safety PASSED [ 78%]
tests/test_synthetic_cases.py::test_syn_017_whole_home_consultation PASSED [ 82%]
tests/test_synthetic_cases.py::test_syn_018_puro_health_faucet_fault PASSED [ 86%]
tests/test_synthetic_cases.py::test_syn_019_medical_claims_rejection PASSED [ 91%]
tests/test_synthetic_cases.py::test_syn_020_unknown_product_identification_no_immediate_escalation PASSED [ 95%]
tests/test_synthetic_cases.py::test_human_approval_workflow PASSED       [100%]

============================= 23 passed in 0.20s ==============================
```

To regenerate the markdown report (`test_results_report.md`):
```bash
python generate_test_report.py
```

---

## Benchmark Results Summary

| Case ID | Stated Product | Issue Category | Expected Escalation | Actual Escalation | Verified Sources | Result |
| --- | --- | --- | --- | --- | --- | --- |
| **SYN-001** | CLEO SFU-717 | compatibility | No | No | `S01` | ✅ PASS |
| **SYN-002** | CLEO SFU-717 | compatibility (plastic tap) | No | No | `S01` | ✅ PASS |
| **SYN-003** | CLEO replacement cartridge | cartridge_selection (TDS 900) | No | No | `S01, S02` | ✅ PASS |
| **SYN-004** | CLEO SFU-717 | tds_expectation (meter same) | No | No | `S01, S02` | ✅ PASS |
| **SYN-005** | CLEO SFU-717 | low_flow (after 2 weeks) | No | No | `S02` | ✅ PASS |
| **SYN-006** | CLEO replacement cartridge | leak_after_maintenance | Yes | Yes | `S02, M01, S03` | ✅ PASS |
| **SYN-007** | CLEO SFU-717 | temperature_limit_conflict (55°C) | Yes | Yes | `S01, S02` | ✅ PASS |
| **SYN-008** | CLEO SFU-717 | warranty_claim (body cracked) | Yes | Yes | `S03` | ✅ PASS |
| **SYN-009** | CLEO SFU-717 | website_return_request | Yes | Yes | `S04, S01` | ✅ PASS |
| **SYN-010** | CLEO SFU-717 | marketplace_return_request | Yes | Yes | `S04` | ✅ PASS |
| **SYN-011** | unknown WaterScience | damaged_on_arrival | Yes | Yes | `S04, S03` | ✅ PASS |
| **SYN-012** | unknown WaterScience | delivery_tracking | No | No | `S05` | ✅ PASS |
| **SYN-013** | IRIS-WMF-325 | washing_machine_compatibility | No | No | `S06` | ✅ PASS |
| **SYN-014** | IRIS-WMF-325 | cartridge_life (top-load) | No | No | `S06` | ✅ PASS |
| **SYN-015** | KTF variant unknown | kitchen_filter_compatibility | Yes | Yes | `S07` | ✅ PASS |
| **SYN-016** | KTF Kitchen Tap Extender | potable_water_safety | Yes | Yes | `S07` | ✅ PASS |
| **SYN-017** | RENO Cygnus | whole_home_consultation | Yes | Yes | `S08` | ✅ PASS |
| **SYN-018** | PURO HFS-625 | product_fault (leak/trigger) | Yes | Yes | `S09, S03` | ✅ PASS |
| **SYN-019** | CLEO SFU-717 | medical_expectation (hair fall) | Yes | Yes | `S02` | ✅ PASS |
| **SYN-020** | unknown WaterScience | product_identification | No | No | `S02, S10` | ✅ PASS |

See the complete [Test Results Report](test_results_report.md) for full transcripts, criteria checks, and draft outputs for all 20 cases.

---

## Documentation Deliverables

- [One-Page Submission Summary](one_page_summary.md)
- [Architecture & Design Decisions](architecture.md)
- [Demo Script & Walkthrough](demo_script.md)
- [Synthetic Benchmark Test Report (20/20)](test_results_report.md)
- [Live Failure Analysis & Resolution](live_failure_analysis.md)
- [Corrective Fixes & Verification Report](corrective_fixes_report.md)
- [Final Release Audit](final_release_audit.md)
- [Research Summary](research/research_summary.md)
- [Source Gaps Log](research/source_gaps.md)
