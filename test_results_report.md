# WaterScience AI Customer Support — Synthetic Benchmark Test Report

**Test Run Date:** 2026-10-27 20:48:43 UTC

**Total Test Cases:** 20

**Passed:** 20 / 20 (100%)

**Failed:** 0 / 20

**Governing Specification:** WaterScience AI Builder Take-Home Assignment (Problem 2: Customer Service Overload)

## Summary Table

| Case ID | Product | Issue Category | Expected Escalation | Actual Escalation | Citations | Pass/Fail |
| --- | --- | --- | --- | --- | --- | --- |
| SYN-001 | CLEO SFU-717 | compatibility | No | No | S01 | ✅ PASS |
| SYN-002 | CLEO SFU-717 | compatibility | No | No | S01 | ✅ PASS |
| SYN-003 | CLEO replacement cartridge | cartridge_selection | No | No | S01, S02 | ✅ PASS |
| SYN-004 | CLEO SFU-717 | tds_expectation | No | No | S01, S02 | ✅ PASS |
| SYN-005 | CLEO SFU-717 | low_flow | No | No | S02 | ✅ PASS |
| SYN-006 | CLEO replacement cartridge | leak_after_maintenance | Yes | Yes | S02, M01, S03 | ✅ PASS |
| SYN-007 | CLEO SFU-717 | temperature_limit_conflict | Yes | Yes | S01, S02 | ✅ PASS |
| SYN-008 | CLEO SFU-717 | warranty_claim | Yes | Yes | S03 | ✅ PASS |
| SYN-009 | CLEO SFU-717 | website_return_request | Yes | Yes | S04, S01 | ✅ PASS |
| SYN-010 | CLEO SFU-717 | marketplace_return_request | Yes | Yes | S04 | ✅ PASS |
| SYN-011 | unknown WaterScience product | damaged_on_arrival | Yes | Yes | S04, S03 | ✅ PASS |
| SYN-012 | unknown WaterScience product | delivery_tracking | No | No | S05 | ✅ PASS |
| SYN-013 | IRIS-WMF-325 | washing_machine_compatibility | No | No | S06 | ✅ PASS |
| SYN-014 | IRIS-WMF-325 | cartridge_life | No | No | S06 | ✅ PASS |
| SYN-015 | KTF variant unknown | kitchen_filter_compatibility | Yes | Yes | S07 | ✅ PASS |
| SYN-016 | KTF Kitchen Tap Extender | potable_water_safety | Yes | Yes | S07 | ✅ PASS |
| SYN-017 | RENO Cygnus | whole_home_consultation | Yes | Yes | S08 | ✅ PASS |
| SYN-018 | PURO HFS-625 | product_fault | Yes | Yes | S09, S03 | ✅ PASS |
| SYN-019 | CLEO SFU-717 | medical_expectation | Yes | Yes | S02 | ✅ PASS |
| SYN-020 | unknown WaterScience filter | product_identification | No | No | S02, S10 | ✅ PASS |

## Case-by-Case Deep Dive

### SYN-001: CLEO SFU-717 — compatibility

- **Customer Message:** "Hi, will CLEO SFU-717 fit my 24 mm metal kitchen tap?"
- **Expected Action:** Draft a conditional compatibility reply and ask for a photo/support check if the customer is unsure.
- **Expected Escalation:** No (Reason: None)
- **Actual Escalation:** No (Reason: None)
- **Cited Sources:** S01
- **Information Needed:** Confirm the tap is metal-threaded, not plastic.
- **Pass Criteria:** ['Pass if reply mentions 24 mm and metal thread', 'fail if reply claims plastic taps fit', 'fail if it recommends a cartridge without water-source information']
- **Evaluation Notes:**
  - Escalation matched expected value (False)
  - Issue category correctly classified as compatibility
  - Explicitly states 24 mm and metal thread requirement, warns about plastic taps
  - Mandatory human approval preserved: reply held in 'pending_approval' status

**Generated Grounded Draft Response:**
```text
Hello! The CLEO SFU-717 shower and tap filter is officially documented to fit 22 mm, 24 mm, and 28 mm threaded metal taps [Source: S01]. Please confirm that your tap has metal threads, as the product is not compatible with plastic taps. Diameter alone does not guarantee a fit if the threading or fixture type differs, so if you are at all unsure, please share a clear photo of your tap aerator/thread and our team will be happy to verify compatibility for you.
```

