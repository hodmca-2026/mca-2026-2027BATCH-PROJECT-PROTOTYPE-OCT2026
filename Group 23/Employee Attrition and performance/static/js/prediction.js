document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("predictionForm");
    const button = document.getElementById("predictButton");

    if (!form || !button) {
        return;
    }


    /* =========================================================
       FORM SUBMISSION
    ========================================================= */

    form.addEventListener("submit", async (event) => {

        event.preventDefault();

        button.disabled = true;
        button.classList.add("is-loading");

        button.innerHTML = `
            <span class="button-spinner"></span>
            Running prediction...
        `;


        try {

            const formData = new FormData(form);
            const data = {};


            /* Convert form values to backend-friendly types */

            formData.forEach((value, key) => {

                if (key === "uses_ai_tools_at_work") {

                    data[key] = value === "True";

                } else if (
                    [
                        "age",
                        "monthly_income",
                        "stock_option_level",
                        "salary_hike_pct",
                        "years_at_company",
                        "total_working_years",
                        "years_since_promotion",
                        "num_prior_companies",
                        "commute_minutes",
                        "overtime_hours_per_week",
                        "business_travel_days_per_year",
                        "training_hours",
                        "manager_support_score",
                        "burnout_score",
                        "engagement_score",
                        "work_life_balance_score",
                        "performance_rating",
                        "last_review_score",
                        "perceived_ai_job_risk"
                    ].includes(key)
                ) {

                    data[key] = Number(value);

                } else {

                    data[key] = value;

                }

            });


            /* API request */

            const response = await fetch("/api/predict", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },

                body: JSON.stringify(data)

            });


            const result = await response.json();


            if (!response.ok) {

                throw new Error(
                    result.error || "Prediction failed"
                );

            }


            displayPrediction(result);


        } catch (error) {

            console.error("Prediction error:", error);

            showError(error.message);

        } finally {

            button.disabled = false;

            button.classList.remove("is-loading");

            button.innerHTML = `
                <i data-lucide="brain-circuit"></i>
                Run AI Prediction
            `;

            refreshIcons();

        }

    });


    /* Reset results when form is reset */

    form.addEventListener("reset", () => {

        setTimeout(() => {
            resetPredictionResults();
        }, 0);

    });


    refreshIcons();

});


/* =========================================================
   DISPLAY PREDICTION
========================================================= */

function displayPrediction(result) {

    const attrition = result.attrition || {};
    const performance = result.performance || {};


    /* =========================================================
       ATTRITION
    ========================================================= */

    const probability = Number(
        attrition.probability ??
        attrition.attrition_probability ??
        0
    );


    const riskLevel = (
        attrition.risk_level ??
        attrition.risk ??
        "UNKNOWN"
    ).toUpperCase();


    setText(
        "attritionProbability",
        `${(probability * 100).toFixed(1)}%`
    );


    setText(
        "riskPercentage",
        `${(probability * 100).toFixed(1)}%`
    );


    const riskBar = document.getElementById("riskBar");

    if (riskBar) {

        riskBar.style.width =
            `${Math.min(probability * 100, 100)}%`;

        riskBar.classList.remove(
            "risk-low",
            "risk-medium",
            "risk-high"
        );

        riskBar.classList.add(
            `risk-${riskLevel.toLowerCase()}`
        );
    }


    const riskBadge =
        document.getElementById("riskBadge");

    if (riskBadge) {

        riskBadge.textContent = riskLevel;

        riskBadge.className =
            `badge ${getRiskBadgeClass(riskLevel)} result-risk-badge`;

    }


    if (
        attrition.threshold !== undefined &&
        attrition.threshold !== null
    ) {

        setText(
            "thresholdValue",
            Number(attrition.threshold).toFixed(2)
        );

    }


    /* =========================================================
       PERFORMANCE
    ========================================================= */

    const rating =
        performance.predicted_rating ??
        performance.rating ??
        "--";


    const label =
        performance.label ??
        performance.performance_label ??
        "Predicted Performance";


    const confidence = Number(
        performance.confidence ?? 0
    );


    setText(
        "performanceRating",
        rating
    );


    setText(
        "performanceLabel",
        label
    );


    setText(
        "performanceConfidence",
        `${(confidence * 100).toFixed(1)}%`
    );


    const performanceBar =
        document.getElementById("performanceBar");

    if (performanceBar) {

        performanceBar.style.width =
            `${Math.min(confidence * 100, 100)}%`;

    }


    displayPerformanceProbabilities(
        performance.probabilities
    );


    /* =========================================================
       RECOMMENDATIONS
    ========================================================= */

    displayRecommendations(
        result.recommendations
    );

}


/* =========================================================
   PERFORMANCE PROBABILITIES
========================================================= */

function displayPerformanceProbabilities(probabilities) {

    const container =
        document.getElementById(
            "performanceProbabilities"
        );


    if (!container) {
        return;
    }


    container.innerHTML = "";


    if (!probabilities) {
        return;
    }


    Object.entries(probabilities).forEach(
        ([rating, probability]) => {

            const numericValue =
                Number(probability);


            const percentage =
                numericValue <= 1
                    ? numericValue * 100
                    : numericValue;


            const row =
                document.createElement("div");

            row.className =
                "performance-probability-row";


            row.innerHTML = `

                <div class="probability-header">

                    <span>
                        Rating ${escapeHtml(String(rating))}
                    </span>

                    <strong>
                        ${percentage.toFixed(1)}%
                    </strong>

                </div>


                <div class="progress-track">

                    <div
                        class="progress-fill probability-fill"
                        style="width:${Math.min(
                            percentage,
                            100
                        )}%"
                    ></div>

                </div>

            `;


            container.appendChild(row);

        }
    );

}


