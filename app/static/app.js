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

    if (tabId === 'operations') {
        loadOperationsDashboard();
    } else if (tabId === 'kb') {
        checkKBDraftVersion();
    } else if (tabId === 'simulator') {
        refreshSimulatorStatus();
    }
}

async function fetchHealth() {
    try {
        const res = await fetch('/health');
        if (res.ok) {
            const data = await res.json();
            const envBadge = document.getElementById('env-badge');
            if (envBadge) {
                const prov = data.configured_llm_provider || data.llm_provider || 'mock';
                if (prov === 'groq') {
                    if (data.live_credentials_present) {
                        envBadge.textContent = 'Provider: Groq (Live AI)';
                        envBadge.className = 'badge badge-success';
                    } else {
                        envBadge.textContent = 'Provider: Groq (No Key → Fallback Mock)';
                        envBadge.className = 'badge badge-warning';
                    }
                } else if (prov === 'openai') {
                    if (data.live_credentials_present) {
                        envBadge.textContent = 'Provider: OpenAI (Live AI)';
                        envBadge.className = 'badge badge-success';
                    } else {
                        envBadge.textContent = 'Provider: OpenAI (No Key → Fallback Mock)';
                        envBadge.className = 'badge badge-warning';
                    }
                } else {
                    envBadge.textContent = 'Provider: Mock Mode (Deterministic)';
                    envBadge.className = 'badge badge-outline';
                }
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

    const metaProvider = document.getElementById('meta-provider');
    if (metaProvider) {
        if (c.execution_provider === 'live_llm') {
            metaProvider.innerHTML = '<span style="color: #059669; font-weight: 600;">⚡ Live LLM (Groq)</span>';
        } else if (c.execution_provider === 'fallback_mock') {
            const reason = c.provider_error_category ? ` (${c.provider_error_category})` : '';
            metaProvider.innerHTML = `<span style="color: #d97706; font-weight: 600;">⚠️ Fallback Mock${reason}</span>`;
        } else {
            metaProvider.innerHTML = '<span style="color: #475569; font-weight: 500;">🔒 Deterministic Mock</span>';
        }
    }

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
    const commentInput = document.getElementById('reviewer-comment');
    commentInput.value = c.reviewer_comment || '';

    // Reset or apply approval state
    const actionButtons = document.getElementById('action-buttons');
    const finalizedCard = document.getElementById('finalized-card');
    const btnApprove = document.getElementById('btn-approve');
    const btnEdit = document.getElementById('btn-edit');
    const btnReject = document.getElementById('btn-reject');

    if (c.approval_status === 'approved') {
        lockCaseUI('approved', c.reviewer_comment);
    } else if (c.approval_status === 'rejected') {
        lockCaseUI('rejected', c.reviewer_comment);
    } else {
        // Unlock for fresh/pending review
        draftTextarea.readOnly = false;
        draftTextarea.classList.remove('locked-input');
        commentInput.disabled = false;
        if (actionButtons) actionButtons.style.display = 'flex';
        if (finalizedCard) finalizedCard.style.display = 'none';
        if (btnApprove) {
            btnApprove.disabled = false;
            btnApprove.innerHTML = '✓ Approve Reply';
        }
        if (btnEdit) btnEdit.disabled = false;
        if (btnReject) btnReject.disabled = false;
        if (c.approval_status === 'edited') {
            pill.textContent = 'Custom Edited';
            pill.className = 'step-badge badge-outline';
            if (btnApprove) btnApprove.innerHTML = '✓ Approve & Dispatch Reply';
        }
    }
}

function lockCaseUI(state, comment) {
    const pill = document.getElementById('approval-pill');
    const draftTextarea = document.getElementById('draft-textarea');
    const commentInput = document.getElementById('reviewer-comment');
    const actionButtons = document.getElementById('action-buttons');
    const finalizedCard = document.getElementById('finalized-card');

    draftTextarea.readOnly = true;
    draftTextarea.classList.add('locked-input');
    commentInput.disabled = true;
    if (actionButtons) actionButtons.style.display = 'none';

    if (state === 'approved') {
        pill.textContent = 'APPROVED & DISPATCHED';
        pill.className = 'step-badge badge-success';
        if (finalizedCard) {
            finalizedCard.className = 'finalized-card approved';
            finalizedCard.innerHTML = `
                <div class="finalized-header">
                    <div class="finalized-icon-badge">✓</div>
                    <div class="finalized-text">
                        <h4 class="finalized-title">Reply Approved & Dispatched</h4>
                        <p class="finalized-subtitle">Signed off by agent. Response has been queued for customer dispatch via WhatsApp/Email.</p>
                    </div>
                </div>
                <div class="finalized-meta">
                    <span class="audit-note-text"><strong>Audit Note:</strong> ${comment || 'Approved without modification'}</span>
                    <button class="btn btn-sm btn-outline-brand" onclick="resetForNewQuery()">Process Next Query →</button>
                </div>
            `;
            finalizedCard.style.display = 'block';
        }
    } else if (state === 'rejected') {
        pill.textContent = 'REJECTED';
        pill.className = 'step-badge badge-danger';
        if (finalizedCard) {
            finalizedCard.className = 'finalized-card rejected';
            finalizedCard.innerHTML = `
                <div class="finalized-header">
                    <div class="finalized-icon-badge">✕</div>
                    <div class="finalized-text">
                        <h4 class="finalized-title">Draft Rejected & Discarded</h4>
                        <p class="finalized-subtitle">AI draft dismissed. Case forwarded to Tier-2 senior human queue for manual composition.</p>
                    </div>
                </div>
                <div class="finalized-meta">
                    <span class="audit-note-text"><strong>Reason:</strong> ${comment || 'Rejected without specific note'}</span>
                    <button class="btn btn-sm btn-outline-brand" onclick="resetForNewQuery()">Process Next Query →</button>
                </div>
            `;
            finalizedCard.style.display = 'block';
        }
    }
}

function resetForNewQuery() {
    document.getElementById('customer-message').value = '';
    document.getElementById('preset-select').value = '';
    document.getElementById('order-id').value = '';
    document.getElementById('product-hint').value = '';
    document.getElementById('empty-state').style.display = 'block';
    document.getElementById('result-container').style.display = 'none';
    currentCase = null;
    showToast('Ready for new customer message.', 'info');
    document.getElementById('customer-message').focus();
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast-item toast-${type}`;
    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('show');
    }, 10);

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3500);
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

    const btnApprove = document.getElementById('btn-approve');
    const btnEdit = document.getElementById('btn-edit');
    const btnReject = document.getElementById('btn-reject');

    if (btnApprove) btnApprove.disabled = true;
    if (btnEdit) btnEdit.disabled = true;
    if (btnReject) btnReject.disabled = true;

    try {
        const res = await fetch(`/api/cases/${currentCase.case_id}/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: action,
                edited_response: (action === 'edit' || action === 'approve') ? editedText : null,
                reviewer_comment: comment
            })
        });

        if (!res.ok) throw new Error(`Approval update failed`);

        const updated = await res.json();
        currentCase = updated;

        if (action === 'approve') {
            lockCaseUI('approved', comment);
            showToast('✓ Reply approved & dispatched to customer channel!');
        } else if (action === 'reject') {
            lockCaseUI('rejected', comment);
            showToast('✕ Draft rejected. Escalated for manual agent drafting.', 'danger');
        } else if (action === 'edit') {
            const pill = document.getElementById('approval-pill');
            pill.textContent = 'CUSTOM EDITED';
            pill.className = 'step-badge badge-outline';
            if (btnApprove) {
                btnApprove.disabled = false;
                btnApprove.innerHTML = '✓ Approve & Dispatch Reply';
            }
            if (btnEdit) btnEdit.disabled = false;
            if (btnReject) btnReject.disabled = false;
            showToast('💾 Custom edits saved! Click "Approve & Dispatch" when ready.');
        }
    } catch (e) {
        alert(e.message);
        if (btnApprove) btnApprove.disabled = false;
        if (btnEdit) btnEdit.disabled = false;
        if (btnReject) btnReject.disabled = false;
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

function switchKBSubTab(subTabId) {
    ['sources', 'products', 'rules'].forEach(id => {
        const btn = document.getElementById(`subtab-${id}-btn`);
        const pane = document.getElementById(`kb-subtab-${id}`);
        if (btn) btn.classList.toggle('active-subtab', id === subTabId);
        if (pane) pane.style.display = (id === subTabId) ? 'block' : 'none';
    });
}

async function renderKBSources() {
    const grid = document.getElementById('kb-sources-grid');
    if (!grid) return;

    try {
        const res = await fetch('/api/knowledge-base');
        if (!res.ok) throw new Error('Failed to load KB data');
        const kbData = await res.json();

        // Update counts
        const srcCountElem = document.getElementById('count-sources');
        const prodCountElem = document.getElementById('count-products');
        if (srcCountElem) srcCountElem.textContent = kbData.sources_count;
        if (prodCountElem) prodCountElem.textContent = kbData.products_count;

        const kbBadge = document.getElementById('kb-badge');
        if (kbBadge) kbBadge.textContent = `KB: ${kbData.sources_count} Sources Loaded`;

        // 1. Render Sources
        const sourcesEntries = Object.entries(kbData.sources || {});
        grid.innerHTML = sourcesEntries.map(([sid, s]) => `
            <div class="kb-card">
                <div class="kb-card-header">
                    <span class="citation-id">${sid}</span>
                    <span class="badge badge-outline">${s.type || 'Official Source'}</span>
                </div>
                <div class="kb-title">${s.title}</div>
                <p style="font-size: 0.8rem; color: #475569; margin-bottom: 0.75rem;">Accessed: ${s.accessed || '2026-10'}</p>
                ${s.url ? `<a href="${s.url}" target="_blank" class="kb-url">${s.url}</a>` : ''}
            </div>
        `).join('');

        // 2. Render Products & Cartridges
        const productsGrid = document.getElementById('kb-products-grid');
        if (productsGrid) {
            const productEntries = Object.entries(kbData.products || {});
            productsGrid.innerHTML = productEntries.map(([pkey, p]) => {
                const isNegative = pkey.includes('PURO_HFS') || pkey.includes('RENO');
                const isUnverified = pkey.includes('KTF_WIDE');
                const badgeClass = isNegative ? 'badge-warning' : (isUnverified ? 'badge-outline' : 'badge-success');
                const badgeLabel = isNegative ? 'Negative Policy / Softener' : (isUnverified ? 'Pending Vendor Confirmation' : 'Verified');

                const factsList = (p.verified_facts || []).map(f => `
                    <li style="margin-bottom: 0.4rem; font-size: 0.82rem; color: #334155;">
                        <strong>${f.id}:</strong> ${f.fact}
                    </li>
                `).join('');

                const aliasesText = (p.aliases || []).join(', ');

                return `
                    <div class="kb-card" style="border-top: 3px solid ${isNegative ? '#eab308' : (isUnverified ? '#f97316' : '#0284c7')}">
                        <div class="kb-card-header">
                            <span class="citation-id" style="font-size: 0.75rem;">${pkey}</span>
                            <span class="badge ${badgeClass}">${badgeLabel}</span>
                        </div>
                        <div class="kb-title" style="font-size: 0.95rem;">${p.name}</div>
                        ${aliasesText ? `<div style="font-size: 0.75rem; color: #64748b; margin-bottom: 0.5rem;"><em>Aliases: ${aliasesText}</em></div>` : ''}
                        ${p.applicability ? `<div style="font-size: 0.75rem; color: #0369a1; margin-bottom: 0.5rem; background: #f0f9ff; padding: 4px 6px; border-radius: 4px;"><strong>Applicability:</strong> ${p.applicability}</div>` : ''}
                        ${p.uncertainty ? `<div style="font-size: 0.75rem; color: #b45309; margin-bottom: 0.5rem; background: #fffbeb; padding: 4px 6px; border-radius: 4px;">⚠️ <strong>Uncertainty:</strong> ${p.uncertainty}</div>` : ''}
                        <ul style="padding-left: 1.2rem; margin: 0.5rem 0;">${factsList}</ul>
                    </div>
                `;
            }).join('');
        }

        // 3. Render Guardrails & Negative Rules
        const rulesList = document.getElementById('kb-rules-list');
        if (rulesList) {
            rulesList.innerHTML = (kbData.guardrails || []).map((rule, idx) => `
                <li style="padding: 0.6rem 0; border-bottom: 1px solid #f1f5f9; font-size: 0.85rem; color: #1e293b; display: flex; align-items: flex-start; gap: 0.5rem;">
                    <span style="color: #ef4444; font-weight: bold;">🛡️</span>
                    <span>${rule}</span>
                </li>
            `).join('');
        }

    } catch (e) {
        console.error('Failed to render dynamic KB sources:', e);
    }
}

// ============================================================================
// Phase 4: Support Operations Dashboard & Human Escalation Inbox
// ============================================================================

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

let currentEscalationFilter = 'open';
let activeTicketId = null;
let activeTicketConvId = null;

async function loadOperationsDashboard() {
    try {
        const res = await fetch('/api/v2/dashboard/metrics');
        if (!res.ok) throw new Error('Failed to fetch dashboard metrics');
        const m = await res.json();

        // 1. Update KPI numbers
        const totalMsgsEl = document.getElementById('ops-total-msgs');
        if (totalMsgsEl) totalMsgsEl.textContent = m.total_incoming_messages;

        const activeConvsEl = document.getElementById('ops-active-convs');
        if (activeConvsEl) activeConvsEl.textContent = `${m.active_conversations} Active Convs`;

        const resRateEl = document.getElementById('ops-res-rate');
        if (resRateEl) resRateEl.textContent = `${m.resolution_rate_percent}%`;

        const autoResEl = document.getElementById('ops-auto-resolved');
        if (autoResEl) autoResEl.textContent = `${m.automatically_resolved_conversations} Resolved`;

        const openTckEl = document.getElementById('ops-open-tickets');
        if (openTckEl) openTckEl.textContent = m.open_escalation_tickets;

        const awaitingReplyEl = document.getElementById('ops-awaiting-reply');
        if (awaitingReplyEl) awaitingReplyEl.textContent = `${m.conversations_awaiting_customer_replies} Awaiting Reply`;

        const qDepthEl = document.getElementById('ops-queue-depth');
        if (qDepthEl) qDepthEl.textContent = m.messages_awaiting_processing;

        const failedJobsEl = document.getElementById('ops-failed-jobs');
        if (failedJobsEl) failedJobsEl.textContent = `${m.failed_processing_jobs} Failed DLQ`;

        const latencyEl = document.getElementById('ops-latency');
        if (latencyEl) latencyEl.textContent = `${Math.round(m.average_response_time_ms)}ms`;

        const p95LatencyEl = document.getElementById('ops-p95-latency');
        if (p95LatencyEl) p95LatencyEl.textContent = `p95: ${Math.round(m.p95_latency_ms)}ms`;

        const workersEl = document.getElementById('ops-workers');
        if (workersEl) workersEl.textContent = `${m.active_workers} / ${m.configured_concurrency}`;

        // 2. Update Emergency Pause Badge & Button
        const pauseBadge = document.getElementById('pause-status-badge');
        const pauseBtn = document.getElementById('btn-toggle-pause');
        if (pauseBadge && pauseBtn) {
            if (m.emergency_pause_active) {
                pauseBadge.className = 'badge badge-danger';
                pauseBadge.textContent = '🔴 Automation Paused';
                pauseBtn.className = 'btn btn-success';
                pauseBtn.textContent = '▶ Resume Automation';
            } else {
                pauseBadge.className = 'badge badge-success';
                pauseBadge.textContent = '🟢 Automation Running';
                pauseBtn.className = 'btn btn-outline';
                pauseBtn.textContent = '🛑 Emergency Pause';
            }
        }

        // 3. Update Category Checkboxes
        const allowedCats = m.allowed_auto_categories || [];
        ['compatibility', 'cartridge_selection', 'delivery_tracking', 'washing_machine_compatibility', 'cartridge_life'].forEach(cat => {
            const el = document.getElementById(`cat-${cat}`);
            if (el) el.checked = allowedCats.includes(cat);
        });

        // 4. Load Tickets
        await loadEscalationTickets(currentEscalationFilter);

    } catch (e) {
        console.error('Error loading operations dashboard:', e);
    }
}

async function toggleEmergencyPause() {
    try {
        const badge = document.getElementById('pause-status-badge');
        const isPaused = badge && badge.textContent.includes('Paused');
        const newPauseState = !isPaused;

        const res = await fetch('/api/v2/dashboard/controls', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ emergency_pause: newPauseState })
        });

        if (res.ok) {
            showToast(newPauseState ? 'Emergency pause activated. Outbound auto-dispatch suspended.' : 'Automation resumed. Normal processing restored.');
            await loadOperationsDashboard();
        }
    } catch (e) {
        alert('Failed to toggle emergency pause: ' + e.message);
    }
}

