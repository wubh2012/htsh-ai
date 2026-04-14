const API_BASE = '/api';

let currentResultId = null;
let ruleList = [];
let historyList = [];

// ========== Navigation ==========
function switchPage(pageName) {
    document.querySelectorAll('.page-section').forEach(section => {
        section.classList.remove('active');
    });

    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });

    document.getElementById(`page-${pageName}`).classList.add('active');
    document.querySelector(`.nav-item[data-page="${pageName}"]`).classList.add('active');

    if (pageName === 'upload') {
        loadHistory();
    } else if (pageName === 'rules') {
        loadRules();
    } else if (pageName === 'results') {
        loadHistory();
    }
}

// ========== Init ==========
document.addEventListener('DOMContentLoaded', () => {
    loadRules();
    loadHistory();
    setupUpload();
    setupNavigation();
});

function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            const page = item.dataset.page;
            switchPage(page);
        });
    });
}

// ========== Upload ==========
function setupUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    if (!uploadArea || !fileInput) return;

    uploadArea.addEventListener('click', () => fileInput.click());

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            uploadFile(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadFile(e.target.files[0]);
        }
    });
}

async function uploadFile(file) {
    const uploadProgress = document.getElementById('uploadProgress');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');

    uploadProgress.classList.add('active');
    progressFill.style.width = '30%';
    progressText.textContent = '正在上传文件...';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '上传失败');
        }

        progressFill.style.width = '100%';
        progressText.textContent = '上传完成！';

        const data = await response.json();
        showToast('上传成功，请点击"AI审核"发起审核', 'success');
        currentResultId = data.result_id;

        setTimeout(() => {
            uploadProgress.classList.remove('active');
            progressFill.style.width = '0%';
        }, 1000);

        await loadAuditDetail(data.result_id);
        switchPage('results');

    } catch (error) {
        showToast(error.message, 'error');
        uploadProgress.classList.remove('active');
        progressFill.style.width = '0%';
    }
}

