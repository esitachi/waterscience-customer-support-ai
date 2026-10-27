// WaterScience Customer Service AI Review Console Client

let syntheticCasesData = [];
let currentCase = null;
let benchmarkResults = [];

document.addEventListener('DOMContentLoaded', async () => {
    await fetchHealth();
    await loadSyntheticCases();
    renderKBSources();
});

function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    const activeBtn = document.getElementById(`tab-${tabId}-btn`);
    const activeContent = document.getElementById(`tab-${tabId}`);
    if (activeBtn) activeBtn.classList.add('active');
    if (activeContent) activeContent.classList.add('active');
}

async function fetchHealth() {
    try {
        const res = await fetch('/health');
        if (res.ok) {
            const data = await res.json();
            const envBadge = document.getElementById('env-badge');
            if (envBadge) {
                envBadge.textContent = `Provider: ${data.llm_provider.toUpperCase()}`;
            }
            const kbBadge = document.getElementById('kb-badge');
            if (kbBadge) {
                kbBadge.textContent = `KB: ${data.kb_sources_count} Sources Loaded`;
            }
        }
    } catch (e) {
        console.error('Health check failed:', e);
    }
}

async function loadSyntheticCases() {
    try {
        const res = await fetch('/api/synthetic-cases');
        if (res.ok) {
            const data = await res.json();
            syntheticCasesData = data.cases || [];
            populatePresetSelect();
            renderBenchmarkTableInitial();
        }
    } catch (e) {
        console.error('Failed to load synthetic cases:', e);
    }
}

function populatePresetSelect() {
    const sel = document.getElementById('preset-select');
    if (!sel) return;
    sel.innerHTML = '<option value="">-- Choose a benchmark case or enter custom --</option>';
    syntheticCasesData.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.case_id;
        opt.textContent = `[${c.case_id}] ${c.product || 'Unknown'} — ${c.issue_category}: "${c.synthetic_customer_message.slice(0, 45)}..."`;
        sel.appendChild(opt);
    });
}

function loadPresetCase() {
    const sel = document.getElementById('preset-select');
    const cid = sel.value;
    if (!cid) return;

    const c = syntheticCasesData.find(item => item.case_id === cid);
    if (!c) return;

    document.getElementById('customer-message').value = c.synthetic_customer_message;
    document.getElementById('product-hint').value = c.product || '';
    
    // Attempt channel pre-selection if obvious
    const msg = c.synthetic_customer_message.toLowerCase();
    const chanSel = document.getElementById('purchase-channel');
    if (msg.includes('amazon')) {
        chanSel.value = 'amazon';
    } else if (msg.includes('website')) {
        chanSel.value = 'waterscience_website';
    } else {
        chanSel.value = '';
    }
}

async function processQuery() {
    const msg = document.getElementById('customer-message').value.trim();
    if (!msg) {
        alert('Please enter or select a customer message.');
        return;
    }

    const productHint = document.getElementById('product-hint').value.trim() || null;
    const channel = document.getElementById('purchase-channel').value || null;
    const orderId = document.getElementById('order-id').value.trim() || null;
    const selPreset = document.getElementById('preset-select').value || null;

    const btn = document.getElementById('process-btn');
    btn.disabled = true;
    btn.innerHTML = '<span>⏳ Processing...</span>';

    try {
        const res = await fetch('/api/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: msg,
                product_hint: productHint,
                purchase_channel: channel,
                order_id: orderId,
                case_id: selPreset
            })
        });

        if (!res.ok) {
            throw new Error(`Error: ${res.statusText}`);
        }

        const data = await res.json();
        currentCase = data;
        renderReviewCard(data);
    } catch (e) {
        alert(`Failed to process query: ${e.message}`);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>⚡ Process with AI Pipeline</span>';
    }
}