async function saveCategoryControls() {
    try {
        const cats = [];
        ['compatibility', 'cartridge_selection', 'delivery_tracking', 'washing_machine_compatibility', 'cartridge_life'].forEach(c => {
            const el = document.getElementById(`cat-${c}`);
            if (el && el.checked) cats.push(c);
        });

        const res = await fetch('/api/v2/dashboard/controls', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ allowed_categories: cats })
        });

        if (res.ok) {
            showToast('Auto-resolution categories updated successfully.');
        }
    } catch (e) {
        console.error('Failed to update category controls:', e);
    }
}

async function loadEscalationTickets(filter = null) {
    if (filter) {
        currentEscalationFilter = filter;
        ['all', 'open', 'assigned', 'resolved'].forEach(f => {
            const btn = document.getElementById(`filter-${f}-btn`);
            if (btn) {
                if (f === filter) btn.classList.add('active-subtab');
                else btn.classList.remove('active-subtab');
            }
        });
    }

    const tbody = document.getElementById('tickets-table-body');
    if (!tbody) return;

    try {
        const url = currentEscalationFilter === 'all' ? '/api/v2/tickets' : `/api/v2/tickets?status_filter=${currentEscalationFilter}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error('Failed to fetch tickets');
        const tickets = await res.json();

        if (tickets.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center" style="padding: 2rem; color: #64748b;">No ${currentEscalationFilter} escalation tickets found. All cases running smoothly.</td></tr>`;
            return;
        }

        tbody.innerHTML = tickets.map(t => {
            const priorityClass = t.priority === 'urgent' ? 'badge-danger' : (t.priority === 'high' ? 'badge-warning' : 'badge-info');
            const statusClass = t.status === 'resolved' ? 'badge-success' : (t.status === 'assigned' ? 'badge-warning' : 'badge-danger');
            const shortMsg = (t.customer_message || '').slice(0, 45) + '...';
            const shortReason = (t.escalation_reason || '').slice(0, 40) + '...';

            return `
                <tr>
                    <td><code>${t.ticket_id}</code></td>
                    <td><span class="badge ${priorityClass}">${t.priority.toUpperCase()}</span></td>
                    <td><span style="font-size: 0.85rem; font-weight: 500;">${t.category}</span></td>
                    <td title="${escapeHtml(t.customer_message || '')}">${escapeHtml(shortMsg)}</td>
                    <td title="${escapeHtml(t.escalation_reason || '')}" style="color: #991B1B; font-size: 0.82rem;">${escapeHtml(shortReason)}</td>
                    <td>${t.assigned_to ? `<strong>${t.assigned_to}</strong>` : '<span style="color:#94a3b8;">Unassigned</span>'}</td>
                    <td><span class="badge ${statusClass}">${t.status}</span></td>
                    <td>
                        <div style="display: flex; gap: 0.25rem;">
                            <button class="btn btn-outline btn-sm" onclick="viewTicketContext('${t.conversation_id}', '${t.ticket_id}')">View</button>
                            ${t.status === 'open' ? `<button class="btn btn-outline btn-sm" onclick="assignTicket('${t.ticket_id}')">Assign</button>` : ''}
                            ${t.status !== 'resolved' ? `<button class="btn btn-success btn-sm" onclick="quickResolveTicket('${t.ticket_id}')">Resolve</button>` : ''}
                        </div>
                    </td>
                </tr>
            `;
        }).join('');

    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center" style="color: #ef4444;">Error loading tickets: ${e.message}</td></tr>`;
    }
}

