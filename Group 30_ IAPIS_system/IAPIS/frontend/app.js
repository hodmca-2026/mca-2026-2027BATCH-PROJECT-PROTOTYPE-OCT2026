// ============================================================
// IAPIS Frontend — Application Logic
// ============================================================

const API_BASE = window.location.origin;

// DOM Elements
const searchInput = document.getElementById('search-input');
const searchBtn = document.getElementById('search-btn');
const topKSelect = document.getElementById('top-k-select');
const alphaSlider = document.getElementById('alpha-slider');
const alphaValue = document.getElementById('alpha-value');
const loadingState = document.getElementById('loading-state');
const resultsContainer = document.getElementById('results-container');
const reportsList = document.getElementById('reports-list');
const resultCount = document.getElementById('result-count');
const riskFlagsContent = document.getElementById('risk-flags-content');
const recurrenceText = document.getElementById('recurrence-text');
const recommendationContent = document.getElementById('recommendation-content');
const llmBadge = document.getElementById('llm-badge');
const ppeFileInput = document.getElementById('ppe-file-input');
const ppeResults = document.getElementById('ppe-results');
const ppeDetectionsList = document.getElementById('ppe-detections-list');

// ============================================================
// Event Listeners
// ============================================================

searchBtn.addEventListener('click', runAnalysis);
searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') runAnalysis();
});

alphaSlider.addEventListener('input', () => {
    const val = (alphaSlider.value / 100).toFixed(2);
    alphaValue.textContent = `α = ${val}`;
});

ppeFileInput.addEventListener('change', handlePPEUpload);

// Initialize Lucide icons
lucide.createIcons();

// ============================================================
// Helper: set query from quick-query buttons
// ============================================================
function setQuery(text) {
    searchInput.value = text;
    searchInput.focus();
}

// ============================================================
// Severity config
// ============================================================
const SEVERITY_CONFIG = {
    critical: { color: 'bg-red-500/20 text-red-300 border-red-500/30', icon: 'alert-octagon' },
    high:     { color: 'bg-orange-500/20 text-orange-300 border-orange-500/30', icon: 'alert-triangle' },
    medium:   { color: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30', icon: 'alert-circle' },
    low:      { color: 'bg-green-500/20 text-green-300 border-green-500/30', icon: 'check-circle' },
};

// ============================================================
// Main Analysis
// ============================================================
async function runAnalysis() {
    const query = searchInput.value.trim();
    if (!query) {
        searchInput.focus();
        return;
    }

    const topK = parseInt(topKSelect.value);
    const alpha = alphaSlider.value / 100;

    // Show loading, hide previous results
    loadingState.classList.remove('hidden');
    resultsContainer.classList.add('hidden');
    searchBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, top_k: topK, alpha }),
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();
        renderResults(data);
    } catch (error) {
        console.error('Analysis failed:', error);
        showError(error.message);
    } finally {
        loadingState.classList.add('hidden');
        searchBtn.disabled = false;
    }
}

