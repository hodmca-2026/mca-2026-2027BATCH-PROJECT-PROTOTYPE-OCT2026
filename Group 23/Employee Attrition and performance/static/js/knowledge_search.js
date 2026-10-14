document.addEventListener("DOMContentLoaded", () => {

    const input = document.getElementById("searchInput");

    const method = document.getElementById("searchMethod");

    const button = document.getElementById("searchButton");

    const resultsContainer = document.getElementById("searchResults");

    const status = document.getElementById("searchStatus");

    const methodButtons = document.querySelectorAll(".retrieval-method");

    const quickSearchButtons = document.querySelectorAll(".quick-search");

    const comparisonContainer = document.getElementById("irComparisonTable");

    const evaluationContainer = document.getElementById("irEvaluationGrid");

    const passageResults = document.getElementById("passageResults");

    const extractionContent = document.getElementById("extractionContent");
    const webSearchStatus = document.getElementById("webSearchStatus");
    const webSearchResults = document.getElementById("webSearchResults");
    let webSearchRequestId = 0;

    // --------------------------------------------------------

    // Helpers

    // --------------------------------------------------------

    function escapeHtml(value) {

        return String(value ?? "")

            .replace(/&/g, "&amp;")

            .replace(/</g, "&lt;")

            .replace(/>/g, "&gt;")

            .replace(/"/g, "&quot;")

            .replace(/'/g, "&#039;");

    }

    function refreshIcons() {

        if (window.lucide) window.lucide.createIcons();

    }

    function normalizeMethod(value) {

        return String(value || "").trim().toLowerCase().replace(/[\s_-]+/g, "");

    }

    function isLanguageModel(value) {

        return normalizeMethod(value) === "languagemodel";

    }

    function isTfidf(value) {

        return normalizeMethod(value) === "tfidf";

    }

    function methodLabel(value) {

        if (isLanguageModel(value)) return "Language Model";

        if (isTfidf(value)) return "TF-IDF";

        if (normalizeMethod(value) === "bm25") return "BM25";

        return value || "Retrieval Model";

    }

    function numberOrNull(value) {

        if (value === null || value === undefined || value === "") return null;

        const number = Number(value);

        return Number.isFinite(number) ? number : null;

    }

    function formatScore(value, decimals = 3) {

        const number = numberOrNull(value);

        return number === null ? "—" : number.toFixed(decimals);

    }

    // Convert log P(Q|D) to P(Q|D) for display only.

    // The original backend log score continues to determine ranking.

    function queryProbabilityFromLogScore(value) {

        const logScore = numberOrNull(value);

        if (logScore === null) return null;

        return Math.max(0, Math.min(1, Math.exp(logScore)));

    }

    function formatQueryProbability(logScore) {

        const probability = queryProbabilityFromLogScore(logScore);

        if (probability === null) return "—";

        if (probability === 0) return "0";

        if (probability < 0.0001) return probability.toExponential(3);

        return probability.toFixed(4);

    }

    function safeRank(value) {

        return value === null || value === undefined ? "—" : `#${value}`;

    }

    function placeholder(message) {

        return `<div class="ir-placeholder">${escapeHtml(message)}</div>`;

    }

    // --------------------------------------------------------

    // Method selector

    // --------------------------------------------------------

    function updateMethodUI() {

        methodButtons.forEach(methodButton => {

            methodButton.classList.toggle("active", methodButton.dataset.method === method.value);

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

    // --------------------------------------------------------

    // Search

    // --------------------------------------------------------

    async function performSearch(query = null) {

        query = query === null ? input.value.trim() : String(query).trim();

        if (!query) {

            status.textContent = "Enter an HR-related query to begin.";

            input.focus();

            return;

        }

        input.value = query;

        button.disabled = true;

        button.classList.add("is-loading");

        button.innerHTML = '<span class="button-spinner"></span> Searching...';

        status.textContent = `Searching with ${methodLabel(method.value)}...`;

        resultsContainer.innerHTML = `

            <article class="knowledge-loading-card">

                <div class="loading-ring"></div>

                <h3>Retrieving HR knowledge</h3>

                <p>Running ${escapeHtml(methodLabel(method.value))} retrieval.</p>

            </article>`;

        // External search is supplemental and runs independently of the internal IR request.
        // Errors here are displayed only in Related Websites and never cancel local retrieval.
        searchWebsites(query);

        const requestBody = { query, method: method.value, top_k: 5 };

        try {

            const response = await fetch("/api/search", {

                method: "POST",

                headers: {

                    "Content-Type": "application/json",

                    "Accept": "application/json"

                },

                body: JSON.stringify(requestBody)

            });

            const data = await response.json();

            if (!response.ok || data.success === false) {

                throw new Error(data.error || "Search failed.");

            }

            displayResults(data);

            // Keep the primary search usable if analytics fail.

            try {

                const analysisResponse = await fetch("/api/ir-analysis", {

                    method: "POST",

                    headers: {

                        "Content-Type": "application/json",

                        "Accept": "application/json"

                    },

                    body: JSON.stringify(requestBody)

                });

                const analysisData = await analysisResponse.json();

                if (!analysisResponse.ok || analysisData.success === false) {

                    throw new Error(analysisData.error || "IR analysis failed.");

                }

                displayIRAnalysis(analysisData.analysis || {});

            } catch (analysisError) {

                console.error("IR analytics unavailable:", analysisError);

                clearIRAnalysis(`IR analytics unavailable: ${analysisError.message}`);

            }

        } catch (error) {

            console.error("Knowledge search error:", error);

            resultsContainer.innerHTML = `

                <article class="knowledge-error-card">

                    <div class="knowledge-error-icon"><i data-lucide="alert-circle"></i></div>

                    <div><h3>Search Error</h3><p>${escapeHtml(error.message)}</p></div>

                </article>`;

            status.textContent = "Search unavailable.";

            clearIRAnalysis("Run another search to load IR analytics.");

        } finally {

            button.disabled = false;

            button.classList.remove("is-loading");

            button.innerHTML = '<i data-lucide="search"></i> Search';

            refreshIcons();

        }

    }

    // --------------------------------------------------------



    // --------------------------------------------------------
    // External website recommendations
    // --------------------------------------------------------
    function safeExternalHref(value) {
        try {
            const parsed = new URL(String(value || ""));
            if ((parsed.protocol === "https:" || parsed.protocol === "http:") && !parsed.username && !parsed.password) {
                return parsed.href;
            }
        } catch (_) {
            // Invalid URLs are omitted rather than rendered as links.
        }
        return null;
    }

    async function searchWebsites(query) {
        if (!webSearchStatus || !webSearchResults) return;

        const requestId = ++webSearchRequestId;
        webSearchStatus.textContent = "Searching the web for related resources...";
        webSearchResults.innerHTML = `
            <div class="ir-placeholder">
                <span class="loading-ring" aria-hidden="true"></span>
                Searching external websites for “${escapeHtml(query)}”...
            </div>`;

        try {
            const response = await fetch("/api/web-search", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: JSON.stringify({ query, count: 6 })
            });

            const data = await response.json().catch(() => ({}));
            if (requestId !== webSearchRequestId) return;

            if (!response.ok || data.success === false) {
                const message = data.error || "External website search is temporarily unavailable.";
                webSearchStatus.textContent = data.code === "not_configured"
                    ? "External website search needs configuration."
                    : "External website search is unavailable.";
                webSearchResults.innerHTML = placeholder(message);
                refreshIcons();
                return;
            }

            const items = Array.isArray(data.results) ? data.results : [];
            webSearchStatus.textContent = items.length
                ? `${items.length} external website result${items.length === 1 ? "" : "s"} for “${query}” · ${data.provider || "Web Search"}`
                : `No external websites found for “${query}”. Try a more specific query.`;

            displayWebsiteResults(items);
        } catch (error) {
            if (requestId !== webSearchRequestId) return;
            console.error("External website search error:", error);
            webSearchStatus.textContent = "External website search is unavailable; internal HR search remains usable.";
            webSearchResults.innerHTML = placeholder("Could not load website recommendations. Check your connection or API configuration and try again.");
            refreshIcons();
        }
    }

    function displayWebsiteResults(items) {
        if (!webSearchResults) return;

        const safeItems = [];
        const seenUrls = new Set();
        for (const item of items) {
            if (!item || typeof item !== "object") continue;
            const href = safeExternalHref(item.url);
            if (!href || seenUrls.has(href.toLowerCase())) continue;
            seenUrls.add(href.toLowerCase());
            let domain = String(item.domain || "").trim();
            if (!domain) {
                try { domain = new URL(href).hostname.replace(/^www\./i, ""); } catch (_) { domain = "External website"; }
            }
            safeItems.push({
                href,
                title: String(item.title || domain || "Website result"),
                domain,
                description: String(item.description || "No description was provided by the search provider.")
            });
        }

        if (!safeItems.length) {
            webSearchResults.innerHTML = placeholder("No usable website results were returned for this query.");
            refreshIcons();
            return;
        }

        webSearchResults.innerHTML = safeItems.map(item => `
            <article class="web-search-result-card">
                <div class="web-search-result-topline">
                    <i data-lucide="globe" aria-hidden="true"></i>
                    <span>${escapeHtml(item.domain)}</span>
                </div>
                <h3><a href="${escapeHtml(item.href)}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.title)}</a></h3>
                <p class="web-search-description">${escapeHtml(item.description)}</p>
                <div class="web-search-result-footer">
                    <a class="web-search-open-link" href="${escapeHtml(item.href)}" target="_blank" rel="noopener noreferrer">
                        Open website <i data-lucide="external-link" aria-hidden="true"></i>
                    </a>
                </div>
            </article>`).join("");
        refreshIcons();
    }


    // Document search results

    // --------------------------------------------------------

    function displayResults(data) {

        const results = Array.isArray(data.results) ? data.results : [];

        const selectedMethod = data.method || method.value;

        const isLM = isLanguageModel(selectedMethod);

        status.innerHTML = `

            <span>Query</span><strong>${escapeHtml(data.query || "")}</strong>

            <span class="status-divider">/</span><span>Method</span>

            <strong>${escapeHtml(methodLabel(selectedMethod))}</strong>

            <span class="status-divider">/</span><span>Results</span>

            <strong>${results.length}</strong>`;

        if (!results.length) {

            resultsContainer.innerHTML = `

                <article class="knowledge-empty-card">

                    <div class="knowledge-empty-icon"><i data-lucide="search-x"></i></div>

                    <h3>No relevant documents found</h3>

                    <p>Try another HR-related query or retrieval method.</p>

                </article>`;

            refreshIcons();

            return;

        }

        resultsContainer.innerHTML = results.map((result, index) => {

            const rank = index + 1;

            const rawScore = numberOrNull(result.score ?? result.display_score);

            const displayedScore = isLM ? formatQueryProbability(rawScore) : formatScore(rawScore);

            const scoreLabel = isLM

                ? "Query Probability P(Q|D)"

                : (isTfidf(selectedMethod) ? "TF-IDF Score" : "BM25 Score");

            const name = result.document || result.document_id || "Unknown document";

            const id = String(result.document_id || result.document || "Unknown").replace(/\.txt$/i, "");

            const matched = Array.isArray(result.matched_terms) ? result.matched_terms : [];

            return `

                <article class="knowledge-result-card ${rank === 1 ? "top-result" : ""}">

                    <div class="knowledge-result-header">

                        <div class="knowledge-result-rank">#${rank}</div>

                        <div class="knowledge-result-title">

                            <h3>${escapeHtml(name)}</h3>

                            <span>Document ID: ${escapeHtml(id)}</span>

                        </div>

                        <div class="knowledge-score">

                            <small>${scoreLabel}</small>

                            <strong>${displayedScore}</strong>

                        </div>

                    </div>

                    <div class="knowledge-result-method">

                        <span>${escapeHtml(methodLabel(selectedMethod))}</span>

                        <span class="result-rank-label">Rank ${rank}</span>

                    </div>

                    ${matched.length ? `

                        <div class="matched-terms-section">

                            <span>Matched terms</span>

                            <div class="matched-terms">

                                ${matched.map(term => `<span class="matched-term">${escapeHtml(term)}</span>`).join("")}

                            </div>

                        </div>` : ""}

                    ${isLM ? `

                        <p class="ir-score-explanation">

                            P(Q|D) is the query probability under this document's language model,

                            not the probability that the document is relevant.

                        </p>` : ""}

                    <div class="ir-result-actions">

                        <button type="button" class="btn btn-primary view-document-btn" data-document-id="${escapeHtml(id)}">

                            <i data-lucide="file-text"></i> View Document

                        </button>

                    </div>

                </article>`;

        }).join("");

        refreshIcons();

    }

    // --------------------------------------------------------

    // Clear analytics

    // --------------------------------------------------------

    function clearIRAnalysis(message) {

        if (comparisonContainer) comparisonContainer.innerHTML = placeholder(message);

        if (evaluationContainer) evaluationContainer.innerHTML = placeholder(message);

        if (passageResults) passageResults.innerHTML = placeholder(message);

        if (extractionContent) extractionContent.innerHTML = placeholder(message);

    }

    function displayIRAnalysis(analysis) {

        displayComparison(analysis.comparison || []);

        displayEvaluation(analysis.evaluation || {});

        displayPassages(analysis.passages || []);

        displayExtraction(analysis.information_extraction || {});

    }

    // --------------------------------------------------------

    // Retrieval model comparison table

    // --------------------------------------------------------

    function displayComparison(rows) {

        if (!comparisonContainer) return;

        if (!Array.isArray(rows) || rows.length === 0) {

            comparisonContainer.innerHTML = placeholder("No cross-model ranking data is available for this query.");

            return;

        }

        const tableRows = rows.map(item => {

            const probability =

                item.language_model_score === null ||

                item.language_model_score === undefined

                    ? "—"

                    : formatQueryProbability(item.language_model_score);

            return `

                <tr>

                    <td><strong>${escapeHtml(item.document || "Unknown")}</strong></td>

                    <td>${safeRank(item.bm25_rank)}

                        <small class="ir-score-subtext">${item.bm25_score == null ? "" : `Score ${formatScore(item.bm25_score)}`}</small>

                    </td>

                    <td>${safeRank(item.tfidf_rank)}

                        <small class="ir-score-subtext">${item.tfidf_score == null ? "" : `Score ${formatScore(item.tfidf_score)}`}</small>

                    </td>

                    <td>${safeRank(item.language_model_rank)}

                        <small class="ir-score-subtext">P=${probability}</small>

                    </td>

                    <td><span class="ir-agreement-pill">${item.method_agreement ?? 0}/3</span></td>

                    <td><strong>${formatScore(item.rrf_score, 5)}</strong></td>

                </tr>`;

        }).join("");

        comparisonContainer.innerHTML = `

            <div class="ir-comparison-table-wrap">

                <table class="ir-comparison-table">

                    <thead>

                        <tr>

                            <th>Document</th>

                            <th>BM25 Rank</th>

                            <th>TF-IDF Rank</th>

                            <th>Language Model Rank</th>

                            <th>Agreement</th>

                            <th>RRF Score</th>

                        </tr>

                    </thead>

                    <tbody>${tableRows}</tbody>

                </table>

            </div>`;

    }

    // --------------------------------------------------------

    // IR Evaluation table

    // --------------------------------------------------------

    function displayEvaluation(evaluation) {

        if (!evaluationContainer) return;

        const methods = evaluation.methods || {};

        const entries = Object.entries(methods);

        const k = Number(evaluation.k || 5);

        if (!entries.length) {

            evaluationContainer.innerHTML = placeholder("Evaluation metrics are unavailable.");

            return;

        }

        const rows = entries.map(([name, metrics]) => `

            <tr>

                <td><span class="ir-evaluation-method"><span class="ir-model-dot"></span>${escapeHtml(name)}</span></td>

                <td>${formatScore(metrics.precision_at_k)}</td>

                <td>${formatScore(metrics.recall_at_k)}</td>

                <td>${formatScore(metrics.f1)}</td>

                <td>${formatScore(metrics.mrr)}</td>

            </tr>`).join("");

        evaluationContainer.innerHTML = `

            <div class="ir-evaluation-table-wrap">

                <table class="ir-evaluation-table">

                    <thead>

                        <tr>

                            <th>Retrieval Method</th>

                            <th>Precision@${k}</th>

                            <th>Recall@${k}</th>

                            <th>F1 Score</th>

                            <th>Mean Reciprocal Rank (MRR)</th>

                        </tr>

                    </thead>

                    <tbody>${rows}</tbody>

                </table>

            </div>

            <div class="ir-evaluation-note">

                ${Number(evaluation.benchmark_queries || 0)} curated HR benchmark queries ·

                ${escapeHtml(evaluation.judgement_type || "Domain relevance judgments")}

            </div>`;

    }

    // --------------------------------------------------------

    // Passage retrieval: individual cards, not a table

    // --------------------------------------------------------

    function displayPassages(items) {

        if (!passageResults) return;

        if (!Array.isArray(items) || items.length === 0) {

            passageResults.innerHTML = placeholder("No matching passages were found. Try a more specific query.");

            return;

        }

        passageResults.innerHTML = items.map((passage, index) => {

            const matched = Array.isArray(passage.matched_terms) ? passage.matched_terms : [];

            return `

                <article class="ir-passage-card">

                    <div class="ir-passage-heading">

                        <div class="ir-passage-document">

                            <span class="ir-passage-rank">Passage ${index + 1}</span>

                            <h3>${escapeHtml(passage.document || "Unknown document")}</h3>

                            <div class="ir-passage-meta">Passage ID: ${escapeHtml(passage.passage_id ?? "—")}</div>

                        </div>

                        <div class="ir-passage-probability">

                            <small>Query Probability P(Q|Passage)</small>

                            <strong>${formatQueryProbability(passage.score)}</strong>

                        </div>

                    </div>

                    <p class="ir-passage-text">${escapeHtml(passage.text || "")}</p>

                    ${matched.length ? `

                        <div class="matched-terms-section ir-passage-matches">

                            <span>Matched terms</span>

                            <div class="matched-terms">

                                ${matched.map(term => `<span class="matched-term">${escapeHtml(term)}</span>`).join("")}

                            </div>

                        </div>` : ""}

                </article>`;

        }).join("");

    }

    // --------------------------------------------------------

    // Information extraction

    // --------------------------------------------------------

    function displayExtraction(data) {

        if (!extractionContent) return;

        if (!data || !data.available) {

            extractionContent.innerHTML = placeholder("No extractable policy information is available for the top result.");

            return;

        }

        const entities = Array.isArray(data.entities) ? data.entities : [];

        const facts = Array.isArray(data.numeric_facts) ? data.numeric_facts : [];

        const sentences = Array.isArray(data.key_sentences) ? data.key_sentences : [];

        extractionContent.innerHTML = `

            <div class="ir-extraction-grid">

                <article class="ir-extraction-card">

                    <span>Top Document</span>

                    <strong>${escapeHtml(data.document || "Unknown")}</strong>

                </article>

                <article class="ir-extraction-card">

                    <span>Policy Entities</span>

                    <div class="ir-extraction-tags">

                        ${entities.length

                            ? entities.map(entity => `<span class="matched-term">${escapeHtml(entity)}</span>`).join("")

                            : `<small class="ir-muted">None detected</small>`}

                    </div>

                </article>

                <article class="ir-extraction-card">

                    <span>Numeric Facts</span>

                    <div class="ir-fact-list">

                        ${facts.length

                            ? facts.map(fact => `<p>${escapeHtml(fact)}</p>`).join("")

                            : `<small class="ir-muted">No numeric fact detected</small>`}

                    </div>

                </article>

            </div>

            <article class="ir-extracted-sentences">

                <h3>Key Extracted Sentences</h3>

                ${sentences.length

                    ? sentences.map(sentence => `<p>${escapeHtml(sentence)}</p>`).join("")

                    : `<p class="ir-muted">No key policy sentences detected.</p>`}

            </article>`;

    }

    // --------------------------------------------------------

    // View Document modal

    // --------------------------------------------------------

    function createDocumentModal() {

        if (document.getElementById("documentModal")) return;

        const modal = document.createElement("div");

        modal.id = "documentModal";

        modal.className = "ir-document-modal-backdrop";

        modal.innerHTML = `

            <div class="ir-document-modal" role="dialog" aria-modal="true" aria-labelledby="documentModalTitle">

                <header class="ir-document-modal-header">

                    <div>

                        <h2 id="documentModalTitle">HR Document</h2>

                        <div id="documentModalCategory" class="ir-document-modal-category"></div>

                    </div>

                    <button type="button" id="closeDocumentModal" class="ir-document-modal-close" aria-label="Close document">

                        <i data-lucide="x"></i>

                    </button>

                </header>

                <div class="ir-document-modal-content" id="documentModalBody">

                    Loading HR document...

                </div>

                <footer class="ir-document-modal-footer">

                    <button type="button" id="closeDocumentModalFooter" class="btn btn-secondary">Close</button>

                </footer>

            </div>`;

        document.body.appendChild(modal);

        document.getElementById("closeDocumentModal")

            .addEventListener("click", closeDocumentModal);

        document.getElementById("closeDocumentModalFooter")

            .addEventListener("click", closeDocumentModal);

        modal.addEventListener("click", event => {

            if (event.target === modal) closeDocumentModal();

        });

        refreshIcons();

    }

    function closeDocumentModal() {

        const modal = document.getElementById("documentModal");

        if (modal) modal.style.display = "none";

    }

    async function openDocument(documentId) {

        if (!documentId) return;

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

            const response = await fetch(`/api/document/${encodeURIComponent(documentId)}`, {

                method: "GET",

                headers: { "Accept": "application/json" }

            });

            const data = await response.json();

            if (!response.ok || data.success === false) {

                throw new Error(data.error || "Unable to load document.");

            }

            title.textContent = data.title || documentId;

            category.textContent = data.category || "HR Knowledge";

            body.textContent = data.content || "Document content is empty.";

        } catch (error) {

            title.textContent = "Document unavailable";

            category.textContent = "";

            body.textContent = error.message;

        }

        refreshIcons();

    }

    // --------------------------------------------------------

    // Events

    // --------------------------------------------------------

    resultsContainer.addEventListener("click", event => {

        const viewButton = event.target.closest(".view-document-btn");

        if (viewButton) openDocument(viewButton.dataset.documentId);

    });

    quickSearchButtons.forEach(quickButton => {

        quickButton.addEventListener("click", () => performSearch(quickButton.dataset.query));

    });

    button.addEventListener("click", () => performSearch());

    input.addEventListener("keydown", event => {

        if (event.key === "Enter") performSearch();

    });

    document.addEventListener("keydown", event => {

        if (event.key === "Escape") closeDocumentModal();

    });

    updateMethodUI();

    refreshIcons();

});