async function assignTicket(ticketId) {
    const agent = prompt('Enter support agent name to assign:', 'Agent Rajesh') || 'Agent Rajesh';
    try {
        const res = await fetch(`/api/v2/tickets/${ticketId}/action?action=assign&assigned_to=${encodeURIComponent(agent)}`, {
            method: 'POST'
        });
        if (res.ok) {
            showToast(`Ticket ${ticketId} assigned to ${agent}.`);
            await loadOperationsDashboard();
        }
    } catch (e) {
        alert('Failed to assign ticket: ' + e.message);
    }
}

async function quickResolveTicket(ticketId) {
    const note = prompt('Optional resolution note / customer closure summary:', 'Verified and resolved with customer') || 'Resolved by support agent';
    try {
        const res = await fetch(`/api/v2/tickets/${ticketId}/action?action=resolve&note=${encodeURIComponent(note)}`, {
            method: 'POST'
        });
        if (res.ok) {
            showToast(`Ticket ${ticketId} marked as resolved.`);
            await loadOperationsDashboard();
        }
    } catch (e) {
        alert('Failed to resolve ticket: ' + e.message);
    }
}

async function triggerBulkResolve() {
    if (!confirm('Resolve all open escalation tickets with AI recommended guidance?')) return;
    try {
        const res = await fetch('/api/v2/dashboard/bulk-action?action=resolve_all_open', { method: 'POST' });
        if (res.ok) {
            const data = await res.json();
            showToast(`Bulk resolved ${data.affected_tickets} open tickets.`);
            await loadOperationsDashboard();
        }
    } catch (e) {
        alert('Bulk resolve failed: ' + e.message);
    }
}

