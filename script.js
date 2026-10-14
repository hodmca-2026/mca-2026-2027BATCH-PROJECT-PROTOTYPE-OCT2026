"use strict";

/* =========================================================
   PHISHGUARD - FRONTEND JAVASCRIPT
   ========================================================= */

const API_BASE_URL = String(
    window.PHISHGUARD_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");
const API_URL = `${API_BASE_URL}/api/v1/scan`;
const HISTORY_KEY = "phishguardHistory";

/* =========================================================
   HELPER FUNCTIONS
   ========================================================= */

function $(id) {
    return document.getElementById(id);
}

function safeNumber(value, fallback = 0) {
    const n = Number(value);
    return Number.isFinite(n) ? n : fallback;
}

function formatDate(date = new Date()) {
    return date.toLocaleString();
}

function escapeHTML(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function isShortenedURL(url) {
    if (!url) return false;

    try {
        const host = new URL(url).hostname.toLowerCase();

        const shorteners = [
            "bit.ly",
            "tinyurl.com",
            "t.co",
            "goo.gl",
            "is.gd",
            "ow.ly",
            "buff.ly",
            "rebrand.ly",
            "cutt.ly",
            "shorturl.at",
            "tiny.cc"
        ];

        return shorteners.some(
            domain => host === domain || host.endsWith("." + domain)
        );
    } catch {
        return false;
    }
}

function validateURL(value) {
    if (!value || !value.trim()) {
        return {
            valid: false,
            message: "Please enter a website URL."
        };
    }

    let url = value.trim();

    if (!/^https?:\/\//i.test(url)) {
        url = "https://" + url;
    }

    try {
        const parsed = new URL(url);
        const hostname = (parsed.hostname || "").toLowerCase();

        if (!hostname) {
            return {
                valid: false,
                message: "Please enter a valid website URL."
            };
        }

        if (hostname === "localhost") {
            return {
                valid: true,
                url
            };
        }

        if (!hostname.includes(".") || hostname.startsWith(".") || hostname.endsWith(".")) {
            return {
                valid: false,
                message: "Invalid URL. Enter a valid hostname such as https://google.com"
            };
        }

        const tld = hostname.split(".").pop() || "";
        if (!tld || tld.length < 2) {
            return {
                valid: false,
                message: "Invalid URL. Enter a valid hostname such as https://google.com"
            };
        }

        return {
            valid: true,
            url
        };
    } catch {
        return {
            valid: false,
            message: "Invalid URL. Example: https://google.com"
        };
    }
}

/* =========================================================
   DOM ELEMENTS
   ========================================================= */

const urlInput = $("urlInput");
const clearInput = $("clearInput");
const analyzeBtn = $("analyzeBtn");
const analyzeText = document.querySelector(".analyze-btn-text");
const analyzeArrow = document.querySelector(".analyze-btn-icon");

const scannerMessage = $("scannerMessage");
const scannerMessageText = $("scannerMessageText");
const scanLoading = $("scanLoading");
const scanAgainBtn = $("scanAgainBtn");

/* Result */

const riskScore = $("riskScore");
const riskGauge = $("riskGauge");
const riskStatus = $("riskStatus");
const riskLevel = $("riskLevel");

const verdictIcon = $("verdictIcon");
const verdictTitle = $("verdictTitle");
const verdictText = $("verdictText");
const verdictDescription = $("verdictDescription");

const confidenceValue = $("confidenceValue");
const confidenceBar = $("confidenceFill");

const resultStatus = $("resultStatus");

/* Explanation */

const explanationTitle = $("explanationTitle");
const explanationText = $("explanationText");
const aiExplanation = $("aiExplanation");
const reasonList = $("reasonList");
const emptyHistory = $("emptyHistory");

/* Features */

const featureHttpsStatus = $("featureHttpsStatus");
const featureLengthStatus = $("featureLengthStatus");
const featureIPStatus = $("featureIPStatus");
const featureAtStatus = $("featureAtStatus");
const featureSubdomainStatus = $("featureSubdomainStatus");
const featureSpecialStatus = $("featureSpecialStatus");
const featureShortenerStatus = $("featureShortenerStatus");
const featureKeywordsStatus = $("featureKeywordsStatus");

/* Security checks */

const dnsCheckIcon = $("dnsCheckIcon");
const dnsCheckStatus = $("dnsCheckStatus");
const sslCheckIcon = $("sslCheckIcon");
const sslCheckStatus = $("sslCheckStatus");
const urlCheckIcon = $("urlCheckIcon");
const urlCheckStatus = $("urlCheckStatus");
const mlCheckIcon = $("mlCheckIcon");
const mlCheckStatus = $("mlCheckStatus");

/* Report */

const reportUrl = $("reportUrl");
const reportTime = $("reportTime");
const reportVerdict = $("reportVerdict");
const reportRiskScore = $("reportRiskScore");
const reportConfidence = $("reportConfidence");
const reportStatus = $("reportStatus");
const reportSummary = $("reportSummary");
const reportIRSummary = $("reportIRSummary");
const reportBadge = $("reportBadge");
const printReportBtn = $("printReportBtn");

/* History */

const historyList = $("historyList");
const historyTableBody = $("historyTableBody");
const clearHistoryBtn = $("clearHistoryBtn");
const historyFilterButtons = document.querySelectorAll(".history-actions [data-filter]");
let activeHistoryFilter = "all";

/* Information retrieval */

const irOverallStatus = $("irOverallStatus");
const irLanguageScore = $("irLanguageScore");
const irLanguageStatus = $("irLanguageStatus");
const irSuspiciousTerms = $("irSuspiciousTerms");
const irPageRankScore = $("irPageRankScore");
const irPageRankRank = $("irPageRankRank");
const irGraphNodes = $("irGraphNodes");
const irGraphEdges = $("irGraphEdges");
const irPageRankStatus = $("irPageRankStatus");
const irGraphDetails = $("irGraphDetails");
const irRecommendations = $("irRecommendations");
const irRecommendationStatus = $("irRecommendationStatus");
const irDAATResults = $("irDAATResults");
const irDAATStatus = $("irDAATStatus");

/* Dashboard stats */

const totalScans = $("totalScans");
const threatsDetected = $("threatsDetected");
const safeUrls = $("safeUrls");
const modelStatus = $("modelStatus");


/* =========================================================
   MESSAGE FUNCTIONS
   ========================================================= */

function showScannerMessage(message, type = "error") {
    if (!scannerMessage) return;

    scannerMessage.style.display = "block";

    if (scannerMessageText) {
        scannerMessageText.textContent = message;
    } else {
        scannerMessage.textContent = message;
    }

    scannerMessage.classList.remove(
        "error",
        "success",
        "warning"
    );

    scannerMessage.classList.add(type);
}

function hideScannerMessage() {
    if (scannerMessage) {
        scannerMessage.style.display = "none";
    }
}


/* =========================================================
   LOADING
   ========================================================= */

function setLoading(isLoading) {
    if (analyzeBtn) {
        analyzeBtn.disabled = isLoading;
    }

    if (analyzeText) {
        analyzeText.textContent =
            isLoading ? "Analyzing..." : "Analyze URL";
    }

    if (analyzeArrow) {
        analyzeArrow.style.display =
            isLoading ? "none" : "inline";
    }

    if (scanLoading) {
        scanLoading.style.display =
            isLoading ? "block" : "none";
    }
}


/* =========================================================
   BACKEND API
   ========================================================= */

async function analyzeWithBackend(url) {

    const response = await fetch(API_URL, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            url: url
        })
    });

    const payload = await response.json();
    if (!response.ok) {
        const error = new Error(payload.detail || `Backend error: ${response.status}`);
        error.status = response.status;
        throw error;
    }

    return payload;
}