// ============================================================
// Render Results
// ============================================================
function renderResults(data) {
    resultsContainer.classList.remove('hidden');

    // Result count
    resultCount.textContent = `${data.results.length} reports found`;

    // --- Report Cards ---
    reportsList.innerHTML = '';
    data.results.forEach((report, index) => {
        const card = createReportCard(report, index);
        reportsList.appendChild(card);
    });

    // --- Risk Flags ---
    renderRiskFlags(data.risk_summary);

    // --- Recurrence ---
    recurrenceText.textContent = data.risk_summary?.recurrence_pattern || 'No recurrence patterns detected.';

    // --- Recommendation ---
    const recHtml = marked.parse(data.recommendation || 'No recommendation available.');
    recommendationContent.innerHTML = recHtml;
    llmBadge.textContent = data.llm_provider || 'unknown';

    // Re-render icons
    lucide.createIcons();

    // Scroll to results
    resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ============================================================
// Create Report Card
// ============================================================
function createReportCard(report, index) {
    const severity = report.severity || 'medium';
    const sevConfig = SEVERITY_CONFIG[severity] || SEVERITY_CONFIG.medium;

    const card = document.createElement('div');
    card.className = `report-card report-card-enter rounded-2xl bg-surface-800/50 border border-white/5 p-5 backdrop-blur-sm`;

    const maxScore = Math.max(report.rerank_score || 0, 0.01);
    const rerankWidth = Math.min(((report.rerank_score || 0) / 12) * 100, 100);
    const denseWidth = Math.min((report.dense_score || 0) * 100, 100);
    const bm25Width = Math.min(((report.bm25_score || 0) / 10) * 100, 100);

    card.innerHTML = `
        <div class="flex items-start justify-between gap-3 mb-3">
            <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1.5">
                    <span class="text-[10px] font-mono text-primary-400 bg-primary-500/10 px-2 py-0.5 rounded-md border border-primary-500/20">${report.id}</span>
                    <span class="severity-badge text-[10px] px-2 py-0.5 rounded-md border ${sevConfig.color}">${severity.toUpperCase()}</span>
                    ${report.source === 'osha' ? '<span class="text-[10px] px-2 py-0.5 rounded-md bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">OSHA</span>' : ''}
                </div>
                <h4 class="text-sm font-semibold text-gray-200 leading-snug">${escapeHtml(report.title)}</h4>
            </div>
            ${report.recurrence_score > 0.3 ? `
                <div class="tooltip shrink-0" data-tooltip="High recurrence">
                    <div class="w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center">
                        <i data-lucide="repeat" class="w-3.5 h-3.5 text-purple-400"></i>
                    </div>
                </div>
            ` : ''}
        </div>

        <p class="text-xs text-gray-400 leading-relaxed mb-3 line-clamp-3">${escapeHtml(report.snippet)}</p>

        <div class="flex flex-wrap gap-2 mb-3">
            ${report.equipment ? `<span class="text-[10px] px-2 py-0.5 rounded-md bg-white/5 text-gray-400 border border-white/5"><i data-lucide="cog" class="w-2.5 h-2.5 inline mr-1 opacity-60"></i>${escapeHtml(report.equipment)}</span>` : ''}
            ${report.hazard_type ? `<span class="text-[10px] px-2 py-0.5 rounded-md bg-white/5 text-gray-400 border border-white/5"><i data-lucide="flame" class="w-2.5 h-2.5 inline mr-1 opacity-60"></i>${escapeHtml(report.hazard_type)}</span>` : ''}
            ${report.location ? `<span class="text-[10px] px-2 py-0.5 rounded-md bg-white/5 text-gray-400 border border-white/5"><i data-lucide="map-pin" class="w-2.5 h-2.5 inline mr-1 opacity-60"></i>${escapeHtml(report.location)}</span>` : ''}
            ${report.date ? `<span class="text-[10px] px-2 py-0.5 rounded-md bg-white/5 text-gray-400 border border-white/5">${escapeHtml(report.date)}</span>` : ''}
        </div>

        <!-- Score Bars -->
        <div class="space-y-1.5">
            <div class="flex items-center gap-2">
                <span class="text-[9px] text-gray-600 w-14 text-right font-mono">Rerank</span>
                <div class="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
                    <div class="score-bar-fill h-full bg-gradient-to-r from-primary-500 to-cyan-400 rounded-full" style="width: ${rerankWidth}%"></div>
                </div>
                <span class="text-[9px] text-gray-500 font-mono w-10">${(report.rerank_score || 0).toFixed(2)}</span>
            </div>
            <div class="flex items-center gap-2">
                <span class="text-[9px] text-gray-600 w-14 text-right font-mono">Dense</span>
                <div class="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
                    <div class="score-bar-fill h-full bg-gradient-to-r from-purple-500 to-pink-400 rounded-full" style="width: ${denseWidth}%"></div>
                </div>
                <span class="text-[9px] text-gray-500 font-mono w-10">${(report.dense_score || 0).toFixed(2)}</span>
            </div>
            <div class="flex items-center gap-2">
                <span class="text-[9px] text-gray-600 w-14 text-right font-mono">BM25</span>
                <div class="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
                    <div class="score-bar-fill h-full bg-gradient-to-r from-amber-500 to-orange-400 rounded-full" style="width: ${bm25Width}%"></div>
                </div>
                <span class="text-[9px] text-gray-500 font-mono w-10">${(report.bm25_score || 0).toFixed(2)}</span>
            </div>
        </div>
    `;

    return card;
}

// ============================================================
// Render Risk Flags
// ============================================================
function renderRiskFlags(riskSummary) {
    riskFlagsContent.innerHTML = '';

    const flags = riskSummary?.equipment_flags || {};
    const entries = Object.entries(flags);

    if (entries.length === 0) {
        riskFlagsContent.innerHTML = '<p class="text-xs text-gray-600 italic">No equipment risk flags detected.</p>';
        return;
    }

    entries.forEach(([eqId, flag]) => {
        const isAtRisk = flag.flag || flag.autoencoder_anomaly;
        const statusColor = isAtRisk ? 'border-red-500/20 bg-red-500/5' : 'border-green-500/20 bg-green-500/5';
        const dotColor = isAtRisk ? 'bg-red-400' : 'bg-green-400';

        const el = document.createElement('div');
        el.className = `rounded-xl border ${statusColor} p-3 transition-colors`;
        el.innerHTML = `
            <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-semibold text-gray-200 flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full ${dotColor} ${isAtRisk ? 'animate-pulse' : ''}"></span>
                    ${escapeHtml(eqId)}
                </span>
                <span class="text-[10px] ${isAtRisk ? 'text-red-400' : 'text-green-400'} font-medium">
                    ${isAtRisk ? 'AT RISK' : 'Normal'}
                </span>
            </div>
            <div class="space-y-1">
                <div class="flex items-center justify-between">
                    <span class="text-[10px] text-gray-500">LSTM Drift</span>
                    <span class="text-[10px] font-mono ${flag.flag ? 'text-red-400' : 'text-gray-500'}">${(flag.lstm_drift_risk || 0).toFixed(2)}</span>
                </div>
                <div class="flex items-center justify-between">
                    <span class="text-[10px] text-gray-500">Autoencoder</span>
                    <span class="text-[10px] font-mono ${flag.autoencoder_anomaly ? 'text-red-400' : 'text-gray-500'}">
                        ${flag.autoencoder_anomaly ? 'Anomaly' : 'Normal'}
                    </span>
                </div>
            </div>
        `;
        riskFlagsContent.appendChild(el);
    });
}

// ============================================================
// PPE Upload Handler
// ============================================================
let currentUploadedImageObj = null;

async function handlePPEUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    currentUploadedImageObj = file;
    const formData = new FormData();
    formData.append('image', file);

    ppeDetectionsList.innerHTML = '<div class="skeleton h-20 w-full"></div>';
    ppeResults.classList.remove('hidden');

    try {
        const response = await fetch(`${API_BASE}/detect-ppe`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || `Error ${response.status}`);
        }

        const data = await response.json();
        renderPPEResults(data, file);
    } catch (error) {
        ppeDetectionsList.innerHTML = `
            <div class="text-xs text-red-400 flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                <i data-lucide="x-circle" class="w-4 h-4 shrink-0"></i>
                ${escapeHtml(error.message)}
            </div>
        `;
        lucide.createIcons();
    }
}