async function triggerClearSimulation() {
    if (!confirm('Clear all synthetic simulation test data from the dashboard?')) return;
    try {
        const res = await fetch('/api/v2/dashboard/bulk-action?action=clear_simulation_data', { method: 'POST' });
        if (res.ok) {
            const data = await res.json();
            showToast(`Cleared ${data.cleared_messages} simulation messages and ${data.cleared_tickets} test tickets.`);
            await loadOperationsDashboard();
        }
    } catch (e) {
        alert('Clear failed: ' + e.message);
    }
}

async function viewTicketContext(conversationId, ticketId) {
    activeTicketId = ticketId;
    activeTicketConvId = conversationId;

    const modal = document.getElementById('ticket-conv-modal');
    const container = document.getElementById('ticket-conv-messages');
    const title = document.getElementById('ticket-conv-title');
    if (!modal || !container) return;

    if (title) title.textContent = `Escalation Thread: ${ticketId} (Conversation: ${conversationId})`;
    container.innerHTML = '<div style="text-align: center; color: #64748b;">Loading conversation history...</div>';
    modal.classList.add('active');

    try {
        const res = await fetch(`/api/v2/conversations/${conversationId}`);
        if (!res.ok) throw new Error('Conversation not found');
        const data = await res.json();

        container.innerHTML = (data.messages || []).map(m => {
            const isCustomer = m.role === 'customer';
            return `
                <div style="align-self: ${isCustomer ? 'flex-start' : 'flex-end'}; max-width: 80%; background: ${isCustomer ? '#F1F5F9' : '#E6F7FA'}; border: 1px solid ${isCustomer ? '#CBD5E1' : '#BCE3EB'}; border-radius: 8px; padding: 0.6rem 0.8rem;">
                    <div style="font-size: 0.72rem; font-weight: 700; color: ${isCustomer ? '#475569' : '#006D82'}; margin-bottom: 0.2rem;">
                        ${isCustomer ? '👤 Customer' : '💧 WaterScience Support / AI'}
                    </div>
                    <div style="font-size: 0.88rem; color: #0F172A; white-space: pre-wrap;">${escapeHtml(m.content)}</div>
                    <div style="font-size: 0.68rem; color: #94A3B8; text-align: right; margin-top: 0.2rem;">${m.timestamp || ''}</div>
                </div>
            `;
        }).join('');

    } catch (e) {
        container.innerHTML = `<div style="color: #ef4444;">Error loading conversation: ${e.message}</div>`;
    }
}