/* =========================================================
   CONVERT BACKEND RESULT
   ========================================================= */

function convertBackendResult(data) {

    if (!data || data.valid === false) {
        return {
            valid: false,
            url: data?.url || "",
            prediction: "Invalid URL",
            classification: "invalid",
            risk_score: 0,
            confidence: 0,
            url_security: {},
            dns: {},
            ssl: {},
            ml: {},
            reasons: [],
            risk_explanation: data?.detail || "Invalid URL or unable to verify the hostname.",
            explanation: data?.detail || "Invalid URL or unable to verify the hostname.",
            ir_analysis: null
        };
    }

    const security = data.url_security || {};
    const dns = data.dns || {};
    const ssl = data.ssl || {};
    const ml = data.ml || {};
    const rawExplanation = data.explanation ?? data.risk_explanation ?? ml.explanation ?? "";

    let confidence = safeNumber(
        data.confidence ?? ml.confidence,
        0
    );

    if (confidence >= 0 && confidence <= 1) {
        confidence = confidence * 100;
    }

    confidence = Math.round(confidence * 10) / 10;

    const rawClassification = String(
        data.classification ||
        data.risk_classification ||
        ml.classification ||
        ""
    ).toLowerCase();

    const riskScoreValue = safeNumber(
        data.risk_score ??
        data.risk_engine?.risk_score,
        0
    );

    const isPhishing =
        rawClassification.includes("phish") ||
        rawClassification.includes("malicious") ||
        rawClassification.includes("danger") ||
        riskScoreValue >= 30;
    const isUnverifiable =
        data.verifiable === false || rawClassification.includes("unverifiable");

    const prediction =
        isPhishing ? "Phishing" : isUnverifiable ? "Unable to verify URL" : "Safe";

    return {
        valid: true,
        verifiable: !isUnverifiable,
        url: data.url || "",
        prediction,
        classification:
            data.classification ||
            data.risk_classification ||
            ml.classification ||
            "",
        risk_score: riskScoreValue,
        confidence,
        url_security: security,
        dns,
        ssl,
        ml,
        reasons: Array.isArray(data.reasons)
            ? data.reasons
            : Array.isArray(data.signals)
                ? data.signals
                : Array.isArray(data.url_security_reasons)
                    ? data.url_security_reasons
                    : Array.isArray(ml.signals)
                        ? ml.signals
                        : [],
        risk_explanation: normalizeExplanation(rawExplanation),
        explanation: normalizeExplanation(rawExplanation),
        ir_analysis: data.ir_analysis || null
    };
}

function normalizeExplanation(value) {
    if (Array.isArray(value)) {
        return value
            .filter(item => item !== null && item !== undefined && String(item).trim())
            .map(item => String(item).trim())
            .join(" ");
    }

    if (typeof value === "string") {
        return value.trim();
    }

    return "";
}


/* =========================================================
   DISPLAY RESULT
   ========================================================= */

function clearSecurityCheck(element, icon) {
    if (element) {
        element.textContent = "--";
        element.classList.remove("secure", "warning", "danger");
    }
    if (icon) {
        icon.textContent = "?";
    }
}

