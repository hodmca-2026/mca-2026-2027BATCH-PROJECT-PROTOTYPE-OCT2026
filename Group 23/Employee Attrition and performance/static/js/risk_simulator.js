document.addEventListener("DOMContentLoaded", () => {

    /* ======================================================
       ELEMENTS
    ====================================================== */

    const employeeSelect =
        document.getElementById("employeeSelect");

    const loadEmployeeBtn =
        document.getElementById("loadEmployeeBtn");

    const employeeProfileSection =
        document.getElementById("employeeProfileSection");

    const simulationSection =
        document.getElementById("simulationSection");

    const resultsSection =
        document.getElementById("resultsSection");

    const employeeProfile =
        document.getElementById("employeeProfile");

    const selectedEmployeeText =
        document.getElementById("selectedEmployeeText");

    const runSimulationBtn =
        document.getElementById("runSimulationBtn");

    const resetSimulationBtn =
        document.getElementById("resetSimulationBtn");

    const clearHistoryBtn =
        document.getElementById("clearHistoryBtn");

    const simulationError =
        document.getElementById("simulationError");


    /* ======================================================
       STATE
    ====================================================== */

    let selectedEmployee = null;

    let riskComparisonChart = null;

    let performanceComparisonChart = null;

    const HISTORY_KEY =
        "hr_insight_ai_simulation_history_v1";


    /* ======================================================
       ICONS
    ====================================================== */

    function refreshIcons() {

        if (window.lucide) {
            lucide.createIcons();
        }

    }


    /* ======================================================
       LOAD EMPLOYEES
    ====================================================== */

    async function loadEmployees() {

        try {

            employeeSelect.innerHTML = `
                <option value="">
                    Loading employees...
                </option>
            `;


            const response =
                await fetch(
                    "/api/employees?page=1&page_size=5000",
                    {
                        headers: {
                            "Accept":
                                "application/json"
                        }
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.error ||
                    "Unable to load employees."
                );

            }


            const employees =
                data.employees || [];


            employeeSelect.innerHTML = `
                <option value="">
                    Select employee
                </option>
            `;


            employees.forEach(
                employee => {

                    const option =
                        document.createElement(
                            "option"
                        );


                    option.value =
                        employee.employee_id;


                    option.textContent =
                        `${employee.employee_id} — ` +
                        `${employee.department} — ` +
                        `${employee.job_role}`;


                    employeeSelect.appendChild(
                        option
                    );

                }
            );


            refreshIcons();


        } catch (error) {

            showError(
                error.message
            );

        }

    }


    /* ======================================================
       EMPLOYEE SELECTION
    ====================================================== */

    employeeSelect.addEventListener(
        "change",
        () => {

            loadEmployeeBtn.disabled =
                !employeeSelect.value;

        }
    );


    /* ======================================================
       LOAD EMPLOYEE
    ====================================================== */

    loadEmployeeBtn.addEventListener(
        "click",
        async () => {

            const employeeId =
                employeeSelect.value;


            if (!employeeId) {
                return;
            }


            clearError();

            loadEmployeeBtn.disabled =
                true;

            loadEmployeeBtn.classList.add(
                "is-loading"
            );

            loadEmployeeBtn.innerHTML = `
                <span class="button-spinner"></span>
                Loading...
            `;


            try {

                const response =
                    await fetch(
                        `/api/employees/${encodeURIComponent(
                            employeeId
                        )}`,
                        {
                            headers: {
                                "Accept":
                                    "application/json"
                            }
                        }
                    );


                const data =
                    await response.json();


                if (!response.ok) {

                    throw new Error(
                        data.error ||
                        "Unable to load employee profile."
                    );

                }


                selectedEmployee =
                    data.employee || data;


                renderEmployeeProfile(
                    selectedEmployee
                );


                initializeSliders(
                    selectedEmployee
                );


                employeeProfileSection
                    .classList.remove(
                        "hidden"
                    );


                simulationSection
                    .classList.remove(
                        "hidden"
                    );


                resultsSection
                    .classList.add(
                        "hidden"
                    );


                selectedEmployeeText.textContent =
                    `Employee ID: ${
                        selectedEmployee.employee_id
                    }`;


                renderHistory();


                employeeProfileSection.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });


            } catch (error) {

                showError(
                    error.message
                );

            } finally {

                loadEmployeeBtn.disabled =
                    false;

                loadEmployeeBtn.classList.remove(
                    "is-loading"
                );

                loadEmployeeBtn.innerHTML = `
                    <i data-lucide="user-check"></i>
                    Load Profile
                `;

                refreshIcons();

            }

        }
    );


    /* ======================================================
       EMPLOYEE PROFILE
    ====================================================== */

    function renderEmployeeProfile(
        employee
    ) {

        const fields = [

            [
                "Department",
                employee.department
            ],

            [
                "Job Role",
                employee.job_role
            ],

            [
                "Job Level",
                employee.job_level
            ],

            [
                "Age",
                employee.age
            ],

            [
                "Years at Company",
                employee.years_at_company
            ],

            [
                "Performance Rating",
                employee.performance_rating
            ],

            [
                "Monthly Income",
                formatCurrency(
                    employee.monthly_income
                )
            ],

            [
                "Work Mode",
                employee.work_mode
            ]

        ];


        employeeProfile.innerHTML =
            fields.map(
                ([label, value]) => `

                    <div class="simulator-profile-item">

                        <span>
                            ${escapeHtml(label)}
                        </span>

                        <strong>
                            ${escapeHtml(
                                String(
                                    value ?? "--"
                                )
                            )}
                        </strong>

                    </div>

                `
            ).join("");

    }


    /* ======================================================
       SLIDER CONFIGURATION
    ====================================================== */

    const sliderConfig = [

        {
            id: "burnout",
            output: "burnoutValue",
            key: "burnout_score"
        },

        {
            id: "engagement",
            output: "engagementValue",
            key: "engagement_score"
        },

        {
            id: "managerSupport",
            output: "managerSupportValue",
            key: "manager_support_score"
        },

        {
            id: "workLifeBalance",
            output: "workLifeBalanceValue",
            key: "work_life_balance_score"
        },

        {
            id: "overtime",
            output: "overtimeValue",
            key: "overtime_hours_per_week"
        },

        {
            id: "training",
            output: "trainingValue",
            key: "training_hours"
        },

        {
            id: "salaryHike",
            output: "salaryHikeValue",
            key: "salary_hike_pct"
        },

        {
            id: "promotionGap",
            output: "promotionGapValue",
            key: "years_since_promotion"
        }

    ];


    /* ======================================================
       INITIALIZE SLIDERS
    ====================================================== */

    function initializeSliders(
        employee
    ) {

        sliderConfig.forEach(
            config => {

                const slider =
                    document.getElementById(
                        config.id
                    );

                const output =
                    document.getElementById(
                        config.output
                    );


                if (!slider || !output) {
                    return;
                }


                let value =
                    Number(
                        employee[
                            config.key
                        ]
                    );


                if (!Number.isFinite(value)) {

                    value =
                        Number(
                            slider.min
                        );

                }


                value =
                    Math.max(
                        Number(slider.min),
                        Math.min(
                            Number(slider.max),
                            value
                        )
                    );


                slider.value =
                    value;


                updateSliderOutput(
                    config.id,
                    config.output,
                    value
                );


                slider.oninput =
                    () => {

                        updateSliderOutput(
                            config.id,
                            config.output,
                            slider.value
                        );

                    };

            }
        );

    }


    /* ======================================================
       SLIDER DISPLAY
    ====================================================== */

    function updateSliderOutput(
        sliderId,
        outputId,
        value
    ) {

        const output =
            document.getElementById(
                outputId
            );


        const numericValue =
            Number(value);


        if (!output) {
            return;
        }


        if (
            sliderId === "salaryHike"
        ) {

            output.textContent =
                `${numericValue.toFixed(1)}%`;

        }

        else if (
            sliderId === "overtime"
        ) {

            output.textContent =
                `${numericValue.toFixed(1)} h`;

        }

        else if (
            sliderId === "training"
        ) {

            output.textContent =
                `${numericValue.toFixed(0)} h`;

        }

        else if (
            sliderId === "promotionGap"
        ) {

            output.textContent =
                `${numericValue.toFixed(1)} y`;

        }

        else {

            output.textContent =
                numericValue.toFixed(1);

        }

    }


    /* ======================================================
       RUN SIMULATION
    ====================================================== */

    runSimulationBtn.addEventListener(
        "click",
        async () => {

            if (!selectedEmployee) {

                showError(
                    "Please select an employee first."
                );

                return;

            }


            clearError();


            runSimulationBtn.disabled =
                true;

            runSimulationBtn.classList.add(
                "is-loading"
            );

            runSimulationBtn.innerHTML = `
                <span class="button-spinner"></span>
                Running Simulation...
            `;


            try {

                const scenario = {

                    employee_id:
                        selectedEmployee.employee_id,

                    burnout_score:
                        getValue("burnout"),

                    engagement_score:
                        getValue("engagement"),

                    manager_support_score:
                        getValue("managerSupport"),

                    work_life_balance_score:
                        getValue("workLifeBalance"),

                    overtime_hours_per_week:
                        getValue("overtime"),

                    training_hours:
                        getValue("training"),

                    salary_hike_pct:
                        getValue("salaryHike"),

                    years_since_promotion:
                        getValue("promotionGap")

                };


                const response =
                    await fetch(
                        "/api/simulate",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json",

                                "Accept":
                                    "application/json"
                            },

                            body:
                                JSON.stringify(
                                    scenario
                                )
                        }
                    );


                const data =
                    await response.json();


                if (!response.ok) {

                    throw new Error(
                        data.error ||
                        "Simulation failed."
                    );

                }


                renderResults(
                    data
                );


                saveHistory(
                    data,
                    scenario
                );


                resultsSection
                    .classList.remove(
                        "hidden"
                    );


                renderHistory();


                resultsSection.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });


            } catch (error) {

                console.error(
                    "Simulation error:",
                    error
                );


                showError(
                    error.message
                );


            } finally {

                runSimulationBtn.disabled =
                    false;

                runSimulationBtn.classList.remove(
                    "is-loading"
                );

                runSimulationBtn.innerHTML = `
                    <i data-lucide="play"></i>
                    Run Simulation
                `;

                refreshIcons();

            }

        }
    );


    /* ======================================================
       RESET
    ====================================================== */

    resetSimulationBtn.addEventListener(
        "click",
        () => {

            if (!selectedEmployee) {
                return;
            }


            initializeSliders(
                selectedEmployee
            );


            resultsSection
                .classList.add(
                    "hidden"
                );


            clearError();

        }
    );


    /* ======================================================
       CLEAR HISTORY
    ====================================================== */

    clearHistoryBtn.addEventListener(
        "click",
        () => {

            if (!selectedEmployee) {
                return;
            }


            const employeeId =
                String(
                    selectedEmployee.employee_id
                );


            const existing =
                getHistory();


            const filtered =
                existing.filter(
                    item =>
                        String(
                            item.employee_id
                        ) !== employeeId
                );


            localStorage.setItem(
                HISTORY_KEY,
                JSON.stringify(
                    filtered
                )
            );


            renderHistory();

        }
    );


    /* ======================================================
       RESULTS
    ====================================================== */

    function renderResults(
        data
    ) {

        const current =
            data.current || {};

        const simulated =
            data.simulated || {};


        const currentRisk =
            Number(
                current.attrition_probability
                || 0
            );


        const simulatedRisk =
            Number(
                simulated.attrition_probability
                || 0
            );


        const currentPerformance =
            Number(
                current.performance_rating
                || 0
            );


        const simulatedPerformance =
            Number(
                simulated.performance_rating
                || 0
            );


        setText(
            "currentRisk",
            formatPercent(
                currentRisk
            )
        );


        setText(
            "simulatedRisk",
            formatPercent(
                simulatedRisk
            )
        );


        setRiskBadge(
            "currentRiskBadge",
            current.risk_level
        );


        setRiskBadge(
            "simulatedRiskBadge",
            simulated.risk_level
        );


        setText(
            "currentPerformance",
            `Rating ${currentPerformance}`
        );


        setText(
            "simulatedPerformance",
            `Rating ${simulatedPerformance}`
        );


        /* Risk delta */

        const riskChange =
            (
                simulatedRisk -
                currentRisk
            ) * 100;


        const performanceChange =
            simulatedPerformance -
            currentPerformance;


        const riskChangeElement =
            document.getElementById(
                "riskChange"
            );


        if (riskChange < 0) {

            riskChangeElement.textContent =
                `${Math.abs(
                    riskChange
                ).toFixed(1)} pp reduction`;

            riskChangeElement.className =
                "positive-change";

        }

        else if (riskChange > 0) {

            riskChangeElement.textContent =
                `+${riskChange.toFixed(
                    1
                )} pp increase`;

            riskChangeElement.className =
                "negative-change";

        }

        else {

            riskChangeElement.textContent =
                "No change";

            riskChangeElement.className =
                "";

        }


        /* Performance delta */

        const performanceChangeElement =
            document.getElementById(
                "performanceChange"
            );


        if (performanceChange > 0) {

            performanceChangeElement.textContent =
                `+${performanceChange} rating`;

            performanceChangeElement.className =
                "positive-change";

        }

        else if (performanceChange < 0) {

            performanceChangeElement.textContent =
                `${performanceChange} rating`;

            performanceChangeElement.className =
                "negative-change";

        }

        else {

            performanceChangeElement.textContent =
                "No change";

            performanceChangeElement.className =
                "";

        }


        renderRecommendation(
            data.recommendation
        );


        renderComparisonCharts(
            currentRisk,
            simulatedRisk,
            currentPerformance,
            simulatedPerformance
        );

    }


    /* ======================================================
       CHARTS
    ====================================================== */

    function renderComparisonCharts(
        currentRisk,
        simulatedRisk,
        currentPerformance,
        simulatedPerformance
    ) {

        const riskCanvas =
            document.getElementById(
                "riskComparisonChart"
            );

        const performanceCanvas =
            document.getElementById(
                "performanceComparisonChart"
            );


        if (
            !riskCanvas ||
            !performanceCanvas ||
            typeof Chart === "undefined"
        ) {
            return;
        }


        if (riskComparisonChart) {
            riskComparisonChart.destroy();
        }


        if (performanceComparisonChart) {
            performanceComparisonChart.destroy();
        }


        riskComparisonChart =
            new Chart(
                riskCanvas,
                {
                    type: "bar",

                    data: {

                        labels: [
                            "Current",
                            "Simulated"
                        ],

                        datasets: [{

                            label:
                                "Attrition Risk (%)",

                            data: [
                                currentRisk * 100,
                                simulatedRisk * 100
                            ],

                            borderRadius: 9,

                            borderSkipped: false,

                            backgroundColor: [
                                "#6366f1",
                                "#22c55e"
                            ],

                            maxBarThickness: 50

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

                                    label:
                                        context =>
                                            ` ${Number(
                                                context.raw || 0
                                            ).toFixed(1)}%`

                                }

                            }

                        },

                        scales: {

                            y: {

                                beginAtZero: true,

                                max: 100,

                                grid: {
                                    color:
                                        "rgba(148,163,184,.07)"
                                },

                                ticks: {

                                    color:
                                        "#77849b",

                                    callback:
                                        value =>
                                            `${value}%`

                                }

                            },

                            x: {

                                grid: {
                                    display: false
                                },

                                ticks: {
                                    color:
                                        "#77849b"
                                }

                            }

                        }

                    }

                }
            );


        performanceComparisonChart =
            new Chart(
                performanceCanvas,
                {
                    type: "bar",

                    data: {

                        labels: [
                            "Current",
                            "Simulated"
                        ],

                        datasets: [{

                            label:
                                "Performance Rating",

                            data: [
                                currentPerformance,
                                simulatedPerformance
                            ],

                            borderRadius: 9,

                            borderSkipped: false,

                            backgroundColor: [
                                "#22d3ee",
                                "#8b80ff"
                            ],

                            maxBarThickness: 50

                        }]

                    },

                    options: {

                        responsive: true,

                        maintainAspectRatio: false,

                        plugins: {

                            legend: {
                                display: false
                            }

                        },

                        scales: {

                            y: {

                                beginAtZero: true,

                                min: 0,

                                max: 5,

                                ticks: {
                                    stepSize: 1,
                                    color:
                                        "#77849b"
                                },

                                grid: {
                                    color:
                                        "rgba(148,163,184,.07)"
                                }

                            },

                            x: {

                                grid: {
                                    display: false
                                },

                                ticks: {
                                    color:
                                        "#77849b"
                                }

                            }

                        }

                    }

                }
            );

    }


    /* ======================================================
       RECOMMENDATION
    ====================================================== */

    function renderRecommendation(
        recommendation
    ) {

        const container =
            document.getElementById(
                "recommendationContent"
            );


        if (!container) {
            return;
        }


        if (!recommendation) {

            container.innerHTML = `
                <div class="simulation-empty-message">
                    No specific intervention was generated.
                </div>
            `;

            return;
        }


        const items =
            Array.isArray(
                recommendation
            )
                ? recommendation
                : [recommendation];


        container.innerHTML = `

            <div class="simulation-recommendation-list">

                ${items.map(
                    (item, index) => `

                        <div class="
                            simulation-recommendation-item
                        ">

                            <span class="
                                simulation-recommendation-number
                            ">
                                ${index + 1}
                            </span>

                            <span>
                                ${escapeHtml(
                                    String(item)
                                )}
                            </span>

                        </div>

                    `
                ).join("")}

            </div>

        `;

    }


    /* ======================================================
       HISTORY
    ====================================================== */

    function getHistory() {

        try {

            const raw =
                localStorage.getItem(
                    HISTORY_KEY
                );


            if (!raw) {
                return [];
            }


            const parsed =
                JSON.parse(
                    raw
                );


            return Array.isArray(
                parsed
            )
                ? parsed
                : [];


        } catch (error) {

            console.error(
                "History read error:",
                error
            );

            return [];

        }

    }


    function saveHistory(
        data,
        scenario
    ) {

        if (!selectedEmployee) {
            return;
        }


        const history =
            getHistory();


        const item = {

            id:
                Date.now(),

            employee_id:
                selectedEmployee.employee_id,

            employee_role:
                selectedEmployee.job_role,

            timestamp:
                new Date().toISOString(),

            current_risk:
                Number(
                    data.current?.attrition_probability
                    || 0
                ),

            simulated_risk:
                Number(
                    data.simulated?.attrition_probability
                    || 0
                ),

            current_performance:
                Number(
                    data.current?.performance_rating
                    || 0
                ),

            simulated_performance:
                Number(
                    data.simulated?.performance_rating
                    || 0
                ),

            scenario:
                scenario

        };


        history.unshift(
            item
        );


        const limited =
            history.slice(
                0,
                20
            );


        localStorage.setItem(
            HISTORY_KEY,
            JSON.stringify(
                limited
            )
        );

    }


    function renderHistory() {

        const historyBody =
            document.getElementById(
                "historyBody"
            );

        const emptyHistory =
            document.getElementById(
                "emptyHistory"
            );

        const historyCount =
            document.getElementById(
                "historyCount"
            );


        if (
            !historyBody ||
            !emptyHistory ||
            !historyCount
        ) {
            return;
        }


        const employeeId =
            selectedEmployee
                ? String(
                    selectedEmployee.employee_id
                )
                : "";


        const history =
            getHistory().filter(
                item =>
                    String(
                        item.employee_id
                    ) === employeeId
            );


        historyCount.textContent =
            `${history.length} ${
                history.length === 1
                    ? "scenario"
                    : "scenarios"
            }`;


        if (!history.length) {

            historyBody.innerHTML =
                "";

            emptyHistory.classList.remove(
                "hidden"
            );

            return;

        }


        emptyHistory.classList.add(
            "hidden"
        );


        historyBody.innerHTML =
            history.map(
                item => {

                    const riskChange =
                        (
                            item.simulated_risk -
                            item.current_risk
                        ) * 100;


                    const riskClass =
                        riskChange < 0
                            ? "positive-change"
                            : riskChange > 0
                                ? "negative-change"
                                : "";


                    const factorCount =
                        countChangedFactors(
                            item.scenario
                        );


                    const performanceText =
                        item.current_performance ===
                        item.simulated_performance

                            ? `Rating ${
                                item.simulated_performance
                            }`

                            : `${item.current_performance}
                                → ${
                                    item.simulated_performance
                                }`;


                    return `

                        <tr>

                            <td>
                                ${formatDate(
                                    item.timestamp
                                )}
                            </td>

                            <td>

                                <span class="
                                    scenario-pill
                                ">

                                    ${factorCount}
                                    factor${
                                        factorCount === 1
                                            ? ""
                                            : "s"
                                    }

                                </span>

                            </td>

                            <td>
                                ${formatPercent(
                                    item.current_risk
                                )}
                            </td>

                            <td>
                                ${formatPercent(
                                    item.simulated_risk
                                )}
                            </td>

                            <td
                                class="${riskClass}"
                            >

                                ${
                                    riskChange < 0
                                        ? `${Math.abs(
                                            riskChange
                                        ).toFixed(1)} pp ↓`

                                        : riskChange > 0
                                            ? `+${riskChange.toFixed(
                                                1
                                            )} pp ↑`

                                            : "No change"
                                }

                            </td>

                            <td>
                                ${escapeHtml(
                                    performanceText.replace(
                                        /\s+/g,
                                        " "
                                    )
                                )}
                            </td>

                        </tr>

                    `;

                }
            ).join("");

    }


    /* ======================================================
       COUNT CHANGED FACTORS
    ====================================================== */

    function countChangedFactors(
        scenario
    ) {

        if (!selectedEmployee) {
            return 0;
        }


        const mapping = {

            burnout_score:
                "burnout_score",

            engagement_score:
                "engagement_score",

            manager_support_score:
                "manager_support_score",

            work_life_balance_score:
                "work_life_balance_score",

            overtime_hours_per_week:
                "overtime_hours_per_week",

            training_hours:
                "training_hours",

            salary_hike_pct:
                "salary_hike_pct",

            years_since_promotion:
                "years_since_promotion"

        };


        let count = 0;


        Object.entries(
            mapping
        ).forEach(
            ([scenarioKey, employeeKey]) => {

                const before =
                    Number(
                        selectedEmployee[
                            employeeKey
                        ]
                    );


                const after =
                    Number(
                        scenario[
                            scenarioKey
                        ]
                    );


                if (
                    Number.isFinite(before) &&
                    Number.isFinite(after) &&
                    Math.abs(
                        before - after
                    ) > 0.0001
                ) {

                    count += 1;

                }

            }
        );


        return count;

    }


    /* ======================================================
       HELPERS
    ====================================================== */

    function getValue(id) {

        const element =
            document.getElementById(id);


        if (!element) {
            return 0;
        }


        return Number(
            element.value
        );

    }


    function setText(id, value) {

        const element =
            document.getElementById(id);

        if (element) {
            element.textContent = value;
        }

    }


    function setRiskBadge(
        elementId,
        riskLevel
    ) {

        const element =
            document.getElementById(
                elementId
            );


        if (!element) {
            return;
        }


        const level =
            String(
                riskLevel ||
                "UNKNOWN"
            ).toUpperCase();


        element.textContent =
            level;


        element.className =
            `risk-badge ${
                level.toLowerCase()
            }`;

    }


    function formatPercent(value) {

        return (
            Number(
                value || 0
            ) * 100
        ).toFixed(1) + "%";

    }


    function formatCurrency(value) {

        const number =
            Number(value);


        if (!Number.isFinite(number)) {
            return "--";
        }


        return new Intl.NumberFormat(
            "en-IN",
            {
                style:
                    "currency",

                currency:
                    "INR",

                maximumFractionDigits:
                    0
            }
        ).format(number);

    }


    function formatDate(timestamp) {

        const date =
            new Date(
                timestamp
            );


        if (
            Number.isNaN(
                date.getTime()
            )
        ) {
            return "--";
        }


        return date.toLocaleString(
            "en-IN",
            {
                day: "2-digit",
                month: "short",
                hour: "2-digit",
                minute: "2-digit"
            }
        );

    }


    function escapeHtml(value) {

        return String(
            value ?? ""
        )
            .replaceAll(
                "&",
                "&amp;"
            )
            .replaceAll(
                "<",
                "&lt;"
            )
            .replaceAll(
                ">",
                "&gt;"
            )
            .replaceAll(
                '"',
                "&quot;"
            )
            .replaceAll(
                "'",
                "&#039;"
            );

    }


    function showError(message) {

        if (!simulationError) {
            return;
        }


        simulationError.innerHTML = `

            <i data-lucide="alert-circle"></i>

            <span>
                ${escapeHtml(message)}
            </span>

        `;


        simulationError.classList.remove(
            "hidden"
        );


        refreshIcons();

    }


    function clearError() {

        if (!simulationError) {
            return;
        }


        simulationError.classList.add(
            "hidden"
        );


        simulationError.textContent =
            "";

    }


    /* ======================================================
       INITIAL LOAD
    ====================================================== */

    refreshIcons();

    loadEmployees();

});