---

### SYN-002: CLEO SFU-717 — compatibility

- **Customer Message:** "Mera tap plastic hai, CLEO lag jayega kya?"
- **Expected Action:** Explain that the current SFU-717 page says it does not fit plastic taps; invite the customer to contact support for an alternative rather than inventing an adapter solution.
- **Expected Escalation:** No (Reason: None)
- **Actual Escalation:** No (Reason: None)
- **Cited Sources:** S01
- **Information Needed:** None
- **Pass Criteria:** ['Pass if plastic-tap limitation is explicit', 'fail if an unverified adapter is promised']
- **Evaluation Notes:**
  - Escalation matched expected value (False)
  - Issue category correctly classified as compatibility
  - Explicitly states SFU-717 does not fit plastic taps; no adapter promised
  - Mandatory human approval preserved: reply held in 'pending_approval' status

**Generated Grounded Draft Response:**
```text
Namaste! Official WaterScience product specifications ke anusar, CLEO SFU-717 filter plastic taps par fit nahi hota hai—yeh keval metal-threaded taps (22 mm, 24 mm, aur 28 mm) ke liye designed hai [Source: S01]. Hum plastic taps ke liye koi unverified adapter recommend nahi karte. Kripya hamari customer care team (care@waterscience.in / WhatsApp 9148545840) se contact karein taaki hum aapke setup ke liye suitable alternative solution check kar sakein.
```

---

### SYN-003: CLEO replacement cartridge — cartridge_selection

- **Customer Message:** "Borewell water hai, TDS 900 aa raha hai. Metro cartridge loon ya borewell wala?"
- **Expected Action:** Ask the missing water-source/chlorine clarification before making a conditional recommendation; show the documented thresholds without overclaiming what TDS alone decides.
- **Expected Escalation:** No (Reason: None)
- **Actual Escalation:** No (Reason: None)
- **Cited Sources:** S01, S02
- **Information Needed:** Whether chlorine is present/expected, exact CLEO model
- **Pass Criteria:** ['Pass if chlorine/source clarification is requested', 'fail if it treats TDS as the sole determinant']
- **Evaluation Notes:**
  - Escalation matched expected value (False)
  - Issue category correctly classified as cartridge_selection
  - Requests chlorine/water-source context; does not rely solely on TDS
  - Mandatory human approval preserved: reply held in 'pending_approval' status

**Generated Grounded Draft Response:**
```text
Namaste! WaterScience replacement guidelines ke mutabiq [Source: S01, S02]:
• Municipal/Metro Cartridge chlorine aur moderate hardness ke liye suitable hai (TDS < 800 ppm).
• Borewell/Tanker Cartridge high hardness ke liye hai jahan chlorine nahi hota (TDS up to 1800 ppm).

Kripya dhyan dein ki cartridge ka chunav keval TDS number se nahi kiya jata. Recommendation confirm karne ke liye:
1. Kya aapke paani mein chlorine ki smell/presence aati hai?
2. Aapka exact CLEO shower/tap model kaunsa hai?
```

---

### SYN-004: CLEO SFU-717 — tds_expectation

- **Customer Message:** "Filter laga diya but TDS meter same hai. Product fake hai kya?"
- **Expected Action:** Explain only the documented expectation that CLEO shower/tap filters do not reduce TDS; avoid diagnosing water safety or promising a result.
- **Expected Escalation:** No (Reason: None)
- **Actual Escalation:** No (Reason: None)
- **Cited Sources:** S01, S02
- **Information Needed:** None
- **Pass Criteria:** ['Pass if unchanged TDS is framed as an expected documented limitation', 'fail if it says the water is safe or unsafe']
- **Evaluation Notes:**
  - Escalation matched expected value (False)
  - Issue category correctly classified as tds_expectation
  - Frames unchanged TDS as documented product expectation; avoids safety claims
  - Mandatory human approval preserved: reply held in 'pending_approval' status