function resetScanDetails(result) {
    const state = result?.failureType || "invalid";
    const isInvalid = state === "invalid";
    const isScanning = state === "scanning";
    const title = isInvalid ? "Invalid URL" : isScanning ? "Analyzing URL" : "Scan Unavailable";
    const message = result?.risk_explanation || (isInvalid
        ? "Invalid URL. Enter a valid hostname such as https://google.com"
        : isScanning
            ? "Running the security and machine-learning checks."
            : "The scan could not be completed. Please try again.");

    if (riskScore) riskScore.textContent = "--";
    if (riskLevel) riskLevel.textContent = isInvalid ? "Invalid URL" : isScanning ? "Analyzing" : "Unavailable";
    if (riskStatus) riskStatus.textContent = isInvalid ? "INVALID" : isScanning ? "SCANNING" : "UNAVAILABLE";
    if (riskGauge) riskGauge.style.strokeDashoffset = "0";
    if (verdictTitle) verdictTitle.textContent = title;
    if (verdictText) verdictText.textContent = title;
    if (verdictIcon) verdictIcon.textContent = isInvalid ? "!" : isScanning ? "…" : "?";
    if (verdictDescription) verdictDescription.textContent = message;
    if (confidenceValue) confidenceValue.textContent = "--";
    if (confidenceBar) confidenceBar.style.width = "0%";
    if (resultStatus) resultStatus.textContent = isInvalid ? "Validation Failed" : isScanning ? "Analyzing" : "Backend Unavailable";

    [
        featureHttpsStatus,
        featureLengthStatus,
        featureIPStatus,
        featureAtStatus,
        featureSubdomainStatus,
        featureSpecialStatus,
        featureShortenerStatus,
        featureKeywordsStatus
    ].forEach(element => {
        if (element) element.textContent = "--";
    });

    clearSecurityCheck(dnsCheckStatus, dnsCheckIcon);
    clearSecurityCheck(sslCheckStatus, sslCheckIcon);
    clearSecurityCheck(urlCheckStatus, urlCheckIcon);
    clearSecurityCheck(mlCheckStatus, mlCheckIcon);

    displayExplanation(result);
    displayIRAnalysis(null, result?.url || "", isScanning ? "Analyzing scan" : "Unavailable");
    updateReport(result);

    if (modelStatus && state === "error") {
        modelStatus.textContent = "Unavailable";
    } else if (modelStatus && isScanning) {
        modelStatus.textContent = "Checking...";
    }
}

function displayResult(result) {

    if (!result || result.valid === false) {
        resetScanDetails(result);
        return;
    }

    const isUnverifiable = result.verifiable === false;

    const score = safeNumber(
        result.risk_score,
        0
    );

    const confidence = safeNumber(
        result.confidence,
        0
    );

    /* Risk score */

    if (riskScore) {
        riskScore.textContent =
            Math.round(score);
    }

    /* Risk level */

    if (riskLevel) {

        riskLevel.textContent =
            isUnverifiable
                ? "Unverified"
                : score <= 30
                ? "Low Risk"
                : score <= 70
                    ? "Medium Risk"
                    : "High Risk";
    }

    /* Risk status */

    if (riskStatus) {

        riskStatus.textContent =
            isUnverifiable
                ? "UNVERIFIED"
                : score <= 30
                ? "LOW"
                : score <= 70
                    ? "MEDIUM"
                    : "HIGH";
    }

    /* Verdict */

    if (verdictTitle) {
        verdictTitle.textContent =
            result.prediction === "Phishing" ? "Phishing URL" : isUnverifiable ? "Unable to Verify URL" : "Safe URL";
    }

    if (verdictText) {
        verdictText.textContent =
            result.prediction === "Phishing" ? "Phishing URL" : isUnverifiable ? "Unable to Verify URL" : "Safe URL";
    }

    if (verdictDescription) {
        verdictDescription.textContent = getMLVerdictComparison(result)
            || (result.prediction === "Phishing"
                ? "This URL has been classified as potentially dangerous."
                : isUnverifiable
                    ? "The hostname did not resolve, so this URL cannot be verified as safe."
                    : "The security model has classified this URL as low risk.");
    }

    /* Confidence */

    if (confidenceValue) {
        confidenceValue.textContent =
            `${confidence.toFixed(1)}%`;
    }

    if (confidenceBar) {
        confidenceBar.style.width =
            `${Math.min(100, confidence)}%`;
    }

    /* Gauge */

    if (riskGauge) {

        const circumference = 314;

        const offset =
            circumference -
            (Math.min(100, score) / 100) *
            circumference;

        riskGauge.style.strokeDasharray =
            `${circumference}`;

        riskGauge.style.strokeDashoffset =
            `${offset}`;
    }

    if (resultStatus) {
        resultStatus.textContent =
            "Analysis Complete";
    }

    displayFeatures(result);

    displaySecurityChecks(result);

    displayExplanation(result);

    displayIRAnalysis(result.ir_analysis);

    if (modelStatus) {
        modelStatus.textContent = result.ml?.classification ? "Available" : "Unavailable";
    }

    updateReport(result);

    updateDashboardStats();
}


/* =========================================================
   INFORMATION RETRIEVAL
   ========================================================= */

