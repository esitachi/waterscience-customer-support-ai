# WaterScience customer-service research - Problem 2

Research date: 28 October 2026

## Scope and method

This is evidence research for an agent-assist prototype, not a claim that the prototype has access to WaterScience's internal SOPs, order system or CRM. I started with current official WaterScience product and policy pages, then separated their stated facts from customer reports and source-access gaps. Direct Amazon India listing pages for the observed CLEO ASINs could not be accessed in this research environment, so this report does **not** present any Amazon review or Q&A themes as observed evidence.

The full evidence register is in `research_register.csv`; source IDs in the knowledge base and test data resolve to URLs, enabling the future application to surface its basis for an answer.

## What WaterScience sells: portfolio map

The official storefront navigation shows a much broader support surface than CLEO SFU-717: shower and tap filters, appliance filters, kitchen tap extenders, water softeners, health faucets, hard-water cleaning products, mainline filters, kitchen tap filters, Kiddo hand-shower filters, plus category-specific replacement cartridges. [Official storefront navigation](https://www.waterscience.in/products/shower-tap-filter-cleo-sfu-717)

| Product family | Representative product(s) researched | Replacement / accessory relationship | Support implications |
| --- | --- | --- | --- |
| Shower and tap filters | CLEO SFU-717; other CLEO shower variants | Municipal/Metro and Borewell/Tanker cartridges; tap adapters | Fitment, water-source/cartridge choice, TDS expectations, low flow, replacement |
| Appliance filters | IRIS-WMF-325 washing-machine filter | IRIS cartridge pack; descaler tablets | Automatic-machine/tap fitment, top-vs-front-load replacement timing |
| Kitchen filters and extenders | FLO-KTF-723 Wide ceramic; KTF Mini displayed on same page; AERA tap extenders | Ceramic cartridges, aerators, adapters, washers | Variant identification and aerator/thread compatibility are essential |
| Mainline / whole-home systems | RENO Cygnus; official whole-house range | Prefilter, softener salt, plumbing/installation items | Consultation, home sizing, city/serviceability and installation must be human-led |
| Health faucets | PURO HFS-625 and other PURO variants | Mesh washer, teflon tape, some models have a cartridge | Fitment, leak/fault and warranty triage |

## Overall support problem: what is supportable with public evidence

The assignment's operational premise is about high-volume service messages. The public evidence does not quantify actual WaterScience ticket mix, but it does show a support catalogue with repeated decision patterns:

1. **Product and variant identification.** Similar family names conceal different fitment, warranty and maintenance details. For example, the official KTF page displays Wide and Mini variants, while its explicit fitment facts are for the Wide ceramic version; the system must not transfer them to Mini.
2. **Compatibility before recommendation.** Tap material, thread/aerator size, fixture type, machine type and water source are decisive. A useful reply often starts by asking for these facts rather than generating prose.
3. **Consumable lifecycle.** Shower/tap and washing-machine products depend on product-specific cartridges with distinct replacement guidance. This is ideal for structured retrieval, but only if the SKU is known.
4. **Policy and channel routing.** Warranty, shipping and returns have documented rules for WaterScience website orders. Marketplace orders require a separate policy; the prototype must ask channel first.
5. **Human exception handling.** Leaks, damaged products, warranty eligibility, returns/refunds, unclear model matching and health claims should become structured handoffs rather than autonomous decisions.

## Initial deep dive: CLEO SFU-717

The current CLEO SFU-717 page states that the filter fits metal-threaded taps, showers and hand showers and names 22 mm, 24 mm and 28 mm taps; it explicitly says plastic taps do not fit. It states Municipal/Metro cartridges are for chlorine and moderate hardness, while Borewell/Tanker is for high hardness with no chlorine. It also states that shower/tap filters do not reduce TDS. [CLEO SFU-717 product page](https://www.waterscience.in/products/shower-tap-filter-cleo-sfu-717)

The current CLEO replacement-cartridge page extends that into an explicit compatible-model list, a documented selection aid (Metro/Municipal: chlorine and hardness, TDS below 800 ppm; Borewell/Tanker: high hardness/no chlorine, TDS up to 1800 ppm) and replacement steps. It gives a 4-6 month life depending on usage and water quality, while also separately recommending replacement every six months. [CLEO replacement cartridge page](https://www.waterscience.in/products/replacement-cartridge-filter)

### CLEO-specific support scenarios that are evidence-backed

- **Fit check:** ask fixture type, material and size; answer only for named metal-threaded 22/24/28 mm taps, or refer for a compatibility check.
- **Cartridge choice:** ask water source/chlorine context and product model; do not pick solely from an unverified TDS number.
- **TDS expectation:** explain that an unchanged TDS reading is documented as expected for this product; do not infer drinking-water safety, efficacy or failure from that reading alone.
- **Cartridge change:** the current FAQ supports “red side up” and a short water flush after replacement. A post-install leak should go to a person, not an auto-repair script.
- **Reduced flow:** current guidance attributes it to sediment blockage and mentions reverse flushing, but does not expose a complete current procedure. The assistant can draft a link/support direction, then escalate if unresolved.

### CLEO source conflicts and restrictions

- The SFU-717 product page specifies a **45°C** maximum; the current replacement-cartridge FAQ says hot water up to **60°C**. This is an official-source conflict. The prototype must not select one answer; it should hand off with both source links.
- The SFU-717 page recommends replacement every six months, whereas the cartridge page says 4-6 months and separately says every six months. Replies should say “4-6 months depending on use and water quality,” not guarantee a fixed lifespan.
- A legacy manual mirror provides detailed low-flow and leak troubleshooting, but it is not hosted on WaterScience's current domain. It may be a useful internal research clue, not an automatically delivered current instruction.
- Customer comments about hair/skin are self-reports. The current cartridge page itself says CLEO is not a medical device. The knowledge base therefore excludes medical promises and directs health/safety concerns to a human.

## Cross-product support evidence

| Product | Verified facts useful to support | What must remain product-specific |
| --- | --- | --- |
| IRIS-WMF-325 | Page says it fits automatic top/front-load machines with supplied adapter; connects to described 1/2-inch BSP / 1/2-inch or 24-mm external threads. It specifies 3-4 month top-load and 4-6 month front-load cartridge guidance. [IRIS-WMF-325 page](https://www.waterscience.in/products/washing-machine-filter-for-hard-water-replaceable-cartridge) | Do not reuse CLEO cartridge intervals or shower-fit rules. |
| FLO-KTF-723 Wide ceramic | Page lists 20/22/24 mm M/F aerators and hot water up to 40°C for the Wide ceramic variant. [KTF Wide page](https://www.waterscience.in/products/kitchen-tap-extender-with-filter-wide-ceramic-cartridge) | Do not apply those numbers to KTF Mini or certify water as potable; that evidence was not collected. |
| RENO Cygnus | Page lists accessories and excludes input/output plumbing material; it has separate valve/electronics warranty wording. [RENO Cygnus page](https://www.waterscience.in/products/water-softener) | Sizing, serviceability, installation costs and scheduling require consultation. |
| PURO HFS-625 | Page says it fits standard 1/2-inch hoses and lists a two-year warranty. [PURO HFS-625 page](https://www.waterscience.in/products/waterscience-water-saving-health-faucet-neverblock-technology-puro-hfs-625-c) | Leakage/fault and any warranty decision require evidence and a person. |

The official product pages also contain individual customer reviews. I use these only as customer reports, never proof of frequency or product performance. The research register records examples: a CLEO cartridge performance complaint, a PURO leak report and a RENO defect report. A third-party reseller page offers unverified reports of kitchen-filter fitment, leak and clogging; it is suitable only to justify adversarial test cases, not to claim a common WaterScience defect.

## Policies, channels and deterministic checks

The published warranty page says that customers need either registration within seven days with serial number or a valid invoice; it may request photos/videos. It lists a five-year warranty for CLEO SFU-717 and a 90-day manufacturing-defect warranty for CLEO cartridges, with stated exclusions such as sediment choking and prolonged disuse. [Warranty & Support](https://www.waterscience.in/pages/warranty-support-1)

For **WaterScience website purchases only**, the returns page states 60 days for CLEO products and seven days for other products, with stated eligibility conditions; a refund is described as initiated within seven working days after the relevant request or pickup, and a pickup charge may apply. It must never be used for Amazon, quick-commerce, retail or other marketplace orders. [Returns & Refund](https://www.waterscience.in/pages/returns-refund)

For WaterScience website orders, the shipping page says most orders dispatch in 2-3 business days, then take 3-4 business days inside Bengaluru or 5-6 elsewhere in India, with location/partner variation. This is an estimate, not a delivery promise. [Billing & Shipping Policy](https://www.waterscience.in/pages/billing-shipping-policy-new)

## Recommended 3-4 hour prototype scope

Build an **AI drafting assistant with mandatory human approval**, not an autonomous chatbot.

### Include in the first working demo

1. **CLEO SFU-717 and compatible CLEO cartridge support:** fitment, cartridge selection clarification, replacement steps, TDS expectation, low-flow triage and the documented source conflict.
2. **IRIS-WMF-325 as one second product family:** demonstrates that the system is extensible without pretending that all product rules are universal.
3. **WaterScience website policy routing:** shipping estimate, warranty evidence checklist, and return/refund intake. Explicitly require purchase channel before policy retrieval.
4. **Human escalation cards:** leaks/damage, return/refund/warranty decisions, source conflicts, medical requests, unknown SKU and whole-home-system consultation.
5. **Citations in every draft:** surface source title/URL internally or in the agent panel so the human reviewer can see why a response was drafted.

### Defer from the first demo

- Whole-home softener pricing, sizing, installation and scheduling.
- Potable-water or medical/dermatological assertions.
- Detailed low-flow repair steps from the legacy manual until WaterScience confirms a current manual.
- Amazon policy, reviews and Q&A until the team supplies an accessible export or authorized integration.
- Any product variant without an exact product record.

## Minimum viable agent-assist workflow

```text
Incoming email / WhatsApp
        |
Identify product + variant + purchase channel
        |
Missing critical details? ---- yes ---> ask focused clarification questions
        | no
Retrieve exact product facts + policies + source IDs
        |
Conflict, leak/damage, medical claim, policy decision or unknown SKU?
        |                         |
       no                         yes
        |                         v
Draft cited response        create human-review card + draft only
        |                         |
        +----------> human approves/edits/sends <----------+
```

The decision logic can mostly be deterministic: product/channel identification, policy applicability, required evidence, source conflicts and escalation labels. Use an LLM only to classify a free-text message, ask a natural clarification question and draft a concise response grounded in retrieved records. That keeps cost, latency and hallucination risk lower than a multi-agent autonomous workflow.

## Evidence-backed conclusion

The strongest first support scenarios are CLEO fitment, cartridge selection/maintenance, “why did my TDS not change?”, IRIS washing-machine fitment and WaterScience-web order policy routing. These are specific, documented and useful without automatic commitments.

The most important gaps are Amazon feedback/Q&A access, a current official CLEO troubleshooting manual, resolved hot-water guidance, variant-level documentation for every KTF/mainline/whole-home product, and internal order/warranty systems. The prototype should make those gaps visible through escalation rather than masking them with fluent answers.