function renderPPEResults(data, file) {
    ppeDetectionsList.innerHTML = '';

    if (!data.detections || data.detections.length === 0) {
        ppeDetectionsList.innerHTML = '<p class="text-xs text-gray-500 italic p-2">No objects detected in this image.</p>';
        return;
    }

    // Separate violations vs person vs compliant
    const violations = data.detections.filter(d => d.class_name.toLowerCase().startsWith('no-') || d.class_name.toLowerCase().startsWith('no_'));
    const people = data.detections.filter(d => ['person', 'human'].includes(d.class_name.toLowerCase()));
    const compliant = data.detections.filter(d => !d.class_name.toLowerCase().startsWith('no-') && !d.class_name.toLowerCase().startsWith('no_') && !['person', 'human'].includes(d.class_name.toLowerCase()));

    // Container for annotated canvas
    const canvasContainer = document.createElement('div');
    canvasContainer.className = 'mb-4 overflow-hidden rounded-xl border border-white/10 bg-black/40 flex justify-center';
    const canvas = document.createElement('canvas');
    canvas.className = 'max-w-full h-auto rounded-lg';
    canvasContainer.appendChild(canvas);
    ppeDetectionsList.appendChild(canvasContainer);

    // Draw image and bounding boxes on canvas
    if (file) {
        const img = new Image();
        img.onload = () => {
            canvas.width = img.width;
            canvas.height = img.height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);

            data.detections.forEach(det => {
                const isViol = det.class_name.toLowerCase().startsWith('no-') || det.class_name.toLowerCase().startsWith('no_');
                const isPer = ['person', 'human'].includes(det.class_name.toLowerCase());
                const strokeColor = isViol ? '#ef4444' : (isPer ? '#06b6d4' : '#22c55e');

                const bbox = det.bbox || [];
                if (bbox.length === 4) {
                    let [x1, y1, x2, y2] = bbox;
                    if (Math.max(...bbox) <= 1.0) {
                        x1 *= img.width;
                        y1 *= img.height;
                        x2 *= img.width;
                        y2 *= img.height;
                    }
                    ctx.strokeStyle = strokeColor;
                    ctx.lineWidth = Math.max(3, Math.round(img.width / 400));
                    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

                    // Label background
                    const label = `${det.class_name} ${(det.confidence * 100).toFixed(0)}%`;
                    ctx.font = `bold ${Math.max(14, Math.round(img.width / 60))}px sans-serif`;
                    const textWidth = ctx.measureText(label).width;
                    const textHeight = Math.max(16, Math.round(img.width / 55));

                    ctx.fillStyle = strokeColor;
                    ctx.fillRect(x1, Math.max(0, y1 - textHeight - 4), textWidth + 8, textHeight + 4);

                    ctx.fillStyle = '#ffffff';
                    ctx.fillText(label, x1 + 4, Math.max(textHeight, y1 - 4));
                }
            });
        };
        img.src = URL.createObjectURL(file);
    }

    // Violation Alert Banner
    if (violations.length > 0) {
        const violNames = [...new Set(violations.map(v => v.class_name))].join(', ');
        const banner = document.createElement('div');
        banner.className = 'p-3 mb-3 rounded-xl bg-red-500/10 border border-red-500/30 flex items-start gap-2.5';
        banner.innerHTML = `
            <i data-lucide="alert-triangle" class="w-5 h-5 text-red-400 shrink-0 mt-0.5"></i>
            <div>
                <p class="text-xs font-semibold text-red-300">Safety Compliance Violations Detected</p>
                <p class="text-[11px] text-red-200/80 mt-0.5">${violations.length} hazard(s) flagged: <span class="font-mono">${escapeHtml(violNames)}</span></p>
            </div>
        `;
        ppeDetectionsList.appendChild(banner);
    } else {
        const banner = document.createElement('div');
        banner.className = 'p-3 mb-3 rounded-xl bg-green-500/10 border border-green-500/30 flex items-center gap-2';
        banner.innerHTML = `
            <i data-lucide="check-circle" class="w-4 h-4 text-green-400 shrink-0"></i>
            <p class="text-xs font-semibold text-green-300">No Missing PPE Detected on Inspected Workers</p>
        `;
        ppeDetectionsList.appendChild(banner);
    }

    // Detections List
    data.detections.forEach((det) => {
        const isViol = det.class_name.toLowerCase().startsWith('no-') || det.class_name.toLowerCase().startsWith('no_');
        const isPer = ['person', 'human'].includes(det.class_name.toLowerCase());

        const confPercent = (det.confidence * 100).toFixed(1);
        const icon = isViol ? 'alert-triangle' : (isPer ? 'user' : 'shield-check');
        const iconColor = isViol ? 'text-red-400' : (isPer ? 'text-cyan-400' : 'text-green-400');
        const cardBorder = isViol ? 'border-red-500/20 bg-red-500/5' : 'border-white/5 bg-white/[0.02]';
        const labelText = isViol ? `⚠️ VIOLATION: ${det.class_name}` : (isPer ? `Worker / Personnel` : `🟢 COMPLIANT: ${det.class_name}`);
        const labelClass = isViol ? 'text-red-300 font-semibold' : (isPer ? 'text-gray-300 font-medium' : 'text-green-300 font-semibold');

        const el = document.createElement('div');
        el.className = `ppe-detection-item flex items-center justify-between p-2.5 rounded-lg border ${cardBorder}`;
        el.innerHTML = `
            <div class="flex items-center gap-2">
                <i data-lucide="${icon}" class="w-4 h-4 ${iconColor}"></i>
                <span class="text-xs ${labelClass}">${escapeHtml(labelText)}</span>
            </div>
            <span class="text-[10px] font-mono ${isViol ? 'text-red-400 font-bold' : 'text-gray-400'}">${confPercent}%</span>
        `;
        ppeDetectionsList.appendChild(el);
    });

    lucide.createIcons();
}

// ============================================================
// Error Display
// ============================================================
function showError(message) {
    resultsContainer.classList.remove('hidden');
    reportsList.innerHTML = `
        <div class="rounded-2xl bg-red-500/5 border border-red-500/20 p-6 text-center">
            <i data-lucide="alert-circle" class="w-8 h-8 text-red-400 mx-auto mb-3"></i>
            <p class="text-sm text-red-300 font-medium mb-1">Analysis Failed</p>
            <p class="text-xs text-gray-500">${escapeHtml(message)}</p>
            <p class="text-xs text-gray-600 mt-3">Make sure the backend is running: <code class="bg-white/5 px-2 py-0.5 rounded text-gray-400">uvicorn api.main:app --reload</code></p>
        </div>
    `;
    riskFlagsContent.innerHTML = '';
    recurrenceText.textContent = '';
    recommendationContent.innerHTML = '';
    lucide.createIcons();
}

// ============================================================
// Utility
// ============================================================
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