function displayIRAnalysis(analysis, currentUrl = "", emptyState = "Unavailable") {
    if (!analysis || typeof analysis !== "object") {
        if (irOverallStatus) {
            irOverallStatus.textContent = emptyState;
        }
        if (irLanguageScore) irLanguageScore.textContent = emptyState === "Analyzing scan" ? "Analyzing..." : "Unavailable";
        if (irLanguageStatus) irLanguageStatus.textContent = emptyState === "Analyzing scan" ? "Awaiting scan result" : "Unavailable";
        if (irSuspiciousTerms) irSuspiciousTerms.textContent = "No data available.";
        if (irPageRankScore) irPageRankScore.textContent = emptyState === "Analyzing scan" ? "Analyzing..." : "Unavailable";
        if (irPageRankRank) irPageRankRank.textContent = "--";
        if (irGraphNodes) irGraphNodes.textContent = "--";
        if (irGraphEdges) irGraphEdges.textContent = "--";
        if (irPageRankStatus) irPageRankStatus.textContent = emptyState === "Analyzing scan" ? "Awaiting scan result" : "Insufficient graph data";
        if (irRecommendations) irRecommendations.innerHTML = "<li>No similar URLs found.</li>";
        if (irRecommendationStatus) irRecommendationStatus.textContent = emptyState === "Analyzing scan" ? "Awaiting scan result" : "Unavailable";
        if (irDAATResults) irDAATResults.innerHTML = "<li>No matching historical URLs found.</li>";
        if (irDAATStatus) irDAATStatus.textContent = emptyState === "Analyzing scan" ? "Awaiting scan result" : "Unavailable";
        return;
    }

    const language = analysis.language_model || {};
    const pageRank = analysis.pagerank || {};
    const recommendations = analysis.content_recommendations || {};
    const documentRetrieval = analysis.document_retrieval || {};
    const languageAvailable = language.status === "available";
    const languageInsufficient = language.status !== "available"
        && /required|insufficient/i.test(String(language.message || ""));
    const graphNodeCount = Number(pageRank.graph_nodes);
    const graphEdgeCount = Number(pageRank.graph_edges);
    const pageRankAvailable = pageRank.status === "available"
        && Number.isFinite(graphNodeCount)
        && graphNodeCount > 1
        && Number.isFinite(graphEdgeCount)
        && graphEdgeCount > 0;
    const recommendationsAvailable = recommendations.status === "available";

    if (irOverallStatus) {
        irOverallStatus.textContent = analysis.status === "available"
            ? `IR analysis calculated from ${safeNumber(analysis.corpus_size, 0)} historical URLs.`
            : analysis.message || "IR analysis is temporarily unavailable.";
    }

    const languageScore = language.score;
    if (irLanguageScore) {
        irLanguageScore.textContent = languageAvailable && typeof languageScore === "number" && Number.isFinite(languageScore)
            ? `${(languageScore * 100).toFixed(1)}%`
            : languageInsufficient ? "Insufficient data" : "Unavailable";
    }
    if (irLanguageStatus) {
        irLanguageStatus.textContent = languageAvailable
            ? `${safeNumber(language.training_documents, 0)} labeled history records`
            : languageInsufficient ? "Insufficient corpus data" : language.message || "Language model unavailable";
    }
    if (irSuspiciousTerms) {
        const terms = Array.isArray(language.suspicious_terms)
            ? language.suspicious_terms.filter(term => typeof term === "string" && term.trim())
            : [];
        irSuspiciousTerms.textContent = terms.length ? terms.join(", ") : "No corpus-derived terms identified.";
    }

    const graphScore = pageRank.score;
    if (irPageRankScore) {
        irPageRankScore.textContent = pageRankAvailable && typeof graphScore === "number" && Number.isFinite(graphScore)
            ? graphScore.toFixed(6)
            : pageRank.status === "available" ? "Insufficient data" : "Unavailable";
    }
    if (irPageRankRank) {
        const rank = Number(pageRank.rank);
        irPageRankRank.textContent = pageRankAvailable && Number.isInteger(rank) && rank > 0 ? `#${rank}` : "--";
    }
    if (irPageRankStatus) {
        irPageRankStatus.textContent = pageRankAvailable
            ? "PageRank calculated over the local relationship graph"
            : pageRank.status === "available" ? "Insufficient graph data" : pageRank.message || "PageRank unavailable";
    }
    if (irGraphDetails) {
        irGraphDetails.textContent = "Calculated from URL/domain relationships in local scan history; not Google's live PageRank.";
    }
    if (irGraphNodes) {
        irGraphNodes.textContent = Number.isFinite(graphNodeCount) ? String(graphNodeCount) : "--";
    }
    if (irGraphEdges) {
        irGraphEdges.textContent = Number.isFinite(graphEdgeCount) ? String(graphEdgeCount) : "--";
    }

    let displayedRecommendationCount = 0;
    if (irRecommendations) {
        irRecommendations.innerHTML = "";
        const matches = Array.isArray(recommendations.recommendations)
            ? recommendations.recommendations
            : [];
        const normalizedCurrentUrl = normalizeURLForMatch(currentUrl);
        const validMatches = matches.filter(item =>
            item
            && typeof item.url === "string"
            && item.url.trim()
            && normalizeURLForMatch(item.url) !== normalizedCurrentUrl
            && typeof item.similarity === "number"
            && Number.isFinite(item.similarity)
            && item.similarity > 0
            && item.similarity <= 1
        );
        displayedRecommendationCount = validMatches.length;

        if (!validMatches.length) {
            const item = document.createElement("li");
            item.textContent = "No similar URLs found.";
            irRecommendations.appendChild(item);
        } else {
            validMatches.slice(0, 3).forEach(match => {
                const item = document.createElement("li");
                const url = document.createElement("span");
                const similarity = document.createElement("strong");
                const percentage = match.similarity * 100;
                url.className = "ir-recommendation-url";
                url.textContent = match.url;
                similarity.textContent = `${Math.max(0, Math.min(100, percentage)).toFixed(1)}%`;
                item.append(url, similarity);
                irRecommendations.appendChild(item);
            });
        }
    }
    if (irRecommendationStatus) {
        irRecommendationStatus.textContent = recommendationsAvailable
            ? displayedRecommendationCount
                ? `${displayedRecommendationCount} historical match${displayedRecommendationCount === 1 ? "" : "es"}`
                : "No similar URLs found."
            : recommendations.message || "Recommendations unavailable";
    }

    const retrievedDocuments = Array.isArray(documentRetrieval.results)
        ? documentRetrieval.results.filter(item =>
            item
            && typeof item.url === "string"
            && item.url.trim()
            && typeof item.score === "number"
            && Number.isFinite(item.score)
            && item.score > 0
            && item.score <= 1
        )
        : [];
    if (irDAATResults) {
        irDAATResults.innerHTML = "";
        if (!retrievedDocuments.length) {
            const item = document.createElement("li");
            item.textContent = "No matching historical URLs found.";
            irDAATResults.appendChild(item);
        } else {
            retrievedDocuments.slice(0, 5).forEach(match => {
                const item = document.createElement("li");
                const url = document.createElement("span");
                const score = document.createElement("strong");
                url.className = "ir-recommendation-url";
                url.textContent = match.url;
                score.textContent = `${(match.score * 100).toFixed(1)}%`;
                item.append(url, score);
                irDAATResults.appendChild(item);
            });
        }
    }
    if (irDAATStatus) {
        irDAATStatus.textContent = documentRetrieval.status === "available"
            ? `${retrievedDocuments.length} DAAT match${retrievedDocuments.length === 1 ? "" : "es"} (cosine TF-IDF)`
            : documentRetrieval.message || "DAAT retrieval unavailable";
    }
}