function renderReviewCard(c) {
    document.getElementById('empty-state').style.display = 'none';
    const container = document.getElementById('result-container');
    container.style.display = 'block';

    // Status Banner
    const banner = document.getElementById('status-banner');
    const title = document.getElementById('status-title');
    const desc = document.getElementById('status-desc');
    const pill = document.getElementById('approval-pill');

    banner.className = 'status-banner';
    if (c.human_escalation_required) {
        banner.classList.add('escalated');
        title.textContent = '⚠️ Escalated to Human Support';
        desc.textContent = c.reason_for_escalation || 'Technical or policy boundary requires human verification.';
        pill.textContent = 'Escalated / Pending Review';
        pill.className = 'step-badge badge-danger';
    } else if (c.review_status === 'needs_clarification') {
        banner.classList.add('clarification');
        title.textContent = 'ℹ️ Clarification Required from Customer';
        desc.textContent = 'Essential context (e.g. water source or model ID) is missing before final resolution.';
        pill.textContent = 'Needs Clarification';
        pill.className = 'step-badge badge-warning';
    } else {
        banner.classList.add('ready');
        title.textContent = '✅ Evidence-Grounded Draft Ready for Agent Approval';
        desc.textContent = 'All factual claims verified against official sources. Awaiting agent sign-off.';
        pill.textContent = 'Pending Approval';
        pill.className = 'step-badge badge-success';
    }

    // Meta Grid
    document.getElementById('meta-product').textContent = c.detected_product || 'Unidentified / Generic';
    document.getElementById('meta-category').textContent = c.issue_category;
    document.getElementById('meta-channel').textContent = (c.purchase_channel || 'Unknown').replace('_', ' ').toUpperCase();
    document.getElementById('meta-escalation').textContent = c.human_escalation_required ? 'REQUIRED' : 'NO';

    // Missing Info Block
    const missingBlock = document.getElementById('missing-info-block');
    const missingList = document.getElementById('missing-info-list');
    missingList.innerHTML = '';
    if (c.information_needed && c.information_needed.length > 0) {
        missingBlock.style.display = 'block';
        c.information_needed.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item;
            missingList.appendChild(li);
        });
    } else {
        missingBlock.style.display = 'none';
    }

    // Guardrails Block
    const guardBlock = document.getElementById('guardrails-block');
    const guardList = document.getElementById('guardrails-list');
    guardList.innerHTML = '';
    if (c.applied_guardrails && c.applied_guardrails.length > 0) {
        guardBlock.style.display = 'block';
        c.applied_guardrails.forEach(g => {
            const li = document.createElement('li');
            li.textContent = g;
            guardList.appendChild(li);
        });
    } else {
        guardBlock.style.display = 'none';
    }

    // Citations
    const citationsList = document.getElementById('citations-list');
    citationsList.innerHTML = '';
    if (c.cited_sources && c.cited_sources.length > 0) {
        c.cited_sources.forEach(s => {
            const div = document.createElement('div');
            div.className = 'citation-pill';
            div.innerHTML = `
                <div>
                    <span class="citation-id">${s.source_id}</span>
                    <strong>${s.title}</strong>
                    <span style="color: #64748b; font-size: 0.75rem;">(${s.evidence_type})</span>
                </div>
                ${s.url ? `<a href="${s.url}" target="_blank" class="citation-link">Open Source ↗</a>` : ''}
            `;
            citationsList.appendChild(div);
        });
    } else {
        citationsList.innerHTML = '<span style="color: #64748b; font-size: 0.85rem;">No citations available for this query.</span>';
    }

    // Draft Textarea
    const draftTextarea = document.getElementById('draft-textarea');
    draftTextarea.value = c.draft_response;
    updateCharCount();
    draftTextarea.oninput = updateCharCount;

    // Reset reviewer comment
    document.getElementById('reviewer-comment').value = c.reviewer_comment || '';
}

function updateCharCount() {
    const draftTextarea = document.getElementById('draft-textarea');
    const count = draftTextarea.value.length;
    document.getElementById('char-count').textContent = `${count} characters`;
}