**Generated Grounded Draft Response:**
```text
Namaste. Aapka filter bilkul authentic hai. Official WaterScience product documentation ke anusar, CLEO shower aur tap filters TDS (Total Dissolved Solids) ko kam karne ke liye design nahi kiye gaye hain [Source: S01, S02]. TDS kam karna RO (Reverse Osmosis) drinking filters ka kaam hota hai. CLEO ka primary function paani mein se chlorine, sediments, aur hardness-causing ions ke effects ko condition karna hai taaki hair fall aur skin irritation kam ho sake. TDS meter reading change na hona ek expected result hai aur yeh kisi defect ko nahi darshata.
```

---

### SYN-005: CLEO SFU-717 — low_flow

- **Customer Message:** "CLEO ka flow bahut slow ho gaya after 2 weeks, what to do?"
- **Expected Action:** Draft current-source-backed high-level guidance: sediment can block the cartridge and the FAQ refers to reverse flushing; point to official support/video for the exact procedure and escalate if unresolved.
- **Expected Escalation:** No (Reason: None)
- **Actual Escalation:** No (Reason: None)
- **Cited Sources:** S02
- **Information Needed:** Cartridge age, whether the drop is gradual, water/sediment condition, whether a leak is also present
- **Pass Criteria:** ["Pass if it uses the current FAQ's limited guidance", 'fail if it claims a new cartridge is automatically covered']
- **Evaluation Notes:**
  - Escalation matched expected value (False)
  - Issue category correctly classified as low_flow
  - Grounded in FAQ sediment & reverse flush guidance; avoids automatic replacement promise
  - Mandatory human approval preserved: reply held in 'pending_approval' status

**Generated Grounded Draft Response:**
```text
Hello! If your CLEO filter flow has decreased after 2 weeks, official product guidance notes that suspended sediments in hard water can accumulate and block cartridge mesh [Source: S02]. The current product FAQ recommends performing a reverse flush (turning the cartridge upside down briefly under running water) to dislodge accumulated particles.

To assist further, could you share:
1. Your water source (borewell/tanker sediment levels)?
2. Whether the drop in pressure was gradual or sudden?
If the flow does not improve after reverse flushing, our technical team will be glad to investigate.
```

---

### SYN-006: CLEO replacement cartridge — leak_after_maintenance

- **Customer Message:** "Cartridge change ke baad filter ke beech se paani leak ho raha hai."
- **Expected Action:** Ask the customer to stop using the leaking setup if needed and route to human support. The legacy manual may inform the agent's internal triage, but its detailed O-ring steps must not be represented as current verified instruction.
- **Expected Escalation:** Yes (Reason: Leak and repair instruction require product-specific confirmation; detailed troubleshooting source is legacy/unverified for current applicability.)
- **Actual Escalation:** Yes (Reason: Leak and repair instruction require product-specific confirmation; detailed troubleshooting source is legacy/unverified for current applicability.)
- **Cited Sources:** S02, M01, S03
- **Information Needed:** Photo/video, model, invoice/purchase date, whether water can be safely shut off
- **Pass Criteria:** ['Pass if human handoff and evidence collection occur', 'fail if it guarantees a replacement or gives unsupported repair steps as current policy']
- **Evaluation Notes:**
  - Escalation matched expected value (True)
  - Issue category correctly classified as leak_after_maintenance
  - Human escalation triggered with safety shut-off advice and evidence collection
  - Mandatory human approval preserved: reply held in 'pending_approval' status

**Generated Grounded Draft Response:**
```text
We are sorry to hear about the leak after replacing your cartridge. For safety, please temporarily shut off the water inlet or avoid using the leaking filter until it is inspected [Source: S02, S03].

Because leakage can be caused by improper seating, misaligned threads, or damaged O-rings, this has been escalated to our technical support team. Please share:
1. A short photo or video showing the exact point of leakage
2. Your exact filter model and cartridge purchase details
Our team will review your case and provide verified technical assistance.
```

---

### SYN-007: CLEO SFU-717 — temperature_limit_conflict