async function startAudit(resultId) {
    try {
        const response = await fetch(`${API_BASE}/audit/${resultId}`, {
            method: 'POST'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '审核失败');
        }

        const data = await response.json();
        showToast('AI审核完成', 'success');
        displayResult(data);

    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function triggerAuditFromButton() {
    if (!currentResultId) return;
    const btn = document.getElementById('btnAudit');
    btn.disabled = true;
    btn.textContent = '审核中...';
    await startAudit(currentResultId);
    btn.disabled = false;
    btn.textContent = '🤖 AI审核';
}

// ========== Display Result ==========
function displayResult(data) {
    const noResult = document.getElementById('noResult');
    const resultDetail = document.getElementById('resultDetail');

    if (!noResult || !resultDetail) return;

    noResult.style.display = 'none';
    resultDetail.classList.add('active');

    document.getElementById('contractName').textContent = data.contract_name;
    document.getElementById('contractMeta').textContent = (data.file_type || '').toUpperCase();

    const statusBadge = document.getElementById('auditStatusBadge');
    statusBadge.textContent = getStatusText(data.audit_status);
    statusBadge.className = `badge badge-${data.audit_status.toLowerCase()}`;

    // 显示操作按钮区域
    const resultActions = document.getElementById('resultActions');
    resultActions.style.display = 'flex';

    const btnAudit = document.getElementById('btnAudit');
    const btnApprove = document.getElementById('btnApprove');
    const btnReject = document.getElementById('btnReject');

    const hasAiResult = !!data.ai_result;
    // AI审核按钮：有结果时隐藏（通过/驳回操作完之后不需要重审）
    btnAudit.style.display = (data.audit_status === 'PENDING') ? '' : 'none';
    btnApprove.style.display = hasAiResult ? '' : 'none';
    btnReject.style.display = hasAiResult ? '' : 'none';

    const conclusionBox = document.getElementById('conclusionBox');
    const conclusionTitle = document.getElementById('aiConclusion');

    if (!hasAiResult) {
        conclusionBox.className = 'conclusion-box review';
        conclusionTitle.textContent = '⏳ 待AI审核';
        document.getElementById('aiSummary').textContent = '请点击右上角"AI审核"按钮发起智能审核';
        document.getElementById('riskList').innerHTML = `
            <div class="risk-item" style="text-align: center; padding: 32px;">
                <div style="font-size: 32px; margin-bottom: 12px;">🤖</div>
                <div style="color: var(--text-muted)">暂无审核结果</div>
            </div>
        `;
        return;
    }

    conclusionBox.className = `conclusion-box ${getConclusionClass(data.ai_conclusion)}`;
    conclusionTitle.textContent = getConclusionText(data.ai_conclusion);
    document.getElementById('aiSummary').textContent = data.ai_result?.summary || '';

    const riskList = document.getElementById('riskList');
    riskList.innerHTML = '';

    const riskPoints = (data.ai_result?.risk_points || []).sort((a, b) => (b.risk_level || 0) - (a.risk_level || 0));
    if (riskPoints.length === 0) {
        riskList.innerHTML = `
            <div class="risk-item" style="text-align: center; padding: 32px;">
                <div style="font-size: 32px; margin-bottom: 12px;">✅</div>
                <div style="color: var(--success); font-weight: 500;">未发现风险点</div>
            </div>
        `;
    } else {
        riskPoints.forEach(rp => {
            const item = document.createElement('div');
            item.className = 'risk-item';
            item.innerHTML = `
                <div class="risk-header">
                    <span class="risk-title">${rp.rule_name || '风险点'}</span>
                    <span class="risk-badge risk-${getRiskClass(rp.risk_level)}">风险 ${rp.risk_level}</span>
                </div>
                <p class="risk-description">${rp.description}</p>
                ${rp.suggestion ? `<div class="risk-suggestion">${rp.suggestion}</div>` : ''}
            `;
            riskList.appendChild(item);
        });
    }
}

// ========== Review ==========
async function approveAudit() {
    if (!currentResultId) return;
    const comment = document.getElementById('auditorComment').value;

    try {
        const response = await fetch(`${API_BASE}/audit/${currentResultId}/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ auditor_comment: comment })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '操作失败');
        }

        showToast('审核已通过', 'success');
        loadHistory();
        await loadAuditDetail(currentResultId);

    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function rejectAudit() {
    if (!currentResultId) return;
    const comment = document.getElementById('auditorComment').value;

    try {
        const response = await fetch(`${API_BASE}/audit/${currentResultId}/reject`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ auditor_comment: comment })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '操作失败');
        }

        showToast('审核已驳回', 'success');
        loadHistory();
        await loadAuditDetail(currentResultId);

    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function loadAuditDetail(resultId) {
    try {
        const response = await fetch(`${API_BASE}/audit/${resultId}`);
        const data = await response.json();
        displayResult(data);
    } catch (error) {
        showToast('加载详情失败', 'error');
    }
}

// ========== Rules ==========
async function loadRules() {
    try {
        const response = await fetch(`${API_BASE}/rules`);
        ruleList = await response.json();
        renderRules();
    } catch (error) {
        showToast('加载规则失败', 'error');
    }
}

function renderRules() {
    const container = document.getElementById('ruleList');
    if (!container) return;

    if (ruleList.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📜</div>
                <p class="empty-state-text">暂无审核规则</p>
            </div>
        `;
        return;
    }

    container.innerHTML = '';
    ruleList.forEach((rule, idx) => {
        const riskClass = rule.risk_level >= 4 ? 'risk-high' : (rule.risk_level >= 3 ? 'risk-medium' : 'risk-low');
        const riskLabel = rule.risk_level >= 4 ? '高' : (rule.risk_level >= 3 ? '中' : '低');
        const typeLabel = rule.rule_type === 'CHECK_MISSING' ? '条款缺失' : '风险关键词';

        const card = document.createElement('div');
        card.className = `rule-card ${riskClass} ${rule.enabled ? '' : 'disabled'}`;
        card.dataset.ruleId = rule.id;

        card.innerHTML = `
            <div class="rule-card-accent ${riskClass}"></div>
            <div class="rule-card-num">${String(idx + 1).padStart(2, '0')}</div>
            <div class="rule-card-body">
                <div class="rule-card-name">${rule.rule_name}</div>
                <div class="rule-card-meta">
                    <span class="rule-badge rule-badge-type">${typeLabel}</span>
                    <span class="rule-badge rule-badge-risk ${riskClass}">风险 ${riskLabel}</span>
                </div>
                <div class="rule-card-expand-hint">
                    <svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M2 3.5L5 6.5L8 3.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
                    点击查看详情
                </div>
            </div>
            <div class="rule-card-detail">
                <div class="rule-card-detail-inner">
                    <div class="rule-detail-label">检查内容</div>
                    <div class="rule-detail-check-content">${rule.check_content}</div>
                    ${rule.suggestion ? `
                        <div class="rule-detail-label">修改建议</div>
                        <div class="rule-detail-suggestion">${rule.suggestion}</div>
                    ` : ''}
                </div>
            </div>
            <div class="rule-card-footer">
                <div class="rule-toggle ${rule.enabled ? 'active' : ''}" onclick="event.stopPropagation(); toggleRule(${rule.id})"></div>
                <div class="rule-actions">
                    <button class="rule-icon-btn edit" onclick="event.stopPropagation(); editRule(${rule.id})" title="编辑">✎</button>
                    <button class="rule-icon-btn delete" onclick="event.stopPropagation(); deleteRule(${rule.id})" title="删除">✕</button>
                </div>
            </div>
        `;

        // Toggle expand on card click (not on toggle/edit/delete clicks)
        card.addEventListener('click', (e) => {
            if (e.target.closest('.rule-toggle') || e.target.closest('.rule-actions')) return;
            card.classList.toggle('expanded');
        });

        container.appendChild(card);
    });
}

async function toggleRule(ruleId) {
    try {
        const response = await fetch(`${API_BASE}/rules/${ruleId}/toggle`, { method: 'PATCH' });
        if (!response.ok) throw new Error('操作失败');
        loadRules();
    } catch (error) {
        showToast('切换失败', 'error');
    }
}

function openRuleModal(rule = null) {
    const modal = document.getElementById('ruleModal');
    if (!modal) return;

    modal.classList.add('active');
    document.getElementById('ruleModalTitle').textContent = rule ? '编辑规则' : '添加规则';

    if (rule) {
        document.getElementById('ruleId').value = rule.id;
        document.getElementById('ruleName').value = rule.rule_name;
        document.getElementById('ruleType').value = rule.rule_type;
        document.getElementById('checkContent').value = rule.check_content;
        document.getElementById('riskLevel').value = rule.risk_level;
        document.getElementById('suggestion').value = rule.suggestion || '';
    } else {
        document.getElementById('ruleForm').reset();
        document.getElementById('ruleId').value = '';
    }
}

function closeRuleModal() {
    const modal = document.getElementById('ruleModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

function editRule(ruleId) {
    const rule = ruleList.find(r => r.id === ruleId);
    if (rule) openRuleModal(rule);
}

document.addEventListener('DOMContentLoaded', () => {
    const ruleForm = document.getElementById('ruleForm');
    if (ruleForm) {
        ruleForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const ruleId = document.getElementById('ruleId').value;
            const data = {
                rule_name: document.getElementById('ruleName').value,
                rule_type: document.getElementById('ruleType').value,
                check_content: document.getElementById('checkContent').value,
                risk_level: parseInt(document.getElementById('riskLevel').value),
                suggestion: document.getElementById('suggestion').value || null
            };

            try {
                const url = ruleId ? `${API_BASE}/rules/${ruleId}` : `${API_BASE}/rules`;
                const method = ruleId ? 'PUT' : 'POST';

                const response = await fetch(url, {
                    method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                if (!response.ok) throw new Error('保存失败');

                showToast('保存成功', 'success');
                closeRuleModal();
                loadRules();

            } catch (error) {
                showToast(error.message, 'error');
            }
        });
    }
});

async function deleteRule(ruleId) {
    if (!confirm('确定要删除这条规则吗？')) return;

    try {
        const response = await fetch(`${API_BASE}/rules/${ruleId}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('删除失败');
        showToast('删除成功', 'success');
        loadRules();
    } catch (error) {
        showToast('删除失败', 'error');
    }
}

// ========== History ==========
async function loadHistory() {
    try {
        const response = await fetch(`${API_BASE}/audit/list`);
        historyList = await response.json();
        renderHistory();
        renderHistoryUpload();
    } catch (error) {
        showToast('加载历史失败', 'error');
    }
}

function createHistoryItem(item) {
    const div = document.createElement('div');
    div.className = 'history-item';
    div.onclick = (e) => {
        if (e.target.closest('.btn-delete')) return;
        currentResultId = item.id;
        loadAuditDetail(item.id);
        switchPage('results');
    };
    div.innerHTML = `
        <div class="history-icon">📄</div>
        <div class="history-info">
            <div class="history-name">${item.contract_name}</div>
            <div class="history-meta">${item.file_type.toUpperCase()} · ${formatDate(item.create_time)}</div>
        </div>
        <span class="badge badge-${item.audit_status.toLowerCase()}">${getStatusText(item.audit_status)}</span>
        <button class="btn btn-danger btn-sm btn-delete" onclick="deleteHistory(${item.id})" title="删除">🗑</button>
    `;
    return div;
}

function renderHistory() {
    const container = document.getElementById('historyList');
    if (!container) return;

    container.innerHTML = '';
    if (historyList.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📁</div>
                <p class="empty-state-text">暂无审核记录</p>
            </div>
        `;
        return;
    }

    historyList.forEach(item => {
        container.appendChild(createHistoryItem(item));
    });
}

function renderHistoryUpload() {
    const container = document.getElementById('historyListUpload');
    if (!container) return;

    container.innerHTML = '';
    if (historyList.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📁</div>
                <p class="empty-state-text">暂无上传记录</p>
            </div>
        `;
        return;
    }

    historyList.slice(0, 5).forEach(item => {
        container.appendChild(createHistoryItem(item));
    });
}

// ========== Delete History ==========
async function deleteHistory(resultId) {
    if (!confirm('确定要删除这条审核记录吗？')) return;

    try {
        const response = await fetch(`${API_BASE}/audit/${resultId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '删除失败');
        }

        showToast('删除成功', 'success');
        loadHistory();

        // 如果删除的是当前查看的记录，清空详情
        if (currentResultId === resultId) {
            currentResultId = null;
            document.getElementById('noResult').style.display = 'block';
            document.getElementById('resultDetail').classList.remove('active');
            document.getElementById('resultActions').style.display = 'none';
        }

    } catch (error) {
        showToast(error.message, 'error');
    }
}

// ========== Helpers ==========
function getStatusText(status) {
    const map = {
        'PENDING': '待审核',
        'APPROVED': '已通过',
        'REJECTED': '已驳回'
    };
    return map[status] || status;
}

function getConclusionText(conclusion) {
    const map = {
        'PASS': '✓ 审核通过',
        'FAIL': '✗ 审核未通过',
        'REVIEW': '⚠ 需要人工复核'
    };
    return map[conclusion] || conclusion;
}

function getConclusionClass(conclusion) {
    const map = {
        'PASS': 'pass',
        'FAIL': 'fail',
        'REVIEW': 'review'
    };
    return map[conclusion] || 'review';
}

function getRiskClass(level) {
    if (level >= 4) return 'high';
    if (level >= 3) return 'medium';
    return 'low';
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    if (!toast) return;

    const icon = toast.querySelector('.toast-icon');
    const msg = toast.querySelector('.toast-message');

    icon.textContent = type === 'success' ? '✓' : '✗';
    msg.textContent = message;
    toast.className = `toast ${type} show`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}