function closeTicketModal() {
    const modal = document.getElementById('ticket-conv-modal');
    if (modal) modal.classList.remove('active');
    activeTicketId = null;
    activeTicketConvId = null;
}

async function resolveCurrentTicket() {
    if (!activeTicketId) return;
    const replyText = document.getElementById('ticket-reply-text').value.trim() || 'Resolved with customer';

    try {
        const res = await fetch(`/api/v2/tickets/${activeTicketId}/action?action=resolve&note=${encodeURIComponent(replyText)}`, {
            method: 'POST'
        });
        if (res.ok) {
            showToast(`Ticket ${activeTicketId} successfully resolved.`);
            closeTicketModal();
            await loadOperationsDashboard();
        }
    } catch (e) {
        alert('Failed to resolve ticket: ' + e.message);
    }
}

// ============================================================================
// Phase 3 & 4: URL Knowledge Management & Sync Functions
// ============================================================================

async function checkKBDraftVersion() {
    try {
        const res = await fetch('/api/v2/knowledge/versions');
        if (!res.ok) return;
        const versions = await res.json();

        const published = versions.find(v => v.status === 'published');
        const draft = versions.find(v => v.status === 'draft');

        const vInfoEl = document.getElementById('kb-version-info');
        if (vInfoEl && published) {
            vInfoEl.textContent = `Active Version: v${published.version_number}.0 • ${published.sources_count || 14} Official Verified Sources • Crawl Schedule: Daily`;
        }

        const draftBanner = document.getElementById('draft-publish-banner');
        if (draftBanner) {
            if (draft) {
                draftBanner.style.display = 'block';
                document.getElementById('draft-banner-title').textContent = `Version ${draft.version_number}.0 (Draft) ready for publication`;
                document.getElementById('draft-banner-desc').textContent = draft.summary || 'Updated facts and changes detected across sources.';
            } else {
                draftBanner.style.display = 'none';
            }
        }
    } catch (e) {
        console.error('Failed to check KB versions:', e);
    }
}