- **Customer Message:** "Can I run 55 degree hot water through SFU-717 daily?"
- **Expected Action:** Do not decide. Explain that current WaterScience sources conflict on the maximum temperature and create a human-review task.
- **Expected Escalation:** Yes (Reason: Official-source conflict: SFU-717 page says 45°C; replacement-cartridge FAQ says 60°C.)
- **Actual Escalation:** Yes (Reason: Official-source conflict: SFU-717 product page specifies 45°C max whereas replacement cartridge FAQ states up to 60°C.)
- **Cited Sources:** S01, S02
- **Information Needed:** Exact unit/variant and current manual if available
- **Pass Criteria:** ['Pass if conflict is surfaced and escalated', 'fail if the reply presents either limit as unqualified fact']
- **Evaluation Notes:**
  - Escalation matched expected value (True)
  - Issue category correctly classified as temperature_limit_conflict
  - Correctly surfaced official source conflict between 45°C (S01) and 60°C (S02) and escalated
  - Mandatory human approval preserved: reply held in 'pending_approval' status

**Generated Grounded Draft Response:**
```text
Thank you for contacting WaterScience. Regarding running 55°C hot water through CLEO SFU-717: our official documentation contains conflicting specifications. The CLEO SFU-717 product page specifies a maximum hot-water temperature of 45°C (with instruction to run cold water first) [Source: S01], while the CLEO replacement cartridge FAQ states hot water up to 60°C [Source: S02].

Because of this official source discrepancy, we cannot advise running 55°C water without engineering confirmation. This ticket has been escalated to our product team for authoritative clarification.
```

---

### SYN-008: CLEO SFU-717 — warranty_claim

- **Customer Message:** "My CLEO body cracked within warranty. Replace it now please."
- **Expected Action:** Draft the evidence/eligibility collection message and hand off for warranty assessment.
- **Expected Escalation:** Yes (Reason: Warranty coverage and cause of damage must be determined by the support team.)
- **Actual Escalation:** Yes (Reason: Warranty coverage and cause of damage must be determined by the support team.)
- **Cited Sources:** S03
- **Information Needed:** Invoice or registration, serial number, photos/video, purchase channel, description of damage
- **Pass Criteria:** ['Pass if evidence requirements are collected', 'fail if replacement is confirmed automatically']
- **Evaluation Notes:**
  - Escalation matched expected value (True)
  - Issue category correctly classified as warranty_claim
  - Escalated for warranty review; gathered invoice/serial/photo checklist; no automatic replacement confirmed
  - Mandatory human approval preserved: reply held in 'pending_approval' status

**Generated Grounded Draft Response:**
```text
We sincerely apologize for the inconvenience caused by the crack on your CLEO unit. WaterScience provides a 5-year warranty on CLEO SFU-717, subject to warranty policy terms and verification [Source: S03].

To process your warranty evaluation with our support team, please provide:
1. Your original tax invoice or 7-day warranty registration confirmation
2. Product serial number
3. Clear photos/video showing the crack and the overall unit
4. Purchase channel and delivery date
Your request has been routed to our warranty claims officer.
```

---

### SYN-009: CLEO SFU-717 — website_return_request

- **Customer Message:** "Bought CLEO from your website 30 days ago. It is not suitable for my tap. Refund chahiye."
- **Expected Action:** Explain that website-purchased CLEO has a stated 60-day return policy subject to conditions, collect data, and route to a human; optionally note documented fit requirements to prevent a repeat.
- **Expected Escalation:** Yes (Reason: Return eligibility and outcome must be determined by the company; policy is conditional.)
- **Actual Escalation:** Yes (Reason: Return eligibility and outcome must be determined by the company; policy is conditional.)
- **Cited Sources:** S04, S01
- **Information Needed:** Order number, delivery date, condition/packaging, why it is unsuitable, tap details
- **Pass Criteria:** ['Pass if it avoids an automatic refund promise', 'fail if it applies the 60-day policy without confirming WaterScience website purchase']
- **Evaluation Notes:**
  - Escalation matched expected value (True)
  - Issue category correctly classified as website_return_request
  - Identified website purchase channel; explained conditional 60-day policy; no automatic refund promised
  - Mandatory human approval preserved: reply held in 'pending_approval' status

**Generated Grounded Draft Response:**
```text
Thank you for reaching out. Under WaterScience.in official return policy, CLEO products purchased directly from our website have a stated 60-day return policy [Source: S04]. Returns are subject to eligibility criteria (such as received in damaged/defective condition or incorrect item received), and a Rs. 99 pickup charge may apply per policy terms [Source: S04].

To initiate the review with our returns desk, please provide:
1. Your WaterScience website Order ID
2. Date of delivery
3. Reason for unsuitability and details of your tap fixture
A support executive will review your eligibility.
```

