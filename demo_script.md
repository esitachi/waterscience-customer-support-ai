# WaterScience AI Customer Support — Demonstration Script

This demo script walks an interviewer or evaluator through the working prototype in 3–5 minutes, demonstrating how the system solves Problem 2 (Customer Service Overload) while preserving factual accuracy, human oversight, and safety.

---

## 1. Environment Setup & Launch (30 seconds)

1. Open a terminal in the project directory:
   ```bash
   cd c:\Users\Dell\Desktop\waterscience-customer-support-ai
   ```
2. Start the FastAPI server (runs in mock mode by default, requiring no API keys):
   ```bash
   python -m uvicorn app.api:app --host 127.0.0.1 --port 8000
   ```
3. Open your browser to:
   ```text
   http://127.0.0.1:8000
   ```

---

## 2. Demonstration Flow

### Scene 1: Automated Test Benchmark (100% Pass Rate)
- **Action:** Click on the **"🧪 Synthetic Test Benchmark (20 Cases)"** tab.
- **Action:** Click the blue button **"▶ Run All 20 Cases"**.
- **Talking Points:**
  - *"Before showing individual queries, let's look at the benchmark suite. We evaluate our pipeline against all 20 synthetic cases from `synthetic_support_cases.json`."*
  - *"Notice the summary metrics: 20 total cases, 20 passed (100%), 0 failed, and 11 safely escalated."*
  - *"Click 'Inspect' on `SYN-007` to see how the system detects the official temperature conflict between S01 (45°C) and S02 (60°C) and generates evaluation notes explaining the pass criteria."*

### Scene 2: Live Console — Routine Inquiries & Hinglish (SYN-001 & SYN-002)
- **Action:** Switch to the **"💬 Live Query Console"** tab.
- **Action:** Select **`SYN-001`** from the preset dropdown (*"Hi, will CLEO SFU-717 fit my 24 mm metal kitchen tap?"*).
- **Action:** Click **"⚡ Process with AI Pipeline"**.
- **Talking Points:**
  - *"The system classifies the issue as `compatibility`, identifies `CLEO SFU-717`, and cites official source `S01`."*
  - *"Notice the draft: it confirms 24 mm is listed for metal-threaded taps, explicitly warns that plastic taps do not fit, does not guarantee fitment from diameter alone, and requests an aerator photo."*
  - *"Now load `SYN-002` (*'Mera tap plastic hai, CLEO lag jayega kya?'*). The pipeline responds naturally in Hinglish, clearly explaining that plastic taps are unsupported, refusing to invent an unverified adapter."*

### Scene 3: Handling TDS Misconceptions (SYN-004)
- **Action:** Select **`SYN-004`** (*"Filter laga diya but TDS meter same hai. Product fake hai kya?"*).
- **Action:** Click **"⚡ Process with AI Pipeline"**.
- **Talking Points:**
  - *"TDS confusion is one of the most common customer complaints in water filtration in India."*
  - *"The assistant remains calm and non-defensive. Grounded in `S01` and `S02`, it explains that shower filters condition hard water and filter chlorine, but do not reduce TDS like an RO system. Unchanged TDS is documented as expected, debunking the 'fake product' suspicion without making medical claims."*

### Scene 4: Safety & Source Conflict Escalation (SYN-006 & SYN-007)
- **Action:** Select **`SYN-007`** (*"Can I run 55 degree hot water through SFU-717 daily?"*).
- **Action:** Click **"⚡ Process with AI Pipeline"**.
- **Talking Points:**
  - *"Here is where generic LLMs fail: they either invent a safe temperature or arbitrarily choose one source. Our deterministic policy engine catches the official conflict: the SFU-717 product page says 45°C, while the cartridge FAQ says 60°C."*
  - *"The system immediately turns the status banner red ('Escalated to Human Support'), cites both `S01` and `S02`, and instructs the agent that engineering confirmation is required before answering."*

### Scene 5: Channel Isolation (Amazon vs Website — SYN-009 & SYN-010)
- **Action:** Select **`SYN-010`** (*"Amazon se filter aaya broken. WaterScience 60-day refund do."*).
- **Action:** Click **"⚡ Process with AI Pipeline"**.
- **Talking Points:**
  - *"A major risk in D2C is policy leakage. WaterScience has a 60-day return policy on its website, but Amazon orders follow Amazon's terms."*
  - *"The system detects Amazon as the purchase channel and strictly isolates the policies. It refuses to apply the website's 60-day refund, guides the customer to their Amazon app orders, and requests marketplace order proof."*

### Scene 6: Unknown Product & Conditional Escalation (SYN-020)
- **Action:** Select **`SYN-020`** (*"Need replacement filter urgently. Old one photo bhej diya, model yaad nahi."*).
- **Action:** Click **"⚡ Process with AI Pipeline"**.
- **Talking Points:**
  - *"In accordance with the prompt specification, the assistant does NOT recommend a generic cartridge (which might not fit), nor does it escalate immediately."*
  - *"Instead, it flags `review_status: needs_clarification` and presents a checklist requesting the SKU label, connector photos, or order history. Only if the product remains unidentified does it escalate to manual image matching."*

### Scene 7: Mandatory Human Oversight in Action
- **Action:** In the review card, show the **"Draft Response"** textarea.
- **Action:** Make a quick edit to the draft (e.g. append *"Best regards, Anjali - WaterScience Support"*).
- **Action:** Type an audit note in the Reviewer Comment box: *"Personalized agent sign-off"*.
- **Action:** Click **"✓ Approve Reply"**.
- **Talking Points:**
  - *"The approval status pill immediately turns green ('APPROVED BY AGENT'). In production, this trigger would dispatch the message to the WhatsApp Business API or Zendesk/Freshdesk."*
  - *"This workflow saves over 80% of typing and research time while ensuring zero unapproved messages are sent to customers."*