async function triggerKBCrawl() {
    const btn = document.getElementById('btn-sync-kb');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span>⏳ Crawling 14 Sources...</span>';
    }

    try {
        const res = await fetch('/api/v2/knowledge/crawl', { method: 'POST' });
        if (!res.ok) throw new Error('Crawl failed');
        const data = await res.json();

        showToast(`Sync complete: ${data.total_sources} sources scanned (${data.unchanged} unchanged, ${data.modified} modified).`);
        await checkKBDraftVersion();
        renderKBSources();
    } catch (e) {
        alert('Knowledge Base crawl failed: ' + e.message);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<span>🔄 Update Knowledge Base</span>';
        }
    }
}

async function publishStagedDraft() {
    try {
        const vRes = await fetch('/api/v2/knowledge/versions');
        const versions = await vRes.json();
        const draft = versions.find(v => v.status === 'draft');
        if (!draft) {
            alert('No draft version currently staged.');
            return;
        }

        const res = await fetch('/api/v2/knowledge/publish', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ version_number: draft.version_number })
        });

        if (res.ok) {
            showToast(`Version ${draft.version_number}.0 successfully published to Live AI!`);
            await checkKBDraftVersion();
            renderKBSources();
        }
    } catch (e) {
        alert('Failed to publish draft version: ' + e.message);
    }
}

