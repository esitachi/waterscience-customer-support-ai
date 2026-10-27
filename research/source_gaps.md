# Source gaps and validation backlog

Research date: 28 October 2026

This log records what was not verified. These are product and safety boundaries for the prototype, not defects attributed to WaterScience.

## High-priority gaps before production use

### 1. Amazon India reviews, Q&A and marketplace policy

- Direct Amazon India product URLs for the observed CLEO ASINs were not accessible through the research tool on 28 October 2026.
- No Amazon review text, question/answer content, seller terms or return/warranty policy is included in the knowledge base.
- Do not describe any issue as “common on Amazon,” quote Amazon customers or apply WaterScience.in return rules to Amazon orders.
- Needed next: an authorized Amazon Seller Central export, a manual research capture with screenshots/URLs and review dates, or an approved API/integration.

## Current official-source conflicts

### 2. CLEO SFU-717 hot-water limit

- The current CLEO SFU-717 page says a maximum of 45°C and says to run cold water first.
- The current CLEO replacement-cartridge FAQ says hot water up to 60°C and also says to run cold water first.
- The prototype labels this `source_conflict` and requires human confirmation. It must not choose the more permissive limit.
- Needed next: product team's authoritative, SKU-specific manual or corrected product-page copy.

### 3. CLEO cartridge replacement timing

- The CLEO SFU-717 page says every six months, varying by use and water quality.
- The replacement-cartridge page says 4-6 months depending on use/water quality and also says every six months.
- Current safe wording: “4-6 months depending on water quality and use; confirm from the product-specific guidance.”
- Needed next: a single operational rule, including a definition of the observed signs that trigger early replacement.

## Documentation gaps

### 4. Current official troubleshooting manual for CLEO SFU-717

- A legacy manual mirror contains detailed instructions for reduced flow, flow restrictors, O-rings and leaks.
- It is not hosted on WaterScience's current domain and its current applicability cannot be confirmed.
- The current official product/cartridge pages are enough for high-level triage but not enough for fully automated repair instructions.
- Needed next: current official PDF/manual, video transcript and a version/date for each SKU.

### 5. Variant-level product facts

- The KTF page presents Wide and Mini variants together, but explicit compatibility/temperature facts were captured for the Wide ceramic variant only.
- The broader store has many shower, faucet, mainline and softener variants, but this research deliberately does not infer one model's fitment, warranty or installation procedure for another.
- Needed next: a canonical product catalogue with SKU, variant, status, compatible cartridge/accessories, thread standards, max temperature, supported water source, warranty, manual URL and last-reviewed date.

### 6. Whole-home softener operating data

- Public pages are sufficient to identify a consultation need but insufficient to automate sizing, total installed price, serviceability, site readiness, salt usage, installation slots or service SLA.
- Needed next: approved sales/service decision tree, city coverage, sizing rules, price rules and escalation owner.

### 7. Order and warranty status

- Public policy pages give process information but not order lookup, invoice validation, warranty registration status, serial verification or final eligibility.
- Needed next: read-only integrations or a secure human handoff form with access controls. Do not put order IDs, phone numbers or images into an ungoverned retrieval corpus.

## Evidence-quality gaps

### 8. Customer feedback is sparse and non-representative

- WaterScience-hosted reviews and one third-party reseller page supplied individual examples only. They do not establish rate, root cause, cohort, channel, product version or frequency.
- Reviews with hair/skin outcomes are subjective reports, not medical or performance validation.
- The prototype uses them to create adverse test cases (fitment, leak, low flow, expectation setting), not to state that a complaint is prevalent.
- Needed next: anonymized internal ticket tagging and/or a reviewed sample of marketplace reviews with provenance and dates.

### 9. Date/version volatility

- Product prices, review counts, availability, offers, pages and policies can change. The repository records the research date but does not guarantee ongoing accuracy.
- Needed next: source-refresh job, `last_verified_at` field, diff review and expiry dates for policy facts.

### 10. Health and potable-water claims

- No clinical evidence, medical indication, drinking-water certification or verified potable-water use record was collected for the researched products.
- Do not promise improvement in hair/skin outcomes, advise against medical care, or certify kitchen-filter water as safe to drink.
- Needed next: explicitly approved legal/compliance wording and product certification documentation if such claims are intended.

## Prototype handling rules derived from these gaps

1. Ask for exact product/variant and purchase channel before retrieving a product or policy answer.
2. Display source IDs and access dates to the human approver.
3. Escalate source conflicts, leaks/damage, unknown compatibility, whole-home systems, returns/refunds/warranty determinations, health claims and marketplace cases.
4. Use deterministic checks for channel/policy applicability and evidence collection; use the LLM only for classification, clarification and draft wording.
5. Log unanswered questions as source gaps instead of converting them into answers.