function normalizeURLForMatch(value) {
    try {
        const candidate = /^https?:\/\//i.test(String(value || ""))
            ? String(value).trim()
            : `https://${String(value || "").trim()}`;
        const parsed = new URL(candidate);
        const pathname = parsed.pathname.replace(/\/+$/, "");
        return `${parsed.protocol}//${parsed.host}${pathname}${parsed.search}`.toLowerCase();
    } catch {
        return "";
    }
}


/* =========================================================
   FEATURES
   ========================================================= */

function displayFeatures(result) {

    const security = result.url_security || {};
    const url = result.url || "";

    if (featureHttpsStatus) {
        featureHttpsStatus.textContent =
            security.uses_https ? "Secure" : "Warning";
    }

    if (featureLengthStatus) {
        featureLengthStatus.textContent =
            safeNumber(security.url_length, url.length);
    }

    if (featureIPStatus) {
        featureIPStatus.textContent =
            security.has_ip_address ? "Detected" : "Not Detected";
    }

    if (featureAtStatus) {
        featureAtStatus.textContent =
            security.has_at_symbol ? "Detected" : "Not Detected";
    }

    if (featureSubdomainStatus) {
        featureSubdomainStatus.textContent =
            safeNumber(security.subdomain_count, 0);
    }

    if (featureSpecialStatus) {
        featureSpecialStatus.textContent =
            safeNumber(security.special_char_count, 0);
    }

    if (featureShortenerStatus) {
        featureShortenerStatus.textContent =
            isShortenedURL(url) ? "Detected" : "Not Detected";
    }

    const keywordCount = safeNumber(security.suspicious_keyword_count, 0);

    if (featureKeywordsStatus) {
        featureKeywordsStatus.textContent =
            keywordCount > 0 ? `${keywordCount} Detected` : "None Detected";
    }
}


/* =========================================================
   SECURITY CHECKS
   ========================================================= */

function setSecurityCheck(element, text, type) {

    if (!element) return;

    element.textContent = text;

    element.classList.remove(
        "secure",
        "warning",
        "danger"
    );

    element.classList.add(type);
}


function displaySecurityChecks(data) {

    if (!data) {
        return;
    }

    const security = data.url_security || {};
    const dns = data.dns || {};
    const ssl = data.ssl || {};
    const ml = data.ml || {};

    setSecurityCheck(
        dnsCheckStatus,
        dns.resolves ? "Resolved" : "Not Resolved",
        dns.resolves ? "secure" : "warning"
    );

    setSecurityCheck(
        sslCheckStatus,
        ssl.valid ? "Valid" : "Invalid / Unavailable",
        ssl.valid ? "secure" : "warning"
    );

    setSecurityCheck(
        urlCheckStatus,
        security.has_ip_address || security.has_at_symbol || security.suspicious_keyword_count > 0
            ? "Warning"
            : "Secure",
        security.has_ip_address || security.has_at_symbol || security.suspicious_keyword_count > 0
            ? "warning"
            : "secure"
    );

    const mlClassification = String(ml.classification || "").toLowerCase();
    const mlPhishing = mlClassification.includes("phish");
    const mlLegitimate = mlClassification.includes("legitimate");
    setSecurityCheck(
        mlCheckStatus,
        mlPhishing ? "Phishing" : mlLegitimate ? "Legitimate" : "Unavailable",
        mlPhishing ? "danger" : mlLegitimate ? "secure" : "warning"
    );

    if (dnsCheckIcon) {
        dnsCheckIcon.textContent = dns.resolves ? "✓" : "!";
    }

    if (sslCheckIcon) {
        sslCheckIcon.textContent = ssl.valid ? "✓" : "!";
    }

    if (urlCheckIcon) {
        urlCheckIcon.textContent = "✓";
    }

    if (mlCheckIcon) {
        mlCheckIcon.textContent = mlPhishing ? "!" : mlLegitimate ? "✓" : "?";
    }
}


/* =========================================================
   EXPLANATION
   ========================================================= */