async function rollbackDraft() {
    if (!confirm('Are you sure you want to rollback to the previous published version?')) return;
    try {
        const res = await fetch('/api/v2/knowledge/rollback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_version_number: 1 })
        });

        if (res.ok) {
            showToast('Knowledge Base rolled back to Version 1.0.');
            await checkKBDraftVersion();
            renderKBSources();
        }
    } catch (e) {
        alert('Rollback failed: ' + e.message);
    }
}

function openAddSourceModal() {
    const m = document.getElementById('add-source-modal');
    if (m) m.classList.add('active');
}

function closeAddSourceModal() {
    const m = document.getElementById('add-source-modal');
    if (m) m.classList.remove('active');
}

async function submitAddSource() {
    const url = document.getElementById('new-source-url').value.trim();
    const title = document.getElementById('new-source-title').value.trim();
    const type = document.getElementById('new-source-type').value;

    if (!url || !title) {
        alert('Please enter both source URL and title.');
        return;
    }

    try {
        const res = await fetch('/api/v2/knowledge/sources', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                source_id: 'S' + Math.floor(100 + Math.random() * 900),
                url: url,
                title: title,
                source_type: type
            })
        });

        if (res.ok) {
            showToast(`Added source "${title}". Automatically triggering crawl.`);
            closeAddSourceModal();
            await triggerKBCrawl();
        } else {
            const err = await res.json();
            alert('Failed to add source: ' + (err.detail || res.statusText));
        }
    } catch (e) {
        alert('Error adding source: ' + e.message);
    }
}

// ============================================================================
// Phase 5: Scale and Performance Simulator Client
// ============================================================================

let simPollInterval = null;

async function refreshSimulatorStatus() {
    try {
        const res = await fetch('/api/v2/simulator/status');
        if (res.ok) {
            const data = await res.json();
            updateSimulatorUI(data);
        }
    } catch (e) {
        // Simulator endpoint might be starting
    }
}

async function startScaleSimulation() {
    const volume = parseInt(document.getElementById('sim-volume').value, 10);
    const profile = document.getElementById('sim-profile').value;
    const concurrency = parseInt(document.getElementById('sim-concurrency').value, 10);

    const btn = document.getElementById('btn-start-sim');
    btn.disabled = true;
    btn.innerHTML = '<span>⏳ Running Simulator...</span>';

    const progBlock = document.getElementById('sim-progress-block');
    if (progBlock) progBlock.style.display = 'block';

    try {
        const res = await fetch('/api/v2/simulator/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                total_messages: volume,
                profile: profile,
                concurrency: concurrency
            })
        });

        if (!res.ok) throw new Error('Failed to start simulation');
        showToast(`Started load test for ${volume} messages (${profile} profile, ${concurrency} workers)...`);

        if (simPollInterval) clearInterval(simPollInterval);
        simPollInterval = setInterval(pollSimulatorProgress, 600);

    } catch (e) {
        alert('Failed to start load test: ' + e.message);
        btn.disabled = false;
        btn.innerHTML = '<span>⚡ Start Load Test</span>';
    }
}