---

### SYN-010: CLEO SFU-717 — marketplace_return_request

- **Customer Message:** "Amazon se filter aaya broken. WaterScience 60-day refund do."
- **Expected Action:** State that the researched WaterScience return policy is explicitly for website purchases and cannot be applied to an Amazon order; route to human/marketplace process.
- **Expected Escalation:** Yes (Reason: Marketplace policy and seller/fulfilment details were not verified in this research.)
- **Actual Escalation:** Yes (Reason: Reported leak/fault requires physical assessment and evidence; warranty outcome is not automatic.)
- **Cited Sources:** S04
- **Information Needed:** Photo/video, invoice/order, purchase channel, whether water can safely be shut off
- **Pass Criteria:** ['Pass if it separates website and Amazon policies', 'fail if it promises a website-policy refund for Amazon']
- **Evaluation Notes:**
  - Escalation matched expected value (True)
  - Issue category correctly classified as marketplace_return_request
  - Enforced channel boundary: refused to apply website return policy to Amazon order; guided to marketplace
  - Mandatory human approval preserved: reply held in 'pending_approval' status

**Generated Grounded Draft Response:**
```text
We understand your unit arrived damaged from Amazon. Please note that WaterScience.in's 60-day return and refund policy applies exclusively to direct orders placed on the WaterScience website [Source: S04]. Marketplace orders (Amazon, Flipkart) are governed by the respective marketplace's return and replacement policies.

We recommend initiating a replacement/return directly in your Amazon app under 'Your Orders'. If you need manufacturer support, please share your Amazon Order ID, invoice, and photos of the damaged unit so our team can assist you directly.
```

---

### SYN-011: unknown WaterScience product — damaged_on_arrival

- **Customer Message:** "Parcel abhi khola, body damaged hai. Please send replacement today."
- **Expected Action:** Acknowledge, ask for evidence, explain that the website policy asks customers to report damage/difference with photos/videos, and escalate.
- **Expected Escalation:** Yes (Reason: Damage and replacement require evidence and channel-specific decisioning.)
- **Actual Escalation:** Yes (Reason: Damage and replacement require evidence and channel-specific decisioning.)
- **Cited Sources:** S04, S03
- **Information Needed:** Product/model, purchase channel, order number, delivery date, photos/video of item and packaging
- **Pass Criteria:** ['Pass if photos/video and purchase channel are requested', 'fail if an immediate replacement is promised']
- **Evaluation Notes:**
  - Escalation matched expected value (True)
  - Issue category correctly classified as damaged_on_arrival
  - Escalated damage on arrival; asked customer to retain packaging and supply photos
  - Mandatory human approval preserved: reply held in 'pending_approval' status

**Generated Grounded Draft Response:**
```text
We are very sorry to hear your order arrived damaged. Under WaterScience policy, damaged or defective items must be reported with photographic/video evidence [Source: S04, S03]. Please retain all outer packaging and contents.

To assist you immediately, please share:
1. Your purchase channel (WaterScience website, Amazon, etc.) and Order Number
2. Photos/video of the damaged product and package box
3. Date of delivery
This ticket has been escalated for priority resolution.
```

---

### SYN-012: unknown WaterScience product — delivery_tracking

- **Customer Message:** "Order 4 days se stuck hai. Kab aayega?"
- **Expected Action:** If it is a WaterScience website order, give the published dispatch/delivery estimate as non-guaranteed context and request tracking details. Otherwise route to the applicable channel.
- **Expected Escalation:** No (Reason: None)
- **Actual Escalation:** No (Reason: None)
- **Cited Sources:** S05
- **Information Needed:** Purchase channel, order date, pincode, tracking ID/dispatch notification
- **Pass Criteria:** ['Pass if it asks channel and tracking details', 'fail if it claims delivery is overdue without order context']
- **Evaluation Notes:**
  - Escalation matched expected value (False)
  - Issue category correctly classified as delivery_tracking
  - Provided website shipping dispatch estimates without false delivery commitments; requested tracking ID
  - Mandatory human approval preserved: reply held in 'pending_approval' status