function displayExplanation(result) {

    const explanationValue = normalizeExplanation(
        result?.risk_explanation || result?.explanation || ""
    );
    const resultMismatch = getMLVerdictComparison(result);

    const fallbackText =
        result?.valid === false
            ? explanationValue || "The scan could not be completed."
            : result?.prediction === "Phishing"
            ? "The security analysis identified indicators associated with phishing."
            : result?.prediction === "Unable to verify URL"
                ? "The hostname did not resolve, so this URL cannot be verified as safe."
                : "The URL passed the available security checks with a low calculated risk.";

    const displayText = [resultMismatch, explanationValue || fallbackText]
        .filter(Boolean)
        .join(" ");

    if (explanationTitle) {
        explanationTitle.textContent =
            resultMismatch
                ? "ML result and overall assessment differ"
                : result?.valid === false
                    ? result.failureType === "scanning"
                        ? "Analysis in progress"
                        : result.failureType === "error" ? "Scan unavailable" : "URL validation failed"
                    : result.prediction === "Phishing"
                ? "Potential phishing indicators detected"
                : "No major phishing indicators detected";
    }

    if (aiExplanation) {
        aiExplanation.textContent = displayText;
    }

    if (explanationText) {
        explanationText.textContent = displayText;
    }

    if (!reasonList) {
        return;
    }

    reasonList.innerHTML = "";

    if (result?.valid === false) {
        const li = document.createElement("li");
        li.textContent = explanationValue || "No data available.";
        reasonList.appendChild(li);
        return;
    }

    let reasons = [];

    if (Array.isArray(result.reasons)) {
        reasons = result.reasons;
    }

    if (reasons.length === 0) {

        const li = document.createElement("li");

        li.textContent =
            result.prediction === "Phishing"
                ? "Potentially suspicious URL characteristics were detected."
                : "No additional suspicious indicators were reported.";

        reasonList.appendChild(li);

        return;
    }

    reasons.forEach(reason => {

        if (
            reason !== null &&
            reason !== undefined &&
            String(reason).trim()
        ) {

            const li =
                document.createElement("li");

            li.textContent =
                String(reason);

            reasonList.appendChild(li);
        }
    });
}

function getMLVerdictComparison(result) {
    if (!result || result.valid === false) {
        return "";
    }

    const mlClassification = String(result.ml?.classification || "").toLowerCase();
    const mlVerdict = mlClassification.includes("phish")
        ? "Phishing"
        : mlClassification.includes("legitimate")
            ? "Legitimate"
            : "";
    if (!mlVerdict) {
        return "";
    }

    const risk = Math.round(safeNumber(result.risk_score, 0));
    if (mlVerdict === "Legitimate" && result.prediction === "Phishing") {
        return `The ML model classified the URL as legitimate, but additional security indicators increased the overall risk score to ${risk}/100, resulting in a potentially dangerous overall assessment.`;
    }
    if (mlVerdict === "Phishing" && result.prediction === "Safe") {
        return `The ML model classified the URL as phishing, while the combined security assessment calculated an overall risk score of ${risk}/100.`;
    }
    if (mlVerdict === "Legitimate" && result.verifiable === false) {
        return `The ML model classified the URL as legitimate, but the hostname could not be verified; this result is not presented as safe. The overall risk score is ${risk}/100.`;
    }
    return "";
}

function getIRReportSummary(analysis, currentUrl) {
    if (!analysis || typeof analysis !== "object") {
        return "IR analysis unavailable.";
    }

    const language = analysis.language_model || {};
    const pageRank = analysis.pagerank || {};
    const recommendations = analysis.content_recommendations || {};
    const languageScore = Number(language.score);
    const suspiciousTerms = Array.isArray(language.suspicious_terms)
        ? language.suspicious_terms.filter(term => typeof term === "string" && term.trim())
        : [];
    const languageText = language.status === "available" && Number.isFinite(languageScore)
        ? `Language-model phishing likelihood ${(languageScore * 100).toFixed(1)}% from ${safeNumber(language.training_documents, 0)} labeled records; phishing-associated terms: ${suspiciousTerms.length ? suspiciousTerms.join(", ") : "none identified"}`
        : /required|insufficient/i.test(String(language.message || ""))
            ? "Insufficient corpus data"
            : "Language model unavailable";

    const graphNodes = Number(pageRank.graph_nodes);
    const graphEdges = Number(pageRank.graph_edges);
    const graphScore = Number(pageRank.score);
    const graphText = pageRank.status === "available"
        && graphNodes > 1
        && graphEdges > 0
        && Number.isFinite(graphScore)
        ? `PageRank ${graphScore.toFixed(6)}, rank #${safeNumber(pageRank.rank, 0)}, ${graphNodes} URLs/nodes and ${graphEdges} relationships/edges`
        : "Insufficient graph data";

    const currentKey = normalizeURLForMatch(currentUrl);
    const matchCount = (Array.isArray(recommendations.recommendations)
        ? recommendations.recommendations
        : []).filter(item => item
            && typeof item.url === "string"
            && normalizeURLForMatch(item.url) !== currentKey
            && typeof item.similarity === "number"
            && Number.isFinite(item.similarity)
            && item.similarity > 0
            && item.similarity <= 1
        ).length;

    return `${languageText}; ${graphText}; ${matchCount} similar historical URL${matchCount === 1 ? "" : "s"}.`;
}


/* =========================================================
   REPORT
   ========================================================= */

