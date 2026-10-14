document.addEventListener("DOMContentLoaded", () => {
    let performanceChart = null;
    let departmentRiskChart = null;
    let riskChart = null;

    const status = document.getElementById("dashboardStatus");

    const setText = (id, value) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    };

    const number = (value) =>
        new Intl.NumberFormat("en-IN").format(Number(value || 0));

    const percent = (value) =>
        `${(Number(value || 0) * 100).toFixed(1)}%`;

    const directPercent = (value) =>
        `${Number(value || 0).toFixed(1)}%`;

    function setStatus(message, isError = false) {
        if (!status) return;

        status.textContent = message;
        status.classList.toggle("error", isError);
    }

    function formatTimestamp(value) {
        if (!value) return "now";

        const date = new Date(value);

        if (Number.isNaN(date.getTime())) {
            return "now";
        }

        return date.toLocaleTimeString("en-IN", {
            hour: "2-digit",
            minute: "2-digit"
        });
    }

    // =========================================================
    // RISK LEGEND
    // =========================================================

    function updateRiskLegend(risk) {
        const host = document.getElementById("riskLegend");

        if (!host) return;

        const rows = [
            {
                name: "High Risk",
                value: Number(risk.high || 0),
                description: "Probability ≥ 64%",
                dot: "risk-dot-high"
            },
            {
                name: "Medium Risk",
                value: Number(risk.medium || 0),
                description: "Probability 40%–63.9%",
                dot: "risk-dot-medium"
            },
            {
                name: "Low Risk",
                value: Number(risk.low || 0),
                description: "Probability < 40%",
                dot: "risk-dot-low"
            }
        ];

        host.innerHTML = rows.map((row) => `
            <div class="legend-row">
                <span class="legend-dot ${row.dot}"></span>

                <span class="legend-main">
                    <strong>${row.name}</strong>
                    <small>${row.description}</small>
                </span>

                <span class="legend-percent">
                    ${directPercent(row.value)}
                </span>
            </div>
        `).join("");
    }

    // =========================================================
    // RISK DOUGHNUT CHART
    // =========================================================

    function renderRiskChart(risk) {
        const canvas = document.getElementById("riskChart");

        if (!canvas || typeof Chart === "undefined") {
            return;
        }

        if (riskChart) {
            riskChart.destroy();
        }

        const values = [
            Number(risk.high || 0),
            Number(risk.medium || 0),
            Number(risk.low || 0)
        ];

        riskChart = new Chart(canvas, {
            type: "doughnut",

            data: {
                labels: [
                    "High",
                    "Medium",
                    "Low"
                ],

                datasets: [{
                    data: values,
                    borderWidth: 0,
                    spacing: 3,
                    hoverOffset: 4,

                    backgroundColor: [
                        "#fb7185",
                        "#f59e0b",
                        "#22c55e"
                    ]
                }]
            },

            options: {
                responsive: true,
                maintainAspectRatio: false,

                cutout: "76%",

                plugins: {
                    legend: {
                        display: false
                    },

                    tooltip: {
                        callbacks: {
                            label: (context) =>
                                `${context.label}: ${Number(
                                    context.raw || 0
                                ).toFixed(1)}%`
                        }
                    }
                }
            }
        });

        const total = values.reduce(
            (sum, value) => sum + value,
            0
        );

        setText(
            "riskCoverage",
            total ? `${total.toFixed(0)}%` : "—"
        );

        updateRiskLegend(risk);
    }

    // =========================================================
    // PERFORMANCE CHART
    // =========================================================

    function renderPerformanceChart(performance) {
        const canvas =
            document.getElementById("performanceChart");

        if (!canvas || typeof Chart === "undefined") {
            return;
        }

        if (performanceChart) {
            performanceChart.destroy();
        }

        const values = [
            Number(performance["2"] || 0),
            Number(performance["3"] || 0),
            Number(performance["4"] || 0),
            Number(performance["5"] || 0)
        ];

        performanceChart = new Chart(
            canvas,
            {
                type: "bar",

                data: {
                    labels: [
                        "Rating 2",
                        "Rating 3",
                        "Rating 4",
                        "Rating 5"
                    ],

                    datasets: [{
                        label: "Employees",

                        data: values,

                        borderRadius: 8,

                        borderSkipped: false,

                        backgroundColor: [
                            "#fb7185",
                            "#818cf8",
                            "#22d3ee",
                            "#34d399"
                        ],

                        maxBarThickness: 48
                    }]
                },

                options: {
                    responsive: true,

                    maintainAspectRatio: false,

                    plugins: {
                        legend: {
                            display: false
                        },

                        tooltip: {
                            callbacks: {
                                label: (context) =>
                                    ` ${number(
                                        context.raw
                                    )} employees`
                            }
                        }
                    },

                    scales: {
                        x: {
                            border: {
                                display: false
                            },

                            grid: {
                                display: false
                            },

                            ticks: {
                                color: "#77849b",

                                font: {
                                    size: 9
                                }
                            }
                        },

                        y: {
                            beginAtZero: true,

                            border: {
                                display: false
                            },

                            grid: {
                                color:
                                    "rgba(148,163,184,.07)"
                            },

                            ticks: {
                                color: "#77849b",

                                font: {
                                    size: 9
                                },

                                precision: 0
                            }
                        }
                    }
                }
            }
        );
    }

    // =========================================================
    // DEPARTMENT RISK CHART
    // =========================================================

    function renderDepartmentChart(departments) {
        const canvas =
            document.getElementById(
                "departmentRiskChart"
            );

        if (!canvas || typeof Chart === "undefined") {
            return;
        }

        if (departmentRiskChart) {
            departmentRiskChart.destroy();
        }

        const sorted = [...departments].sort(
            (a, b) =>
                Number(b.average_risk || 0) -
                Number(a.average_risk || 0)
        );

        departmentRiskChart = new Chart(
            canvas,
            {
                type: "bar",

                data: {
                    labels: sorted.map(
                        item => item.department
                    ),

                    datasets: [{
                        label:
                            "Average predicted risk",

                        data: sorted.map(
                            item =>
                                Number(
                                    item.average_risk || 0
                                ) * 100
                        ),

                        borderRadius: 7,

                        borderSkipped: false,

                        backgroundColor: "#7c6cff",

                        maxBarThickness: 26
                    }]
                },

                options: {
                    indexAxis: "y",

                    responsive: true,

                    maintainAspectRatio: false,

                    plugins: {
                        legend: {
                            display: false
                        },

                        tooltip: {
                            callbacks: {
                                label: (context) =>
                                    ` ${Number(
                                        context.raw || 0
                                    ).toFixed(1)}% average predicted risk`
                            }
                        }
                    },

                    scales: {
                        x: {
                            beginAtZero: true,

                            max: 100,

                            border: {
                                display: false
                            },

                            grid: {
                                color:
                                    "rgba(148,163,184,.07)"
                            },

                            ticks: {
                                color: "#77849b",

                                font: {
                                    size: 9
                                },

                                callback: value =>
                                    `${value}%`
                            }
                        },

                        y: {
                            border: {
                                display: false
                            },

                            grid: {
                                display: false
                            },

                            ticks: {
                                color: "#77849b",

                                font: {
                                    size: 9
                                }
                            }
                        }
                    }
                }
            }
        );
    }

    // =========================================================
    // WORKFORCE SIGNALS
    // =========================================================

    function renderSignals(data) {
        const host =
            document.getElementById(
                "workforceSignals"
            );

        if (!host) return;

        const kpis =
            data.kpis || {};

        const risk =
            data.risk_distribution || {};

        const departments =
            data.department_risk || [];

        const performance =
            data.performance_distribution || {};

        const mediumHighCount =
            Number(
                kpis.high_risk_count || 0
            ) +
            Math.round(
                (
                    Number(risk.medium || 0) / 100
                ) *
                Number(
                    kpis.total_employees || 0
                )
            );

        const highPerformanceCount =
            Number(
                performance["4"] || 0
            ) +
            Number(
                performance["5"] || 0
            );

        const highestRiskDepartment =
            departments.length
                ? departments[0].department
                : "—";

        const items = [
            {
                label:
                    "Historical attrition rate",

                value:
                    percent(
                        kpis.historical_attrition_rate
                    ),

                cls: ""
            },

            {
                label:
                    "Medium + high predicted risk",

                value:
                    number(
                        mediumHighCount
                    ) +
                    " employees",

                cls: "accent"
            },

            {
                label:
                    "Highest average-risk department",

                value:
                    highestRiskDepartment,

                cls: "accent"
            },

            {
                label:
                    "Ratings 4–5",

                value:
                    number(
                        highPerformanceCount
                    ) +
                    " employees",

                cls: ""
            }
        ];

        host.innerHTML =
            items.map(item => `
                <div class="signal-item">
                    <span>${item.label}</span>

                    <strong class="${item.cls}">
                        ${item.value}
                    </strong>
                </div>
            `).join("");
    }

    // =========================================================
    // LOAD DASHBOARD
    // =========================================================

    async function loadDashboard() {
        try {
            setStatus(
                "Loading workforce intelligence..."
            );

            const response =
                await fetch(
                    "/api/dashboard",
                    {
                        headers: {
                            "Accept":
                                "application/json"
                        }
                    }
                );

            const data =
                await response.json();

            if (
                !response.ok ||
                !data.success
            ) {
                throw new Error(
                    data.error ||
                    "Unable to load dashboard data."
                );
            }

            const kpis =
                data.kpis || {};

            const risk =
                data.risk_distribution || {};

            const performance =
                data.performance_distribution || {};

            const departments =
                data.department_risk || [];

            // -------------------------------------------------
            // KPI VALUES
            // -------------------------------------------------

            setText(
                "totalEmployees",
                number(
                    kpis.total_employees
                )
            );

            setText(
                "avgPredictedRisk",
                percent(
                    kpis.average_predicted_risk
                )
            );

            setText(
                "historicalAttrition",
                `Historical attrition: ${percent(
                    kpis.historical_attrition_rate
                )}`
            );

            setText(
                "avgPerformance",
                Number(
                    kpis.average_performance || 0
                ).toFixed(1)
            );

            setText(
                "highRiskCount",
                number(
                    kpis.high_risk_count
                )
            );

            setText(
                "highRiskPercentage",
                `${percent(
                    kpis.high_risk_percentage
                )} of workforce`
            );

            // -------------------------------------------------
            // CHARTS
            // -------------------------------------------------

            renderRiskChart(
                risk
            );

            renderPerformanceChart(
                performance
            );

            renderDepartmentChart(
                departments
            );

            // -------------------------------------------------
            // SIGNALS
            // -------------------------------------------------

            renderSignals(
                data
            );

            // -------------------------------------------------
            // STATUS
            // -------------------------------------------------

            setStatus(
                `Updated ${formatTimestamp(
                    data.generated_at
                )}`
            );

        } catch (error) {

            console.error(
                "Dashboard error:",
                error
            );

            setStatus(
                `Dashboard unavailable: ${error.message}`,
                true
            );

            const errorBox =
                document.getElementById(
                    "dashboardError"
                );

            if (errorBox) {
                errorBox.classList.remove(
                    "hidden"
                );

                errorBox.textContent =
                    error.message;
            }

            setText(
                "totalEmployees",
                "—"
            );

            setText(
                "avgPredictedRisk",
                "—"
            );

            setText(
                "avgPerformance",
                "—"
            );

            setText(
                "highRiskCount",
                "—"
            );
        }
    }

    // =========================================================
    // START
    // =========================================================

    loadDashboard();
});