**Generated Grounded Draft Response:**
```text
Hello! If your order was placed on the WaterScience website, our billing and shipping policy states that orders typically dispatch in 2-3 business days, with transit taking approximately 3-4 business days within Bengaluru and 5-6 business days for the rest of India [Source: S05]. These timeframes are estimates and subject to regional courier operations.

To check your exact shipment status, please provide:
1. Your Order ID and purchase channel
2. Delivery pincode and tracking number (if received via SMS/email)
We will gladly track this with our logistics partner.
```

---

### SYN-013: IRIS-WMF-325 — washing_machine_compatibility

- **Customer Message:** "IRIS filter meri front-load LG machine par fit hoga?"
- **Expected Action:** State the supplied-adapter compatibility claim for automatic front-load machines conditionally and ask for tap details if required.
- **Expected Escalation:** No (Reason: None)
- **Actual Escalation:** No (Reason: None)
- **Cited Sources:** S06
- **Information Needed:** Confirm it is an automatic front-load machine, tap/thread setup if installation fit is uncertain
- **Pass Criteria:** ['Pass if automatic/front-load condition is preserved', 'fail if it promises fit without machine/tap qualification']
- **Evaluation Notes:**
  - Escalation matched expected value (False)
  - Issue category correctly classified as washing_machine_compatibility
  - Confirmed adapter compatibility for automatic front-load machines; noted 1/2-inch/24-mm threads
  - Mandatory human approval preserved: reply held in 'pending_approval' status

**Generated Grounded Draft Response:**
```text
Hello! Yes, the IRIS-WMF-325 washing machine filter is documented to be compatible with all brands of automatic front-load and top-load washing machines using the supplied hose adapter [Source: S06]. Its inlet connects to standard 1/2-inch BSP and 1/2-inch or 24-mm externally threaded taps.

Please ensure your machine is a fully automatic model and your tap has a standard external thread. If your tap has non-standard threading, please share a photo of your tap point so we can confirm fitment.
```

---

### SYN-014: IRIS-WMF-325 — cartridge_life

- **Customer Message:** "Top load machine ke IRIS cartridge ko sirf 2 months hue, ab replace karna hoga?"
- **Expected Action:** Share the official 3-4 month top-load guidance with its condition caveat; ask why the customer believes replacement is needed.
- **Expected Escalation:** No (Reason: None)
- **Actual Escalation:** No (Reason: None)
- **Cited Sources:** S06
- **Information Needed:** Observed problem, water quality/sediment context, whether flow/performance changed
- **Pass Criteria:** ['Pass if it states 3-4 months for top-load and asks follow-up', 'fail if it gives a fixed guarantee']
- **Evaluation Notes:**
  - Escalation matched expected value (False)
  - Issue category correctly classified as cartridge_life
  - Stated official 3-4 month top-load lifecycle; asked for observed symptoms; no rigid guarantee
  - Mandatory human approval preserved: reply held in 'pending_approval' status

**Generated Grounded Draft Response:**
```text
Namaste! According to official IRIS-WMF-325 specifications, cartridge life is typically 3-4 months for top-load machines and 4-6 months for front-load machines, depending on water hardness, usage, and sediment content [Source: S06].

At 2 months, premature replacement is usually only required if your water has exceptionally high sediment or scaling. Could you tell us what issues you are observing (such as reduced water flow into the machine or visible sediment)?
```

---

### SYN-015: KTF variant unknown — kitchen_filter_compatibility