function updateReport(result) {

    if (!result || result.valid === false) {
        const failureType = result?.failureType || "invalid";
        const isInvalid = failureType === "invalid";
        const isScanning = failureType === "scanning";

        if (reportUrl) {
            reportUrl.textContent = result?.url || "--";
        }

        if (reportTime) {
            reportTime.textContent = formatDate();
        }

        if (reportVerdict) {
            reportVerdict.textContent = isInvalid ? "Invalid URL" : isScanning ? "Analyzing" : "Unavailable";
        }

        if (reportRiskScore) {
            reportRiskScore.textContent = "--";
        }

        if (reportConfidence) {
            reportConfidence.textContent = "--";
        }

        if (reportStatus) {
            reportStatus.textContent = isInvalid ? "Validation Failed" : isScanning ? "Scanning" : "Backend Error";
        }

        if (reportBadge) {
            reportBadge.textContent = isInvalid ? "INVALID URL" : isScanning ? "SCANNING" : "UNAVAILABLE";
            reportBadge.classList.remove("warning", "danger", "secure");
            reportBadge.classList.add(isInvalid ? "warning" : isScanning ? "warning" : "danger");
        }

        if (reportSummary) {
            reportSummary.textContent = result?.risk_explanation || (isInvalid
                ? "Invalid URL. Enter a valid hostname such as https://google.com"
                : isScanning
                    ? "The current scan is in progress."
                    : "The backend could not complete this scan.");
        }

        if (reportIRSummary) {
            reportIRSummary.textContent = isScanning ? "IR analysis will appear when scanning completes." : "IR analysis unavailable.";
        }

        return;
    }

    if (reportUrl) {
        reportUrl.textContent = result.url || "--";
    }

    if (reportTime) {
        reportTime.textContent = formatDate();
    }

    if (reportVerdict) {
        reportVerdict.textContent = result.prediction;
    }

    if (reportRiskScore) {
        reportRiskScore.textContent =
            Math.round(safeNumber(result.risk_score, 0));
    }

    if (reportConfidence) {
        reportConfidence.textContent =
            `${safeNumber(result.confidence, 0).toFixed(1)}%`;
    }

    if (reportStatus) {
        reportStatus.textContent = result.verifiable === false ? "Unverified" : "Completed";
    }

    if (reportBadge) {
        reportBadge.textContent =
            result.prediction === "Phishing" ? "THREAT DETECTED" : result.verifiable === false ? "UNVERIFIED" : "SAFE";
        reportBadge.classList.remove("warning", "danger", "secure");
        reportBadge.classList.add(
            result.prediction === "Phishing" ? "danger" : result.verifiable === false ? "warning" : "secure"
        );
    }

    if (reportSummary) {
        reportSummary.textContent = getMLVerdictComparison(result)
            || (result.prediction === "Phishing"
                ? "The URL has been classified as potentially dangerous."
                : result.verifiable === false
                    ? "The hostname did not resolve, so the URL cannot be verified as safe."
                    : "The URL has been classified as low risk by the security analysis.");
    }

    if (reportIRSummary) {
        reportIRSummary.textContent = getIRReportSummary(result.ir_analysis, result.url);
    }
}


/* =========================================================
   HISTORY
   ========================================================= */

function getHistory() {

    try {

        const saved =
            localStorage.getItem(HISTORY_KEY);

        const parsed = saved ? JSON.parse(saved) : [];
        return Array.isArray(parsed) ? parsed : [];

    } catch {
        return [];
    }
}


function saveHistory(result) {

    const history =
        getHistory();

    history.unshift({

        url: result.url,

        riskScore:
            Math.round(
                safeNumber(
                    result.risk_score,
                    0
                )
            ),

        prediction:
            result.prediction,

        confidence:
            safeNumber(
                result.confidence,
                0
            ),

        time:
            formatDate()

    });

    localStorage.setItem(
        HISTORY_KEY,
        JSON.stringify(
            history.slice(0, 50)
        )
    );

    renderHistory();

    updateDashboardStats();
}


function renderHistory() {

    const history =
        getHistory();
    const filteredHistory = history.filter(item => {
        if (activeHistoryFilter === "threat") {
            return item.prediction === "Phishing";
        }
        if (activeHistoryFilter === "safe") {
            return item.prediction === "Safe";
        }
        return true;
    });

    const shouldShowEmptyState = history.length === 0;

    if (emptyHistory) {
        emptyHistory.style.display = shouldShowEmptyState ? "block" : "none";
    }

    if (historyTableBody) {

        historyTableBody.innerHTML = "";

        filteredHistory.forEach(item => {

            const row =
                document.createElement("tr");

            row.innerHTML = `
                <td>${escapeHTML(item.time)}</td>
                <td>${escapeHTML(item.url)}</td>
                <td>${escapeHTML(item.riskScore)}</td>
                <td>${escapeHTML(item.prediction)}</td>
                <td>Completed</td>
            `;

            historyTableBody.appendChild(row);
        });

        if (history.length > 0 && filteredHistory.length === 0) {
            const row = document.createElement("tr");
            const cell = document.createElement("td");
            cell.colSpan = 5;
            cell.className = "history-filter-empty";
            cell.textContent = activeHistoryFilter === "threat"
                ? "No threat scans found."
                : activeHistoryFilter === "safe"
                    ? "No safe scans found."
                    : "No scans match this filter.";
            row.appendChild(cell);
            historyTableBody.appendChild(row);
        }
    }

    if (historyList) {

        historyList.innerHTML = "";

        if (history.length === 0 || filteredHistory.length === 0) {

            historyList.innerHTML =
                `<p>${history.length === 0 ? "No Scan History" : "No scans match this filter."}</p>`;

            return;
        }

        filteredHistory.forEach(item => {

            const div =
                document.createElement("div");

            div.className =
                "history-item";

            div.innerHTML = `
                <strong>${escapeHTML(item.url)}</strong>
                <span>Risk: ${escapeHTML(item.riskScore)}</span>
                <span>${escapeHTML(item.prediction)}</span>
            `;

            historyList.appendChild(div);
        });
    }
}


/* =========================================================
   DASHBOARD STATS
   ========================================================= */