async function updateApproval(action) {
    if (!currentCase) return;

    const editedText = document.getElementById('draft-textarea').value;
    const comment = document.getElementById('reviewer-comment').value.trim() || null;

    try {
        const res = await fetch(`/api/cases/${currentCase.case_id}/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: action,
                edited_response: action === 'edit' ? editedText : null,
                reviewer_comment: comment
            })
        });

        if (!res.ok) throw new Error(`Approval update failed`);

        const updated = await res.json();
        currentCase = updated;

        const pill = document.getElementById('approval-pill');
        if (action === 'approve') {
            pill.textContent = 'APPROVED BY AGENT';
            pill.className = 'step-badge badge-success';
            alert('✓ Reply approved! In production, this would dispatch the message to WhatsApp/Email.');
        } else if (action === 'edit') {
            pill.textContent = 'CUSTOM EDITED';
            pill.className = 'step-badge badge-outline';
            alert('💾 Edits saved successfully.');
        } else if (action === 'reject') {
            pill.textContent = 'REJECTED';
            pill.className = 'step-badge badge-danger';
            alert('✕ Draft rejected. Escalated for manual agent drafting.');
        }
    } catch (e) {
        alert(e.message);
    }
}

function renderBenchmarkTableInitial() {
    const tbody = document.getElementById('benchmark-table-body');
    if (!tbody || syntheticCasesData.length === 0) return;

    tbody.innerHTML = '';
    syntheticCasesData.forEach(c => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><span class="case-id-tag">${c.case_id}</span></td>
            <td>${c.synthetic_customer_message}</td>
            <td>${c.product || 'Unknown'}</td>
            <td><span class="badge badge-outline">${c.issue_category}</span></td>
            <td>${c.human_escalation_required ? '<span class="badge badge-danger">Escalate</span>' : '<span class="badge badge-success">Direct</span>'}</td>
            <td><span class="badge badge-outline" id="bench-status-${c.case_id}">Not Run</span></td>
            <td>
                <button class="btn btn-outline" style="padding: 0.3rem 0.6rem; font-size: 0.75rem;" onclick="loadAndInspectCase('${c.case_id}')">
                    Inspect
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function runBenchmark() {
    const btn = document.getElementById('run-benchmark-btn');
    btn.disabled = true;
    btn.textContent = 'Running 20 Tests...';

    try {
        const res = await fetch('/api/run-synthetic-tests', { method: 'POST' });
        if (!res.ok) throw new Error('Benchmark execution failed');

        benchmarkResults = await res.json();
        renderBenchmarkResults(benchmarkResults);
    } catch (e) {
        alert(e.message);
    } finally {
        btn.disabled = false;
        btn.textContent = '▶ Re-run All 20 Cases';
    }
}

function renderBenchmarkResults(results) {
    let passed = 0;
    let failed = 0;
    let escalated = 0;

    results.forEach(r => {
        if (r.pass_status) passed++;
        else failed++;
        if (r.actual_escalation) escalated++;

        const statusEl = document.getElementById(`bench-status-${r.case_id}`);
        if (statusEl) {
            statusEl.textContent = r.pass_status ? 'PASSED' : 'FAILED';
            statusEl.className = r.pass_status ? 'badge badge-success' : 'badge badge-danger';
        }
    });

    document.getElementById('total-cases-count').textContent = results.length;
    document.getElementById('passed-cases-count').textContent = passed;
    document.getElementById('failed-cases-count').textContent = failed;
    document.getElementById('escalated-cases-count').textContent = escalated;
}

function loadAndInspectCase(caseId) {
    const result = benchmarkResults.find(r => r.case_id === caseId);
    const synthetic = syntheticCasesData.find(s => s.case_id === caseId);

    const modal = document.getElementById('case-modal');
    const title = document.getElementById('modal-title');
    const body = document.getElementById('modal-body');

    title.textContent = `Case Evaluation Details: ${caseId}`;

    if (result) {
        body.innerHTML = `
            <div style="margin-bottom: 1rem;">
                <span class="badge ${result.pass_status ? 'badge-success' : 'badge-danger'}">
                    ${result.pass_status ? 'PASS' : 'FAIL'}
                </span>
                <span style="margin-left: 0.5rem; font-weight: 600;">Category: ${result.actual_issue_category}</span>
                <span style="margin-left: 0.5rem; font-weight: 600;">Escalation: ${result.actual_escalation ? 'Yes' : 'No'}</span>
            </div>
            <p><strong>Customer Message:</strong> "${result.customer_message}"</p>
            <div style="margin: 1rem 0; padding: 1rem; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">
                <strong>Evaluation Notes:</strong>
                <ul style="margin-top: 0.5rem; padding-left: 1.25rem;">
                    ${result.evaluation_notes.map(n => `<li>${n}</li>`).join('')}
                </ul>
            </div>
            <div style="margin: 1rem 0;">
                <strong>Generated Draft Reply:</strong>
                <div style="margin-top: 0.4rem; padding: 0.75rem; background: #f1f5f9; border-radius: 6px; font-size: 0.9rem; line-height: 1.5;">
                    ${result.draft_response.replace(/\n/g, '<br>')}
                </div>
            </div>
            <div>
                <strong>Cited Sources:</strong> ${result.cited_sources.join(', ') || 'None'}
            </div>
            <div style="margin-top: 1.5rem; text-align: right;">
                <button class="btn btn-primary" onclick="openInLiveConsole('${caseId}')">
                    Open in Live Review Console →
                </button>
            </div>
        `;
    } else if (synthetic) {
        body.innerHTML = `
            <p><strong>Customer Message:</strong> "${synthetic.synthetic_customer_message}"</p>
            <p><strong>Product:</strong> ${synthetic.product}</p>
            <p><strong>Expected Category:</strong> ${synthetic.issue_category}</p>
            <p><strong>Expected Escalation:</strong> ${synthetic.human_escalation_required ? 'Yes' : 'No'}</p>
            <div style="margin-top: 1.5rem; text-align: right;">
                <button class="btn btn-primary" onclick="openInLiveConsole('${caseId}')">
                    Open in Live Review Console →
                </button>
            </div>
        `;
    }
    modal.classList.add('active');
}

function openInLiveConsole(caseId) {
    closeModal();
    switchTab('live');
    const sel = document.getElementById('preset-select');
    sel.value = caseId;
    loadPresetCase();
    processQuery();
}

function closeModal() {
    document.getElementById('case-modal').classList.remove('active');
}

function renderKBSources() {
    const grid = document.getElementById('kb-sources-grid');
    if (!grid) return;

    const sources = [
        { id: "S01", title: "CLEO Shower & Tap Filter for Hard Water", type: "Official Product Page", url: "https://www.waterscience.in/products/shower-tap-filter-cleo-sfu-717", desc: "Fits 22, 24, 28 mm metal-threaded taps; plastic taps do not fit; max 45°C temp; does not reduce TDS." },
        { id: "S02", title: "CLEO Replacement Cartridge for Shower & Tap Filters", type: "Official Product Page", url: "https://www.waterscience.in/products/replacement-cartridge-filter", desc: "Municipal/Metro (<800 ppm, chlorine) vs Borewell/Tanker (up to 1800 ppm, no chlorine); 4-6 months lifecycle; max 60°C temp (source conflict)." },
        { id: "S03", title: "Warranty & Support Policy", type: "Official Policy Page", url: "https://www.waterscience.in/pages/warranty-support-1", desc: "Requires 7-day registration or valid tax invoice with serial number; 5-yr CLEO filter warranty; 90-day cartridge defect warranty." },
        { id: "S04", title: "Returns & Refund Policy", type: "Official Policy Page", url: "https://www.waterscience.in/pages/returns-refund", desc: "Applies to WaterScience website orders only; 60 days for CLEO, 7 days for other products; damaged/defective condition proof required." },
        { id: "S05", title: "Billing & Shipping Policy", type: "Official Policy Page", url: "https://www.waterscience.in/pages/billing-shipping-policy-new", desc: "WaterScience website orders: 2-3 business days dispatch, 3-4 days Bengaluru transit, 5-6 days rest of India." },
        { id: "S06", title: "IRIS-WMF-325 Washing Machine Filter", type: "Official Product Page", url: "https://www.waterscience.in/products/washing-machine-filter-for-hard-water-replaceable-cartridge", desc: "Supplied adapter fits automatic top/front-load machines; 1/2-inch BSP / 24-mm threads; 3-4 mo top-load, 4-6 mo front-load." },
        { id: "S07", title: "KTF Kitchen Tap Extender with Filter", type: "Official Product Page", url: "https://www.waterscience.in/products/kitchen-tap-extender-with-filter-wide-ceramic-cartridge", desc: "Wide ceramic variant lists 20/22/24 mm male/female aerators; max 40°C temp; NOT certified for drinking water." },
        { id: "S08", title: "RENO Cygnus Water Softeners", type: "Official Product Page", url: "https://www.waterscience.in/products/water-softener", desc: "Whole-home softeners; includes prefilter, stand, starter salt; plumbing input/output excluded; requires on-site consultation." },
        { id: "S09", title: "PURO HFS-625 Self-cleaning Health Faucet", type: "Official Product Page", url: "https://www.waterscience.in/products/waterscience-water-saving-health-faucet-neverblock-technology-puro-hfs-625-c", desc: "Standard 1/2-inch hose fitment; 2-year breakage & damage warranty; leak triage requires valve shut-off and photo evidence." },
        { id: "S10", title: "WaterScience Replacement Cartridges Collection", type: "Official Collection Page", url: "https://www.waterscience.in/collections/replacement-cartridges", desc: "13 distinct cartridges across families; cartridges are not universally interchangeable." },
        { id: "M01", title: "CLEO 2 Manual Mirror (Sep11 PDF)", type: "Legacy Manual Mirror", url: "https://m.media-amazon.com/images/I/B1xekuVv3HS.pdf", desc: "Detailed legacy O-ring & flow restrictor steps; unverified for current models; restricted to internal agent triage." }
    ];

    grid.innerHTML = sources.map(s => `
        <div class="kb-card">
            <div class="kb-card-header">
                <span class="citation-id">${s.id}</span>
                <span class="badge badge-outline">${s.type}</span>
            </div>
            <div class="kb-title">${s.title}</div>
            <p style="font-size: 0.8rem; color: #475569; margin-bottom: 0.75rem;">${s.desc}</p>
            <a href="${s.url}" target="_blank" class="kb-url">${s.url}</a>
        </div>
    `).join('');
}
