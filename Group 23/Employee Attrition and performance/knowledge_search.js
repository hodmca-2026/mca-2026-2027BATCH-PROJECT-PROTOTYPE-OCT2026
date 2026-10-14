document.addEventListener("DOMContentLoaded", () => {

    const input = document.getElementById("searchInput");
    const method = document.getElementById("searchMethod");
    const button = document.getElementById("searchButton");
    const resultsContainer = document.getElementById("searchResults");
    const status = document.getElementById("searchStatus");
    const methodButtons = document.querySelectorAll(".retrieval-method");
    const quickSearchButtons = document.querySelectorAll(".quick-search");

    const comparisonTable = document.getElementById("irComparisonTable");
    const evaluationGrid = document.getElementById("irEvaluationGrid");
    const passageResults = document.getElementById("passageResults");
    const extractionContent = document.getElementById("extractionContent");


    // ========================================================
    // ICONS
    // ========================================================

    function refreshIcons() {
        if (window.lucide) {
            lucide.createIcons();
        }
    }


    // ========================================================
    // METHOD HELPERS
    // ========================================================

    function getMethodLabel(value) {
        switch (value) {
            case "bm25":
                return "BM25";
            case "tfidf":
                return "TF-IDF";
            case "language_model":
                return "Language Model";
            default:
                return value || "Retrieval Model";
        }
    }


    function getScoreLabel(methodValue) {
        switch (methodValue) {
            case "language_model":
                return "Log Likelihood";
            case "tfidf":
                return "TF-IDF Score";
            default:
                return "BM25 Score";
        }
    }


    function formatScore(value) {
        const number = Number(value);

        if (Number.isNaN(number)) {
            return "0.000";
        }

        return number.toFixed(3);
    }


    function safeRank(value) {
        return value === null || value === undefined ? "—" : `#${value}`;
    }


    // ========================================================
    // METHOD UI
    // ========================================================

    function updateMethodUI() {
        methodButtons.forEach(methodButton => {
            methodButton.classList.toggle(
                "active",
                methodButton.dataset.method === method.value
            );
        });
    }


    method.addEventListener("change", updateMethodUI);

    methodButtons.forEach(methodButton => {
        methodButton.addEventListener("click", () => {
            method.value = methodButton.dataset.method;
            updateMethodUI();
            input.focus();
        });
    });


    // ========================================================
    // SEARCH
    // ========================================================

    async function performSearch(query = null) {
        if (query === null) {
            query = input.value.trim();
        } else {
            input.value = query;
        }

        if (!query) {
            status.textContent = "Enter an HR-related query to begin.";
            input.focus();
            return;
        }

        button.disabled = true;
        button.classList.add("is-loading");
        button.innerHTML = '<span class="button-spinner"></span> Searching...';

        status.textContent = `Searching with ${getMethodLabel(method.value)}...`;

        resultsContainer.innerHTML = `
            <article class="knowledge-loading-card">
                <div class="loading-ring"></div>
                <h3>Retrieving HR knowledge</h3>
                <p>Running ${escapeHtml(getMethodLabel(method.value))} and the IR analysis pipeline.</p>
            </article>
        `;

        try {
            const requestBody = {
                query,
                method: method.value,
                top_k: 5
            };

            const [searchResponse, analysisResponse] = await Promise.all([
                fetch("/api/search", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    body: JSON.stringify(requestBody)
                }),
                fetch("/api/ir-analysis", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    body: JSON.stringify(requestBody)
                })
            ]);

            const searchData = await searchResponse.json();
            const analysisData = await analysisResponse.json();

            if (!searchResponse.ok) {
                throw new Error(searchData.error || "Search failed");
            }

            if (!analysisResponse.ok) {
                throw new Error(analysisData.error || "IR analysis failed");
            }

            displayResults(searchData);
            displayIRAnalysis(analysisData.analysis || {});

        } catch (error) {
            console.error("Knowledge search error:", error);

            resultsContainer.innerHTML = `
                <article class="knowledge-error-card">
                    <div class="knowledge-error-icon">
                        <i data-lucide="alert-circle"></i>
                    </div>
                    <div>
                        <h3>Search Error</h3>
                        <p>${escapeHtml(error.message)}</p>
                    </div>
                </article>
            `;

            clearIRAnalysis("IR analysis is unavailable for this query.");
            status.textContent = "Search unavailable.";
            refreshIcons();

        } finally {
            button.disabled = false;
            button.classList.remove("is-loading");
            button.innerHTML = '<i data-lucide="search"></i> Search';
            refreshIcons();
        }
    }


    // ========================================================
    // DOCUMENT RESULTS
    // ========================================================

    function displayResults(data) {
        const results = Array.isArray(data.results) ? data.results : [];
        const selectedMethod = data.method || method.value;

        status.innerHTML = `
            <span>Query</span>
            <strong>${escapeHtml(data.query || "")}</strong>
            <span class="status-divider">/</span>
            <span>Method</span>
            <strong>${escapeHtml(getMethodLabel(selectedMethod))}</strong>
            <span class="status-divider">/</span>
            <span>Results</span>
            <strong>${results.length}</strong>
        `;

        if (!results.length) {
            resultsContainer.innerHTML = `
                <article class="knowledge-empty-card">
                    <div class="knowledge-empty-icon">
                        <i data-lucide="search-x"></i>
                    </div>
                    <h3>No relevant documents found</h3>
                    <p>Try another HR-related query or retrieval method.</p>
                </article>
            `;
            refreshIcons();
            return;
        }

        resultsContainer.innerHTML = results.map((result, index) => {
            const rank = index + 1;
            const score = Number(result.score ?? result.display_score ?? 0);
            const matched = Array.isArray(result.matched_terms)
                ? result.matched_terms
                : [];
            const documentName = result.document || result.document_id || "Unknown document";
            const documentId = String(
                result.document_id || result.document || "Unknown"
            ).replace(/\.txt$/i, "");

            const scoreLabel = selectedMethod === "language_model"
                ? "Log Likelihood"
                : "Relevance";

            return `
                <article class="knowledge-result-card ${rank === 1 ? "top-result" : ""}">
                    <div class="knowledge-result-header">
                        <div class="knowledge-result-rank">#${rank}</div>

                        <div class="knowledge-result-title">
                            <h3>${escapeHtml(documentName)}</h3>
                            <span>Document ID: ${escapeHtml(documentId)}</span>
                        </div>

                        <div class="knowledge-score">
                            <small>${scoreLabel}</small>
                            <strong>${formatScore(score)}</strong>
                        </div>
                    </div>

                    <div class="knowledge-result-method">
                        <span>${escapeHtml(getMethodLabel(selectedMethod))}</span>
                        <span class="result-rank-label">Rank ${rank}</span>
                    </div>

                    ${matched.length ? `
                        <div class="matched-terms-section">
                            <span>Matched terms</span>
                            <div class="matched-terms">
                                ${matched.map(term => `
                                    <span class="matched-term">${escapeHtml(term)}</span>
                                `).join("")}
                            </div>
                        </div>
                    ` : ""}

                    ${selectedMethod === "language_model" ? `
                        <div style="margin-top:14px;color:#64748b;font-size:10px;line-height:1.6;">
                            Higher log-likelihood is better within the Language Model.
                            Negative values are expected because log(probability) is negative for probabilities below 1.
                        </div>
                    ` : ""}

                    <div style="margin-top:18px;display:flex;justify-content:flex-end;">
                        <button
                            type="button"
                            class="btn btn-primary view-document-btn"
                            data-document-id="${escapeHtml(documentId)}"
                        >
                            <i data-lucide="file-text"></i>
                            View Document
                        </button>
                    </div>
                </article>
            `;
        }).join("");

        refreshIcons();
    }


    // ========================================================
    // IR ANALYSIS
    // ========================================================

    function clearIRAnalysis(message) {
        comparisonTable.innerHTML = `
            <tr>
                <td colspan="6" style="padding:22px;text-align:center;color:#64748b;">
                    ${escapeHtml(message)}
                </td>
            </tr>
        `;

        evaluationGrid.innerHTML = `
            <div class="card" style="padding:18px;color:#64748b;">
                ${escapeHtml(message)}
            </div>
        `;

        passageResults.innerHTML = `
            <div class="card" style="padding:18px;color:#64748b;">
                ${escapeHtml(message)}
            </div>
        `;

        extractionContent.innerHTML = `
            <div class="card" style="padding:18px;color:#64748b;">
                ${escapeHtml(message)}
            </div>
        `;
    }


    function displayIRAnalysis(analysis) {
        displayComparison(analysis.comparison || []);
        displayEvaluation(analysis.evaluation || {});
        displayPassages(analysis.passages || []);
        displayExtraction(analysis.information_extraction || {});
    }


    // ========================================================
    // RANKING COMPARISON
    // ========================================================

    function displayComparison(comparison) {
        if (!comparison.length) {
            comparisonTable.innerHTML = `
                <tr>
                    <td colspan="6" style="padding:22px;text-align:center;color:#64748b;">
                        No cross-model ranking data is available.
                    </td>
                </tr>
            `;
            return;
        }

        comparisonTable.innerHTML = comparison.map(item => `
            <tr>
                <td style="padding:13px 15px;text-align:left;">
                    <strong>${escapeHtml(item.document || "Unknown")}</strong>
                </td>
                <td style="padding:13px 10px;text-align:center;">
                    ${safeRank(item.bm25_rank)}
                    <div style="font-size:9px;color:#64748b;margin-top:3px;">
                        ${item.bm25_score === null || item.bm25_score === undefined ? "" : formatScore(item.bm25_score)}
                    </div>
                </td>
                <td style="padding:13px 10px;text-align:center;">
                    ${safeRank(item.tfidf_rank)}
                    <div style="font-size:9px;color:#64748b;margin-top:3px;">
                        ${item.tfidf_score === null || item.tfidf_score === undefined ? "" : formatScore(item.tfidf_score)}
                    </div>
                </td>
                <td style="padding:13px 10px;text-align:center;">
                    ${safeRank(item.language_model_rank)}
                    <div style="font-size:9px;color:#64748b;margin-top:3px;">
                        ${item.language_model_score === null || item.language_model_score === undefined ? "" : formatScore(item.language_model_score)}
                    </div>
                </td>
                <td style="padding:13px 10px;text-align:center;">
                    <strong>${item.method_agreement || 0}/3</strong>
                </td>
                <td style="padding:13px 10px;text-align:center;">
                    ${Number(item.rrf_score || 0).toFixed(5)}
                </td>
            </tr>
        `).join("");
    }


    // ========================================================
    // EVALUATION
    // ========================================================

    function displayEvaluation(evaluation) {
        const methods = evaluation.methods || {};
        const methodEntries = Object.entries(methods);

        if (!methodEntries.length) {
            evaluationGrid.innerHTML = `
                <div class="card" style="padding:18px;color:#64748b;">
                    No evaluation data is available.
                </div>
            `;
            return;
        }

        evaluationGrid.innerHTML = methodEntries.map(([methodName, metrics]) => `
            <div class="card" style="padding:18px;">
                <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;">
                    <strong>${escapeHtml(methodName)}</strong>
                    <span style="font-size:9px;color:#64748b;">Top-${evaluation.k || 5}</span>
                </div>

                <div style="display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:14px;">
                    ${metricBox("Precision@5", metrics.precision_at_k)}
                    ${metricBox("Recall@5", metrics.recall_at_k)}
                    ${metricBox("F1", metrics.f1)}
                    ${metricBox("MRR", metrics.mrr)}
                </div>
            </div>
        `).join("");
    }


    function metricBox(label, value) {
        return `
            <div style="padding:10px;border:1px solid rgba(148,163,184,.12);border-radius:9px;background:rgba(15,23,42,.35);">
                <small style="display:block;color:#64748b;font-size:9px;">${escapeHtml(label)}</small>
                <strong style="display:block;margin-top:4px;font-size:15px;">${Number(value || 0).toFixed(3)}</strong>
            </div>
        `;
    }


    // ========================================================
    // PASSAGE RETRIEVAL
    // ========================================================

    function displayPassages(passages) {
        if (!passages.length) {
            passageResults.innerHTML = `
                <div class="card" style="padding:18px;color:#64748b;">
                    No matching passages were found.
                </div>
            `;
            return;
        }

        passageResults.innerHTML = passages.map((passage, index) => {
            const matched = Array.isArray(passage.matched_terms)
                ? passage.matched_terms
                : [];

            return `
                <article class="card" style="padding:18px;">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:15px;">
                        <div>
                            <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:.7px;">
                                Passage ${index + 1}
                            </div>
                            <h3 style="margin:6px 0 0;font-size:14px;">
                                ${escapeHtml(passage.document || "Unknown document")}
                            </h3>
                            <div style="margin-top:4px;font-size:10px;color:#64748b;">
                                Passage ID: ${escapeHtml(passage.passage_id ?? "—")}
                            </div>
                        </div>

                        <div style="text-align:right;">
                            <small style="display:block;color:#64748b;font-size:9px;">Log Likelihood</small>
                            <strong>${formatScore(passage.score)}</strong>
                        </div>
                    </div>

                    <div style="margin-top:14px;color:#cbd5e1;font-size:12px;line-height:1.75;padding:14px;border-left:2px solid rgba(129,140,248,.55);background:rgba(15,23,42,.35);border-radius:0 9px 9px 0;">
                        ${escapeHtml(passage.text || "")}
                    </div>

                    ${matched.length ? `
                        <div class="matched-terms-section" style="margin-top:13px;">
                            <span>Matched terms</span>
                            <div class="matched-terms">
                                ${matched.map(term => `
                                    <span class="matched-term">${escapeHtml(term)}</span>
                                `).join("")}
                            </div>
                        </div>
                    ` : ""}
                </article>
            `;
        }).join("");
    }


    // ========================================================
    // INFORMATION EXTRACTION
    // ========================================================

    function displayExtraction(extraction) {
        if (!extraction || !extraction.available) {
            extractionContent.innerHTML = `
                <div class="card" style="padding:18px;color:#64748b;">
                    No extractable policy information is available for the top result.
                </div>
            `;
            return;
        }

        const entities = Array.isArray(extraction.entities)
            ? extraction.entities
            : [];
        const numericFacts = Array.isArray(extraction.numeric_facts)
            ? extraction.numeric_facts
            : [];
        const keySentences = Array.isArray(extraction.key_sentences)
            ? extraction.key_sentences
            : [];

        extractionContent.innerHTML = `
            <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;">
                <div class="card" style="padding:18px;">
                    <small style="color:#64748b;font-size:9px;text-transform:uppercase;">Top Document</small>
                    <strong style="display:block;margin-top:7px;">${escapeHtml(extraction.document || "Unknown")}</strong>
                </div>

                <div class="card" style="padding:18px;">
                    <small style="color:#64748b;font-size:9px;text-transform:uppercase;">Policy Entities</small>
                    <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:10px;">
                        ${entities.length
                            ? entities.map(item => `<span class="matched-term">${escapeHtml(item)}</span>`).join("")
                            : `<span style="font-size:10px;color:#64748b;">None detected</span>`
                        }
                    </div>
                </div>

                <div class="card" style="padding:18px;">
                    <small style="color:#64748b;font-size:9px;text-transform:uppercase;">Numeric Facts</small>
                    <div style="margin-top:9px;color:#cbd5e1;font-size:11px;line-height:1.8;">
                        ${numericFacts.length
                            ? numericFacts.map(item => `<div>• ${escapeHtml(item)}</div>`).join("")
                            : `<span style="color:#64748b;">No numeric fact detected</span>`
                        }
                    </div>
                </div>
            </div>

            <div class="card" style="padding:18px;margin-top:14px;">
                <small style="color:#64748b;font-size:9px;text-transform:uppercase;">Key Extracted Sentences</small>
                <div style="margin-top:10px;display:grid;gap:9px;">
                    ${keySentences.length
                        ? keySentences.map(sentence => `
                            <div style="padding:12px;border:1px solid rgba(148,163,184,.12);border-radius:9px;color:#cbd5e1;font-size:11px;line-height:1.7;">
                                ${escapeHtml(sentence)}
                            </div>
                        `).join("")
                        : `<div style="color:#64748b;font-size:11px;">No key policy sentences detected.</div>`
                    }
                </div>
            </div>
        `;
    }


    // ========================================================
    // DOCUMENT VIEW
    // ========================================================

    async function openDocument(documentId) {
        if (!documentId) {
            return;
        }

        createDocumentModal();

        const modal = document.getElementById("documentModal");
        const title = document.getElementById("documentModalTitle");
        const category = document.getElementById("documentModalCategory");
        const body = document.getElementById("documentModalBody");

        modal.style.display = "flex";
        title.textContent = "Loading document...";
        category.textContent = "";
        body.textContent = "Loading HR document...";

        try {
            const response = await fetch(
                `/api/document/${encodeURIComponent(documentId)}`,
                {
                    method: "GET",
                    headers: {
                        "Accept": "application/json"
                    }
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.error || "Unable to load document"
                );
            }

            title.textContent = data.title || documentId;
            category.textContent = data.category || "HR Knowledge";
            body.textContent = data.content || "Document content is empty.";

        } catch (error) {
            console.error("Document retrieval error:", error);
            title.textContent = "Document unavailable";
            category.textContent = "";
            body.innerHTML = `
                <div style="padding:20px;border:1px solid #7f1d1d;background:#450a0a;border-radius:10px;">
                    <div style="color:#fca5a5;font-weight:600;margin-bottom:8px;">
                        Unable to open document
                    </div>
                    <div style="color:#fecaca;font-size:12px;line-height:1.6;">
                        ${escapeHtml(error.message)}
                    </div>
                </div>
            `;
        }

        refreshIcons();
    }


    function createDocumentModal() {
        if (document.getElementById("documentModal")) {
            return;
        }

        const modal = document.createElement("div");
        modal.id = "documentModal";
        modal.style.cssText = `
            position:fixed;
            inset:0;
            z-index:99999;
            display:none;
            align-items:center;
            justify-content:center;
            padding:24px;
            background:rgba(2,6,23,.78);
            backdrop-filter:blur(6px);
        `;

        modal.innerHTML = `
            <div style="
                width:min(920px,96vw);
                max-height:90vh;
                display:flex;
                flex-direction:column;
                overflow:hidden;
                background:#0f172a;
                border:1px solid #1e293b;
                border-radius:16px;
                box-shadow:0 25px 80px rgba(0,0,0,.55);
            ">
                <div style="
                    display:flex;
                    align-items:flex-start;
                    justify-content:space-between;
                    gap:16px;
                    padding:20px 22px;
                    border-bottom:1px solid #1e293b;
                ">
                    <div>
                        <h2 id="documentModalTitle" style="margin:0;color:#f8fafc;font-size:18px;font-weight:700;">
                            HR Document
                        </h2>
                        <div id="documentModalCategory" style="margin-top:6px;color:#64748b;font-size:11px;"></div>
                    </div>

                    <button
                        type="button"
                        id="closeDocumentModal"
                        aria-label="Close document"
                        style="width:36px;height:36px;flex-shrink:0;border:1px solid #334155;background:#1e293b;color:#cbd5e1;border-radius:8px;cursor:pointer;display:flex;align-items:center;justify-content:center;"
                    >
                        <i data-lucide="x"></i>
                    </button>
                </div>

                <div style="flex:1;overflow:auto;padding:24px;">
                    <div
                        id="documentModalBody"
                        style="color:#cbd5e1;font-size:13px;line-height:1.8;white-space:pre-wrap;word-break:break-word;font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;"
                    >
                        Loading HR document...
                    </div>
                </div>

                <div style="display:flex;justify-content:flex-end;padding:14px 22px;border-top:1px solid #1e293b;">
                    <button type="button" id="closeDocumentModalFooter" class="btn btn-secondary">Close</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        document.getElementById("closeDocumentModal").addEventListener(
            "click",
            closeDocumentModal
        );

        document.getElementById("closeDocumentModalFooter").addEventListener(
            "click",
            closeDocumentModal
        );

        modal.addEventListener("click", event => {
            if (event.target === modal) {
                closeDocumentModal();
            }
        });

        refreshIcons();
    }


    function closeDocumentModal() {
        const modal = document.getElementById("documentModal");

        if (modal) {
            modal.style.display = "none";
        }
    }


    resultsContainer.addEventListener("click", event => {
        const viewButton = event.target.closest(".view-document-btn");

        if (!viewButton) {
            return;
        }

        openDocument(viewButton.dataset.documentId);
    });


    // ========================================================
    // QUICK SEARCH + EVENTS
    // ========================================================

    quickSearchButtons.forEach(quickButton => {
        quickButton.addEventListener("click", () => {
            performSearch(quickButton.dataset.query);
        });
    });

    button.addEventListener("click", () => performSearch());

    input.addEventListener("keydown", event => {
        if (event.key === "Enter") {
            performSearch();
        }
    });

    document.addEventListener("keydown", event => {
        if (event.key === "Escape") {
            closeDocumentModal();
        }
    });


    // ========================================================
    // INITIAL STATE
    // ========================================================

    updateMethodUI();
    refreshIcons();
});


// ============================================================
// HTML ESCAPING
// ============================================================

function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