/* =========================================================
   RECOMMENDATIONS
========================================================= */

function displayRecommendations(recommendations) {

    const container =
        document.getElementById(
            "recommendations"
        );


    if (!container) {
        return;
    }


    /*
     * Handle:
     * 1. null / undefined
     * 2. empty array []
     * 3. normal recommendation array
     * 4. single recommendation string
     */

    if (
        recommendations === null ||
        recommendations === undefined ||
        (
            Array.isArray(recommendations) &&
            recommendations.length === 0
        )
    ) {

        container.innerHTML = `

            <div class="empty-state">

                <i data-lucide="info"></i>

                <h3>
                    No specific actions identified
                </h3>

                <p>
                    The prediction completed successfully.
                    No additional HR action was triggered
                    by the current employee inputs.
                </p>

            </div>

        `;

        refreshIcons();

        return;
    }


    let items = [];


    /*
     * Convert the backend response into an array.
     */

    if (Array.isArray(recommendations)) {

        items = recommendations.filter(
            recommendation =>
                recommendation !== null &&
                recommendation !== undefined &&
                String(
                    recommendation
                ).trim() !== ""
        );

    } else {

        items = [
            recommendations
        ];

    }


    /*
     * Safety check:
     * Do not leave the card blank if all
     * returned values are empty.
     */

    if (items.length === 0) {

        container.innerHTML = `

            <div class="empty-state">

                <i data-lucide="info"></i>

                <h3>
                    No specific actions identified
                </h3>

                <p>
                    The prediction completed successfully.
                    No additional HR action was triggered
                    by the current employee inputs.
                </p>

            </div>

        `;

        refreshIcons();

        return;
    }


    /*
     * Clear previous recommendations.
     */

    container.innerHTML = "";


    /*
     * Render each recommendation.
     */

    items.forEach(
        (recommendation, index) => {

            const item =
                document.createElement("div");

            item.className =
                "recommendation-item-modern";


            item.innerHTML = `

                <div class="recommendation-number">
                    ${index + 1}
                </div>

                <div class="recommendation-text">
                    ${escapeHtml(
                        String(
                            recommendation
                        )
                    )}
                </div>

            `;


            container.appendChild(
                item
            );

        }
    );


    /*
     * Refresh Lucide icons.
     */

    refreshIcons();

}


/* =========================================================
   RISK BADGES
========================================================= */

function getRiskBadgeClass(risk) {

    switch (risk) {

        case "HIGH":
            return "badge-high";

        case "MEDIUM":
            return "badge-medium";

        case "LOW":
            return "badge-low";

        default:
            return "badge-medium";

    }

}


/* =========================================================
   ERROR HANDLING
========================================================= */

function showError(message) {

    const container =
        document.getElementById(
            "recommendations"
        );


    if (!container) {
        return;
    }


    container.innerHTML = `

        <div class="prediction-error">

            <div class="prediction-error-icon">
                <i data-lucide="alert-circle"></i>
            </div>

            <div>

                <strong>
                    Prediction Error
                </strong>

                <p>
                    ${escapeHtml(message)}
                </p>

            </div>

        </div>

    `;


    refreshIcons();

}


/* =========================================================
   RESET
========================================================= */

function resetPredictionResults() {

    setText(
        "attritionProbability",
        "--"
    );

    setText(
        "riskPercentage",
        "--"
    );

    setText(
        "thresholdValue",
        "--"
    );

    setText(
        "performanceRating",
        "--"
    );

    setText(
        "performanceLabel",
        "Waiting for prediction"
    );

    setText(
        "performanceConfidence",
        "--"
    );


    const riskBadge =
        document.getElementById("riskBadge");

    if (riskBadge) {

        riskBadge.textContent = "Waiting";

        riskBadge.className =
            "badge badge-medium result-risk-badge";

    }


    const riskBar =
        document.getElementById("riskBar");

    if (riskBar) {

        riskBar.style.width = "0%";

        riskBar.classList.remove(
            "risk-low",
            "risk-medium",
            "risk-high"
        );

    }


    const performanceBar =
        document.getElementById("performanceBar");

    if (performanceBar) {
        performanceBar.style.width = "0%";
    }


    const probabilities =
        document.getElementById(
            "performanceProbabilities"
        );

    if (probabilities) {
        probabilities.innerHTML = "";
    }


    const recommendations =
        document.getElementById(
            "recommendations"
        );

    if (recommendations) {

        recommendations.innerHTML = `

            <div class="empty-state">

                <i data-lucide="sparkles"></i>

                <h3>
                    No prediction yet
                </h3>

                <p>
                    Run the prediction model to generate
                    HR recommendations.
                </p>

            </div>

        `;

    }


    refreshIcons();

}


/* =========================================================
   HELPERS
========================================================= */

function setText(id, value) {

    const element =
        document.getElementById(id);

    if (element) {
        element.textContent = value;
    }

}


function refreshIcons() {

    if (window.lucide) {
        lucide.createIcons();
    }

}


function escapeHtml(value) {

    return value
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

}