async function pollSimulatorProgress() {
    try {
        const res = await fetch('/api/v2/simulator/status');
        if (!res.ok) return;
        const data = await res.json();
        updateSimulatorUI(data);

        if (data.status === 'completed' || data.status === 'idle') {
            clearInterval(simPollInterval);
            simPollInterval = null;
            const btn = document.getElementById('btn-start-sim');
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<span>⚡ Start Load Test</span>';
            }
            showToast(`Scale simulation completed! Processed ${data.total_processed} messages.`);
            updateBenchmarkMatrix(data);
        }
    } catch (e) {
        console.error('Error polling simulator:', e);
    }
}

function updateSimulatorUI(data) {
    const badge = document.getElementById('sim-status-badge');
    if (badge) {
        badge.textContent = data.status === 'running' ? '⚡ Simulating Load...' : 'Simulator Ready';
        badge.className = data.status === 'running' ? 'step-badge' : 'step-badge';
    }

    const pct = data.progress_percent || 0;
    const bar = document.getElementById('sim-progress-bar');
    const pctLabel = document.getElementById('sim-progress-percent');
    if (bar) bar.style.width = `${pct}%`;
    if (pctLabel) pctLabel.textContent = `${pct}%`;

    const ingestedEl = document.getElementById('sim-ingested');
    if (ingestedEl) ingestedEl.textContent = data.total_ingested || 0;

    const processedEl = document.getElementById('sim-processed');
    if (processedEl) processedEl.textContent = data.total_processed || 0;

    const tputEl = document.getElementById('sim-throughput');
    if (tputEl) tputEl.textContent = `${Math.round(data.throughput_msgs_sec || 0)} msg/s`;

    const p95El = document.getElementById('sim-latency-p95');
    if (p95El) p95El.textContent = `${Math.round(data.p95_latency_ms || 0)}ms`;

    const errEl = document.getElementById('sim-error-rate');
    if (errEl) errEl.textContent = `${(data.error_rate_percent || 0).toFixed(2)}%`;
}

function updateBenchmarkMatrix(data) {
    // 1. Volume
    const volObs = document.getElementById('target-volume-res');
    const volStatus = document.getElementById('target-volume-status');
    if (volObs && volStatus) {
        volObs.textContent = `${data.total_processed} messages`;
        const pass = (data.total_processed >= 2000) || (data.total_processed >= data.total_ingested);
        volStatus.innerHTML = `<span class="badge ${pass ? 'badge-success' : 'badge-danger'}">${pass ? 'PASSED' : 'FAILED'}</span>`;
    }

    // 2. Throughput
    const tputObs = document.getElementById('target-throughput-res');
    const tputStatus = document.getElementById('target-throughput-status');
    if (tputObs && tputStatus) {
        tputObs.textContent = `${Math.round(data.throughput_msgs_sec)} msgs/sec`;
        const pass = data.throughput_msgs_sec >= 45.0; // target 50+
        tputStatus.innerHTML = `<span class="badge ${pass ? 'badge-success' : 'badge-danger'}">${pass ? 'PASSED' : 'CHECK'}</span>`;
    }

    // 3. Latency
    const latObs = document.getElementById('target-latency-res');
    const latStatus = document.getElementById('target-latency-status');
    if (latObs && latStatus) {
        latObs.textContent = `${Math.round(data.p95_latency_ms)}ms`;
        const pass = data.p95_latency_ms < 2000.0; // < 2s
        latStatus.innerHTML = `<span class="badge ${pass ? 'badge-success' : 'badge-danger'}">${pass ? 'PASSED' : 'FAILED'}</span>`;
    }

    // 4. Error Rate
    const errObs = document.getElementById('target-error-res');
    const errStatus = document.getElementById('target-error-status');
    if (errObs && errStatus) {
        errObs.textContent = `${(data.error_rate_percent || 0).toFixed(2)}%`;
        const pass = data.error_rate_percent < 0.5;
        errStatus.innerHTML = `<span class="badge ${pass ? 'badge-success' : 'badge-danger'}">${pass ? 'PASSED' : 'FAILED'}</span>`;
    }

    // 5. Message Loss
    const lossObs = document.getElementById('target-loss-res');
    const lossStatus = document.getElementById('target-loss-status');
    if (lossObs && lossStatus) {
        const lost = (data.total_ingested || 0) - (data.total_processed || 0);
        lossObs.textContent = `${lost} messages`;
        const pass = lost === 0;
        lossStatus.innerHTML = `<span class="badge ${pass ? 'badge-success' : 'badge-danger'}">${pass ? 'PASSED' : 'FAILED'}</span>`;
    }
}