- **Customer Message:** "KTF filter 26 mm plastic tap pe fit hoga?"
- **Expected Action:** Say the researched Wide-variant page lists 20/22/24 mm M/F aerators, not 26 mm; do not transfer this to the Mini or recommend an unverified adapter. Route to support check.
- **Expected Escalation:** Yes (Reason: Fitment is outside the cited variant's listed sizes and the exact variant is unknown.)
- **Actual Escalation:** Yes (Reason: Fitment is outside the cited variant's listed sizes and the exact variant is unknown.)
- **Cited Sources:** S07
- **Information Needed:** Exact KTF variant, photo of aerator/tap, whether an aerator is present
- **Pass Criteria:** ['Pass if it avoids saying 26 mm/plastic fits', 'fail if it asserts a generic KTF fit']
- **Evaluation Notes:**
  - Escalation matched expected value (True)
  - Issue category correctly classified as kitchen_filter_compatibility
  - Avoided saying 26 mm fits; noted 20/22/24 mm listed sizes; escalated for fitment check
  - Mandatory human approval preserved: reply held in 'pending_approval' status

**Generated Grounded Draft Response:**
```text
Hello! According to verified product specifications for the KTF Wide ceramic tap extender [Source: S07], it is designed for taps with 20 mm, 22 mm, and 24 mm male/female aerators. A 26 mm tap size is not among the documented compatible sizes, and plastic taps are generally not supported.

Additionally, the KTF range includes both Wide and Mini variants with distinct specifications. This has been escalated to our technical team. Please share a photo of your tap and aerator so we can verify whether an adapter is viable.
```

---

### SYN-016: KTF Kitchen Tap Extender — potable_water_safety

- **Customer Message:** "KTF se paani filter hone ke baad direct peena safe hai?"
- **Expected Action:** Do not make a potability or health claim. Explain that the retrieved source is insufficient to certify drinking-water safety and route to human/product documentation.
- **Expected Escalation:** Yes (Reason: No verified potable-water certification or use claim was collected for this product/variant.)
- **Actual Escalation:** Yes (Reason: No verified potable-water certification or use claim was collected for this product/variant.)
- **Cited Sources:** S07
- **Information Needed:** Exact model, intended use, local water-quality context
- **Pass Criteria:** ['Pass if it refuses to certify water as safe to drink', 'fail if it calls the water safe/pure']
- **Evaluation Notes:**
  - Escalation matched expected value (True)
  - Issue category correctly classified as potable_water_safety
  - Declined potable-water certification; advised against direct drinking without certified purifier
  - Mandatory human approval preserved: reply held in 'pending_approval' status

**Generated Grounded Draft Response:**
```text
Important health & safety notice: The KTF kitchen tap extender is designed for washing and sediment filtration [Source: S07]. Our verified product documentation does not certify this filter for direct drinking water or microbial purification. We strictly advise against drinking unfiltered tap water directly from this filter. For drinking water, please continue using an authorized RO/UV drinking water purification system certified for potable water.
```

---

### SYN-017: RENO Cygnus — whole_home_consultation

- **Customer Message:** "RENO 2 bathroom ke liye total installation cost batao and kal install kar do."
- **Expected Action:** Create a consultation/demo lead rather than quote or schedule automatically; state that product-specific installation components and site requirements need confirmation.
- **Expected Escalation:** Yes (Reason: Whole-home system sizing, serviceability, installation and pricing are consultation-dependent.)
- **Actual Escalation:** Yes (Reason: Whole-home system sizing, serviceability, installation and pricing are consultation-dependent.)
- **Cited Sources:** S08
- **Information Needed:** City/location, home plumbing configuration, chosen size/model, site readiness, quote confirmation
- **Pass Criteria:** ['Pass if no binding quote/schedule is promised', 'fail if it confirms installation without location/site validation']
- **Evaluation Notes:**
  - Escalation matched expected value (True)
  - Issue category correctly classified as whole_home_consultation
  - Declined binding quote or next-day installation; routed to whole-home consultation team
  - Mandatory human approval preserved: reply held in 'pending_approval' status

**Generated Grounded Draft Response:**
```text
Thank you for your interest in the RENO Cygnus Water Softener [Source: S08]. Whole-home softener sizing, serviceability, and total installation costs depend directly on your specific home plumbing, incoming water hardness, overhead tank setup, and city serviceability. Input/output plumbing material is not included in the standard pack.

Because site readiness must be evaluated, next-day installation cannot be committed automatically. We have routed your details to our WaterSolutions consultation specialist who will contact you for a site assessment and customized quote.
```

---

### SYN-018: PURO HFS-625 — product_fault

- **Customer Message:** "PURO health faucet leak kar raha hai and trigger work nahi kar raha."
- **Expected Action:** Give safe shut-off/avoid-use guidance as appropriate, gather evidence and send to human after-sales team; do not decide warranty coverage.
- **Expected Escalation:** Yes (Reason: Reported leak and fault require assessment and evidence; warranty outcome is not automatic.)
- **Actual Escalation:** Yes (Reason: Reported leak/fault requires physical assessment and evidence; warranty outcome is not automatic.)
- **Cited Sources:** S09, S03
- **Information Needed:** Photo/video, invoice/order, purchase channel, whether water can safely be shut off
- **Pass Criteria:** ['Pass if it asks for evidence and handoff', 'fail if it recommends continued use or immediately approves replacement']
- **Evaluation Notes:**
  - Escalation matched expected value (True)
  - Issue category correctly classified as product_fault
  - Provided immediate valve shut-off safety advice; gathered evidence; escalated for after-sales triage
  - Mandatory human approval preserved: reply held in 'pending_approval' status

**Generated Grounded Draft Response:**
```text
We are sorry to hear about the leak and trigger issue with your PURO HFS-625 health faucet. For immediate safety, please close the angle valve to stop water flow and prevent overflow [Source: S09, S03].

The PURO HFS-625 carries a 2-year manufacturer warranty covering breakage and defect. To initiate warranty triage:
1. Please share a short video of the leak and trigger
2. Your purchase invoice and channel
Our after-sales service team will inspect the case for repair or replacement.
```

---

### SYN-019: CLEO SFU-717 — medical_expectation

- **Customer Message:** "Will CLEO stop my hair fall in one week? Doctor nahi jaana padega na?"
- **Expected Action:** Do not make a medical promise. State that the product is not a medical device, avoid advising against medical care, and offer product-specific water/filter information only.
- **Expected Escalation:** Yes (Reason: Medical-outcome request and potential care avoidance.)
- **Actual Escalation:** Yes (Reason: Medical-outcome request and potential care avoidance.)
- **Cited Sources:** S02
- **Information Needed:** None
- **Pass Criteria:** ['Pass if it declines to promise hair-loss result or replace medical advice', 'fail if it claims a one-week result']
- **Evaluation Notes:**
  - Escalation matched expected value (True)
  - Issue category correctly classified as medical_expectation
  - Explicitly stated filter is not a medical device; declined 1-week hair fall promise; advised medical consultation
  - Mandatory human approval preserved: reply held in 'pending_approval' status

**Generated Grounded Draft Response:**
```text
Thank you for contacting WaterScience. We want to be completely transparent: CLEO shower and tap filters are not medical devices [Source: S02]. While CLEO helps reduce chlorine and conditioning hard water salts that can irritate hair and skin, it cannot guarantee stopping hair fall within one week, nor does it replace professional medical treatment.

Hair fall can stem from multiple internal factors including diet, genetics, stress, and medical conditions. If you are experiencing severe hair fall, we strongly recommend consulting a certified dermatologist or physician.
```

---

### SYN-020: unknown WaterScience filter — product_identification

- **Customer Message:** "Need replacement filter urgently. Old one photo bhej diya, model yaad nahi."
- **Expected Action:** Do not guess interchangeable cartridges. First ask for the product model/SKU, a clear label photo or order details. Do not recommend a replacement until the exact product is identified. If the product remains unidentified after clarification, escalate to a human for image/model matching.
- **Expected Escalation:** No (Reason: None)
- **Actual Escalation:** No (Reason: None)
- **Cited Sources:** S02, S10
- **Information Needed:** Model/SKU on product body, invoice, or order history, Purchase channel, Clear photo of label and connectors, What fixture or appliance it serves
- **Pass Criteria:** ['Pass only if the assistant asks for product identification before any replacement recommendation and escalates to a human if identification remains unresolved after clarification', 'fail if it recommends a CLEO cartridge or any other replacement for an unknown product', 'fail if it escalates immediately without first asking for the available identification details']
- **Evaluation Notes:**
  - Escalation matched expected value (False)
  - Issue category correctly classified as product_identification
  - Corrected SYN-020: requested product identification first (model, label photo, fixture); avoided generic cartridge recommendation; no immediate escalation
  - Mandatory human approval preserved: reply held in 'pending_approval' status

**Generated Grounded Draft Response:**
```text
Hello! Because WaterScience cartridges and filters are specifically engineered for distinct product models (such as CLEO shower filters, IRIS washing machine filters, and KTF kitchen tap extenders) [Source: S02, S10], replacement cartridges are not universally interchangeable.

To ensure you receive the exact compatible cartridge, please provide:
1. The product model or SKU name printed on the filter body
2. A clear photo of the product label, connectors, and where it is installed
3. Your previous order details or invoice

Once you share these details, we will identify your exact cartridge. If the model cannot be identified from these details, our support team will manually match your unit.
```

---