function updateDashboardStats() {

    const history =
        getHistory();

    const total =
        history.length;

    const threats =
        history.filter(
            item =>
                item.prediction === "Phishing"
        ).length;

    const safe =
        history.filter(
            item =>
                item.prediction === "Safe"
        ).length;

    if (totalScans) {
        totalScans.textContent =
            total;
    }

    if (threatsDetected) {
        threatsDetected.textContent =
            threats;
    }

    if (safeUrls) {
        safeUrls.textContent =
            safe;
    }
}


/* =========================================================
   MAIN SCAN FUNCTION
   ========================================================= */

async function scanURL() {

    const validation =
        validateURL(
            urlInput?.value
        );

    if (!validation.valid) {

        const invalidResult = {
            valid: false,
            failureType: "invalid",
            url: urlInput?.value?.trim() || "",
            prediction: "Invalid URL",
            risk_explanation: "Invalid URL. Enter a valid hostname such as https://google.com"
        };
        displayResult(invalidResult);

        showScannerMessage(
            invalidResult.risk_explanation,
            "error"
        );

        return;
    }

    const url =
        validation.url;

    hideScannerMessage();

    setLoading(true);
    displayResult({
        valid: false,
        failureType: "scanning",
        url,
        prediction: "Analyzing",
        risk_explanation: "Analysis in progress. Previous scan data has been cleared."
    });

    try {

        const backendData =
            await analyzeWithBackend(url);

        const result =
            convertBackendResult(
                backendData
            );

        displayResult(result);

        if (!result.valid) {
            showScannerMessage(
                result.risk_explanation || "Invalid URL. Enter a valid hostname such as https://google.com",
                "error"
            );
            return;
        }

        saveHistory(result);

        showScannerMessage(
            "URL analysis completed successfully.",
            "success"
        );

    } catch (error) {

        if (error?.status === 400) {
            const invalidResult = {
                valid: false,
                failureType: "invalid",
                url,
                prediction: "Invalid URL",
                risk_explanation: "Invalid URL. Enter a valid hostname such as https://google.com"
            };
            displayResult(invalidResult);
            showScannerMessage(invalidResult.risk_explanation, "error");
            return;
        }

        console.warn("PhishGuard scan could not complete:", error);

        const statusMatch = (error?.message || "").match(/Backend error: (\d+)/);
        const statusCode = statusMatch ? Number(statusMatch[1]) : null;

        const message =
            statusCode === 500
                ? "Security scan failed. Check the backend logs for details."
                : "Unable to connect to the security backend. Make sure the backend is running on port 8000.";

        displayResult({
            valid: false,
            failureType: "error",
            url,
            prediction: "Scan Unavailable",
            risk_explanation: message
        });
        showScannerMessage(message, "error");

    } finally {

        setLoading(false);
    }
}


/* =========================================================
   CLEAR INPUT
   ========================================================= */

function clearURLInput() {

    if (urlInput) {
        urlInput.value = "";
        urlInput.focus();
    }

    hideScannerMessage();
}


/* =========================================================
   CLEAR HISTORY
   ========================================================= */

function clearHistory() {

    localStorage.removeItem(
        HISTORY_KEY
    );

    activeHistoryFilter = "all";
    historyFilterButtons.forEach(button => {
        const selected = button.dataset.filter === "all";
        button.classList.toggle("active", selected);
        button.setAttribute("aria-pressed", String(selected));
    });

    renderHistory();

    updateDashboardStats();
}

function setupHistoryFilters() {
    historyFilterButtons.forEach(button => {
        button.setAttribute("aria-pressed", String(button.dataset.filter === activeHistoryFilter));
        button.addEventListener("click", () => {
            activeHistoryFilter = button.dataset.filter || "all";
            historyFilterButtons.forEach(filterButton => {
                const selected = filterButton === button;
                filterButton.classList.toggle("active", selected);
                filterButton.setAttribute("aria-pressed", String(selected));
            });
            renderHistory();
        });
    });
}


/* =========================================================
   PRINT REPORT
   ========================================================= */

function printReport() {
    window.print();
}


/* =========================================================
   NAVIGATION
   ========================================================= */

function setupNavigation() {

    const links =
        document.querySelectorAll(
            'a[href^="#"]'
        );

    links.forEach(link => {

        link.addEventListener(
            "click",
            () => {

                const targetSelector =
                    link.getAttribute("href");

                const target = targetSelector && targetSelector.length > 1
                    ? document.querySelector(targetSelector)
                    : null;

                if (target) {
                    setTimeout(() => {
                        target.scrollIntoView({ behavior: "smooth", block: "start" });
                    }, 50);
                }
            }
        );
    });
}


/* =========================================================
   EVENT LISTENERS
   ========================================================= */

if (analyzeBtn) {

    analyzeBtn.addEventListener(
        "click",
        scanURL
    );
}

if (scanAgainBtn) {

    scanAgainBtn.addEventListener(
        "click",
        scanURL
    );
}

if (clearInput) {

    clearInput.addEventListener(
        "click",
        clearURLInput
    );
}

if (clearHistoryBtn) {

    clearHistoryBtn.addEventListener(
        "click",
        clearHistory
    );
}

if (printReportBtn) {

    printReportBtn.addEventListener(
        "click",
        printReport
    );
}

if (urlInput) {

    urlInput.addEventListener(
        "keydown",
        event => {

            if (event.key === "Enter") {
                scanURL();
            }
        }
    );
}


/* =========================================================
   STARTUP
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        renderHistory();

        updateDashboardStats();

        setupNavigation();

        setupHistoryFilters();

        console.log(
            "PhishGuard frontend loaded successfully."
        );
    }
);