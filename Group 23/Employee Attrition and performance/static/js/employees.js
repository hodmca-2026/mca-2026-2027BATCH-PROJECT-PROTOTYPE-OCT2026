document.addEventListener("DOMContentLoaded", () => {

    /* =====================================================
       DOM ELEMENTS
    ===================================================== */

    const searchInput =
        document.getElementById("employeeSearch");

    const departmentFilter =
        document.getElementById("departmentFilter");

    const clearFilters =
        document.getElementById("clearFilters");

    const tableBody =
        document.getElementById("employeeTableBody");

    const employeeCount =
        document.getElementById("employeeCount");

    const pageInfo =
        document.getElementById("pageInfo");

    const previousPage =
        document.getElementById("previousPage");

    const nextPage =
        document.getElementById("nextPage");

    const paginationText =
        document.getElementById("paginationText");

    const rosterStatus =
        document.getElementById("rosterStatus");


    /* Assessment */

    const panel =
        document.getElementById("employeePanel");

    const closePanel =
        document.getElementById("closeEmployeePanel");

    const selectedEmployeeId =
        document.getElementById("selectedEmployeeId");

    const employeeProfile =
        document.getElementById("employeeProfile");

    const runAssessment =
        document.getElementById("runAssessment");

    const explainAssessment =
        document.getElementById("explainAssessment");

    const employeePolicies =
        document.getElementById("employeePolicies");


    /* =====================================================
       STATE
    ===================================================== */

    let currentPage = 1;
    let totalPages = 1;
    let selectedEmployee = null;
    let searchTimer = null;


    /* =====================================================
       HELPERS
    ===================================================== */

    function refreshIcons() {

        if (window.lucide) {
            lucide.createIcons();
        }

    }


    function setText(id, value) {

        const element =
            document.getElementById(id);

        if (element) {
            element.textContent = value;
        }

    }


    function setRosterStatus(message, error = false) {

        if (!rosterStatus) {
            return;
        }

        rosterStatus.textContent = message;

        rosterStatus.classList.toggle(
            "error",
            error
        );

    }


    /* =====================================================
       LOAD EMPLOYEES
    ===================================================== */

    async function loadEmployees() {

        tableBody.innerHTML = `

            <tr>

                <td colspan="7">

                    <div class="empty-state roster-loading">

                        <div class="loading-ring"></div>

                        <h3>
                            Loading employees
                        </h3>

                        <p>
                            Retrieving workforce records...
                        </p>

                    </div>

                </td>

            </tr>

        `;


        setRosterStatus(
            "Loading workforce records..."
        );


        const params =
            new URLSearchParams({

                search:
                    searchInput.value.trim(),

                department:
                    departmentFilter.value,

                page:
                    currentPage,

                per_page:
                    20

            });


        try {

            const response =
                await fetch(
                    `/api/employees?${params}`,
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


            currentPage =
                Number(data.page || 1);

            totalPages =
                Math.max(
                    Number(data.pages || 1),
                    1
                );


            const total =
                Number(data.total || 0);


            employeeCount.textContent =
                `${total.toLocaleString(
                    "en-IN"
                )} Employees`;


            pageInfo.textContent =
                `Page ${currentPage} of ${totalPages}`;


            paginationText.textContent =
                total
                    ? `${total.toLocaleString(
                        "en-IN"
                    )} employees`
                    : "No employees";


            previousPage.disabled =
                currentPage <= 1;


            nextPage.disabled =
                currentPage >= totalPages;


            populateDepartments(
                data.departments || []
            );


            renderEmployees(
                data.employees || []
            );


            setRosterStatus(
                `${total.toLocaleString(
                    "en-IN"
                )} workforce records`
            );


        } catch (error) {

            console.error(
                "Employee load error:",
                error
            );


            tableBody.innerHTML = `

                <tr>

                    <td colspan="7">

                        <div class="empty-state">

                            <div class="error-state-icon">
                                <i data-lucide="alert-circle"></i>
                            </div>

                            <h3>
                                Unable to load employees
                            </h3>

                            <p>
                                ${escapeHtml(
                                    error.message
                                )}
                            </p>

                        </div>

                    </td>

                </tr>

            `;


            setRosterStatus(
                "Unable to load workforce records",
                true
            );


            refreshIcons();

        }

    }


    /* =====================================================
       DEPARTMENT FILTER
    ===================================================== */

    function populateDepartments(departments) {

        const currentValue =
            departmentFilter.value;


        departmentFilter.innerHTML = `

            <option value="">
                All Departments
            </option>

        `;


        departments.forEach(
            department => {

                const option =
                    document.createElement("option");


                option.value =
                    department;


                option.textContent =
                    department;


                departmentFilter.appendChild(
                    option
                );

            }
        );


        const available =
            [...departmentFilter.options]
                .some(
                    option =>
                        option.value ===
                        currentValue
                );


        departmentFilter.value =
            available
                ? currentValue
                : "";

    }


    /* =====================================================
       RENDER EMPLOYEE TABLE
    ===================================================== */

    function renderEmployees(employees) {

        if (!employees.length) {

            tableBody.innerHTML = `

                <tr>

                    <td colspan="7">

                        <div class="empty-state">

                            <div class="empty-state-icon">
                                <i data-lucide="users-round"></i>
                            </div>

                            <h3>
                                No employees found
                            </h3>

                            <p>
                                Try another search term
                                or department filter.
                            </p>

                        </div>

                    </td>

                </tr>

            `;


            refreshIcons();

            return;

        }


        tableBody.innerHTML =
            employees.map(
                employee => {

                    const performance =
                        Number(
                            employee.performance_rating
                        );


                    const performanceClass =
                        performance >= 4
                            ? "performance-high"
                            : performance === 3
                                ? "performance-mid"
                                : "performance-low";


                    return `

                        <tr>

                            <td>

                                <div class="employee-id-cell">

                                    <div class="employee-avatar">
                                        <i data-lucide="user"></i>
                                    </div>

                                    <strong>
                                        ${escapeHtml(
                                            employee.employee_id
                                        )}
                                    </strong>

                                </div>

                            </td>


                            <td>

                                <span class="table-secondary">
                                    ${escapeHtml(
                                        employee.department
                                    )}
                                </span>

                            </td>


                            <td>

                                <span class="role-cell">
                                    ${escapeHtml(
                                        employee.job_role
                                    )}
                                </span>

                            </td>


                            <td>

                                <span class="level-pill">
                                    L${escapeHtml(
                                        employee.job_level
                                    )}
                                </span>

                            </td>


                            <td>

                                ${escapeHtml(
                                    employee.years_at_company
                                )}

                                <span class="years-label">
                                    yrs
                                </span>

                            </td>


                            <td>

                                <span class="
                                    performance-pill
                                    ${performanceClass}
                                ">

                                    <span class="performance-dot"></span>

                                    Rating
                                    ${escapeHtml(
                                        employee.performance_rating
                                    )}

                                </span>

                            </td>


                            <td>

                                <button
                                    type="button"
                                    class="btn btn-secondary employee-assess-btn"
                                    data-employee-id="${escapeHtml(
                                        employee.employee_id
                                    )}"
                                >

                                    <i data-lucide="scan-search"></i>

                                    Assess

                                </button>

                            </td>

                        </tr>

                    `;

                }
            ).join("");


        tableBody
            .querySelectorAll(
                ".employee-assess-btn"
            )
            .forEach(button => {

                button.addEventListener(
                    "click",
                    () => {

                        openEmployee(
                            button.dataset.employeeId
                        );

                    }
                );

            });


        refreshIcons();

    }


    /* =====================================================
       OPEN EMPLOYEE
    ===================================================== */

    window.openEmployee =
        async function(employeeId) {

            try {

                setRosterStatus(
                    `Opening employee ${employeeId}...`
                );


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
                        "Employee not found."
                    );

                }


                selectedEmployee =
                    data.employee;


                selectedEmployeeId.textContent =
                    `Employee ID: ${
                        selectedEmployee.employee_id
                    }`;


                renderProfile(
                    selectedEmployee
                );


                resetAssessment();


                panel.classList.remove(
                    "hidden"
                );


                panel.scrollIntoView({

                    behavior: "smooth",

                    block: "start"

                });


                setRosterStatus(
                    `Reviewing employee ${
                        selectedEmployee.employee_id
                    }`
                );


            } catch (error) {

                console.error(
                    "Open employee error:",
                    error
                );


                setRosterStatus(
                    error.message,
                    true
                );

                alert(
                    error.message
                );

            }

        };


    /* =====================================================
       EMPLOYEE PROFILE
    ===================================================== */

    function renderProfile(employee) {

        const fields = [

            [
                "Age",
                employee.age
            ],

            [
                "Gender",
                employee.gender
            ],

            [
                "Education",
                employee.education_level
            ],

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
                "Monthly Income",
                formatCurrency(
                    employee.monthly_income
                )
            ],

            [
                "Years at Company",
                employee.years_at_company
            ],

            [
                "Total Working Years",
                employee.total_working_years
            ],

            [
                "Years Since Promotion",
                employee.years_since_promotion
            ],

            [
                "Overtime / Week",
                employee.overtime_hours_per_week
            ],

            [
                "Training Hours",
                employee.training_hours
            ],

            [
                "Manager Support",
                employee.manager_support_score
            ],

            [
                "Burnout",
                employee.burnout_score
            ],

            [
                "Engagement",
                employee.engagement_score
            ],

            [
                "Work-Life Balance",
                employee.work_life_balance_score
            ],

            [
                "Performance Rating",
                employee.performance_rating
            ],

            [
                "Last Review",
                employee.last_review_score
            ],

            [
                "AI Tools at Work",
                employee.uses_ai_tools_at_work
                    ? "Yes"
                    : "No"
            ],

            [
                "Perceived AI Job Risk",
                employee.perceived_ai_job_risk
            ]

        ];


        employeeProfile.innerHTML =
            fields.map(
                ([label, value]) => `

                    <div class="employee-profile-item">

                        <span>
                            ${escapeHtml(label)}
                        </span>

                        <strong>
                            ${escapeHtml(value)}
                        </strong>

                    </div>

                `
            ).join("");

    }


    /* =====================================================
       RUN AI ASSESSMENT
    ===================================================== */

    runAssessment.addEventListener(
        "click",
        async () => {

            if (!selectedEmployee) {
                return;
            }


            runAssessment.disabled = true;

            explainAssessment.disabled = true;


            runAssessment.innerHTML = `

                <span class="button-spinner"></span>

                Running Assessment...

            `;


            refreshIcons();


            try {

                const response =
                    await fetch(
                        "/api/predict",
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
                                    selectedEmployee
                                )

                        }
                    );


                const data =
                    await response.json();


                if (!response.ok) {

                    throw new Error(
                        data.error ||
                        "Prediction failed."
                    );

                }


                displayAssessment(
                    data
                );


                explainAssessment.disabled =
                    false;


                await loadActionCenter(
                    selectedEmployee.employee_id
                );


            } catch (error) {

                console.error(
                    "Assessment error:",
                    error
                );


                showAssessmentError(
                    error.message
                );


            } finally {

                runAssessment.disabled =
                    false;


                runAssessment.innerHTML = `

                    <i data-lucide="brain-circuit"></i>

                    Run AI Assessment

                `;


                refreshIcons();

            }

        }
    );


    /* =====================================================
       DISPLAY ASSESSMENT
    ===================================================== */

    function displayAssessment(result) {

        const attrition =
            result.attrition || {};

        const performance =
            result.performance || {};


        /* ATTRITION */

        const probability =
            Number(
                attrition.probability ??
                attrition.attrition_probability ??
                0
            );


        const risk =
            String(
                attrition.risk_level ??
                attrition.risk ??
                "UNKNOWN"
            ).toUpperCase();


        setText(
            "employeeRisk",
            `${(
                probability * 100
            ).toFixed(1)}%`
        );


        const riskBadge =
            document.getElementById(
                "employeeRiskBadge"
            );


        riskBadge.textContent =
            risk;


        riskBadge.className =
            `badge ${
                getRiskBadgeClass(risk)
            }`;


        if (
            attrition.threshold !== undefined &&
            attrition.threshold !== null
        ) {

            setText(
                "employeeRiskThreshold",
                `Decision threshold: ${
                    Number(
                        attrition.threshold
                    ).toFixed(2)
                }`
            );

        }


        setText(
            "employeeRiskPercent",
            `${(
                probability * 100
            ).toFixed(1)}%`
        );


        const riskBar =
            document.getElementById(
                "employeeRiskBar"
            );


        riskBar.style.width =
            `${Math.min(
                probability * 100,
                100
            )}%`;


        riskBar.classList.remove(
            "risk-low",
            "risk-medium",
            "risk-high"
        );


        riskBar.classList.add(
            `risk-${risk.toLowerCase()}`
        );


        document.getElementById(
            "employeeRiskIndicator"
        ).classList.add("is-visible");


        /* PERFORMANCE */

        const rating =
            performance.predicted_rating ??
            performance.rating ??
            "--";


        const label =
            performance.label ??
            performance.performance_label ??
            "Predicted Performance";


        const confidence =
            Number(
                performance.confidence ??
                0
            );


        setText(
            "employeePerformance",
            rating
        );


        setText(
            "employeePerformanceLabel",
            label
        );


        setText(
            "employeePerformanceConfidence",
            `Confidence: ${
                (
                    confidence * 100
                ).toFixed(1)
            }%`
        );


        displayRecommendations(
            result.recommendations
        );

    }


    /* =====================================================
       HR RECOMMENDATIONS
    ===================================================== */

    function displayRecommendations(
        recommendations
    ) {

        const container =
            document.getElementById(
                "employeeRecommendations"
            );


        if (
            !recommendations ||
            (
                Array.isArray(
                    recommendations
                ) &&
                recommendations.length === 0
            )
        ) {

            container.innerHTML = "";

            return;

        }


        const items =
            Array.isArray(
                recommendations
            )
                ? recommendations
                : [recommendations];


        container.innerHTML = `

            <article class="action-center-card">

                <div class="action-center-header">

                    <div>

                        <span class="section-kicker">
                            Decision support
                        </span>

                        <h3>
                            Recommended HR Actions
                        </h3>

                        <p>
                            Model-informed actions for HR review.
                        </p>

                    </div>

                    <span class="badge badge-low">
                        Action Center
                    </span>

                </div>


                <div class="recommendation-list-modern">

                    ${items.map(
                        (item, index) => `

                            <div class="recommendation-item-modern">

                                <div class="recommendation-number">
                                    ${index + 1}
                                </div>

                                <div class="recommendation-text">
                                    ${escapeHtml(
                                        item
                                    )}
                                </div>

                            </div>

                        `
                    ).join("")}

                </div>

            </article>

        `;

    }


    /* =====================================================
       HR POLICY INTELLIGENCE
    ===================================================== */

    async function loadActionCenter(
        employeeId
    ) {

        employeePolicies.innerHTML = `

            <article class="policy-card">

                <div class="policy-loading">

                    <div class="loading-ring small"></div>

                    <div>

                        <strong>
                            Finding Relevant HR Policies...
                        </strong>

                        <p>
                            Using employee risk factors
                            and Information Retrieval.
                        </p>

                    </div>

                </div>

            </article>

        `;


        try {

            const response =
                await fetch(
                    `/api/employees/${encodeURIComponent(
                        employeeId
                    )}/action-center`,
                    {
                        method: "POST",

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
                    "Policy retrieval failed."
                );

            }


            renderPolicies(
                data
            );


        } catch (error) {

            console.error(
                "Policy retrieval error:",
                error
            );


            employeePolicies.innerHTML = `

                <article class="policy-card policy-error">

                    <div class="policy-error-icon">
                        <i data-lucide="alert-circle"></i>
                    </div>

                    <div>

                        <strong>
                            Policy Retrieval Error
                        </strong>

                        <p>
                            ${escapeHtml(
                                error.message
                            )}
                        </p>

                    </div>

                </article>

            `;


            refreshIcons();

        }

    }


    /* =====================================================
       RENDER HR POLICIES
    ===================================================== */

    function renderPolicies(data) {

        const policies =
            data.policies || [];


        if (!policies.length) {

            employeePolicies.innerHTML = `

                <article class="policy-card">

                    <div class="empty-state">

                        <div class="empty-state-icon">
                            <i data-lucide="book-x"></i>
                        </div>

                        <h3>
                            No supporting HR policies found
                        </h3>

                        <p>
                            Use the HR Knowledge page for
                            manual policy search.
                        </p>

                    </div>

                </article>

            `;


            refreshIcons();

            return;

        }


        employeePolicies.innerHTML = `

            <article class="policy-card">

                <div class="policy-card-header">

                    <div>

                        <span class="section-kicker">
                            HR knowledge intelligence
                        </span>

                        <h3>
                            Relevant HR Policies
                        </h3>

                        <p>
                            Documents retrieved from the employee's
                            risk and performance profile.
                        </p>

                    </div>

                    <span class="badge badge-low">
                        IR Powered
                    </span>

                </div>


                ${
                    data.query
                        ? `
                            <div class="generated-query-box">

                                <span>
                                    Generated HR Search Query
                                </span>

                                <p>
                                    ${escapeHtml(
                                        data.query
                                    )}
                                </p>

                            </div>
                        `
                        : ""
                }


                <div class="policy-list">

                    ${policies.map(
                        (policy, index) => `

                            <article class="policy-item">

                                <div class="policy-item-main">

                                    <div>

                                        <h4>
                                            ${index + 1}.
                                            ${escapeHtml(
                                                policy.document
                                            )}
                                        </h4>

                                        <span>
                                            Supporting HR document
                                        </span>

                                    </div>

                                    <span class="relevance-pill">
                                        Relevance
                                        ${
                                            Number(
                                                policy.relevance
                                            ).toFixed(0)
                                        }
                                    </span>

                                </div>


                                <div class="policy-methods">

                                    ${(policy.methods || [])
                                        .map(
                                            evidence => `

                                                <span class="method-pill">

                                                    ${
                                                        escapeHtml(
                                                            evidence.method
                                                        )
                                                    }

                                                    · Rank
                                                    ${
                                                        escapeHtml(
                                                            evidence.rank
                                                        )
                                                    }

                                                </span>

                                            `
                                        )
                                        .join("")}

                                </div>

                            </article>

                        `
                    ).join("")}

                </div>

            </article>

        `;


        refreshIcons();

    }


    /* =====================================================
       SHAP EXPLANATION
    ===================================================== */

    explainAssessment.addEventListener(
        "click",
        async () => {

            if (!selectedEmployee) {
                return;
            }


            explainAssessment.disabled =
                true;


            explainAssessment.innerHTML = `

                <span class="button-spinner"></span>

                Generating Explanation...

            `;


            refreshIcons();


            const container =
                document.getElementById(
                    "employeeExplanation"
                );


            container.innerHTML = `

                <article class="explanation-card">

                    <div class="explanation-loading">

                        <div class="loading-ring small"></div>

                        <div>

                            <strong>
                                Calculating SHAP explanation...
                            </strong>

                            <p>
                                Computing the model factors
                                contributing to the prediction.
                            </p>

                        </div>

                    </div>

                </article>

            `;


            try {

                const response =
                    await fetch(
                        `/api/employees/${encodeURIComponent(
                            selectedEmployee.employee_id
                        )}/explain`,
                        {
                            method: "POST",

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
                        "Explanation failed."
                    );

                }


                renderExplanation(
                    data.explanations || []
                );


            } catch (error) {

                console.error(
                    "SHAP error:",
                    error
                );


                container.innerHTML = `

                    <article class="
                        explanation-card
                        explanation-error
                    ">

                        <div class="prediction-error">

                            <div class="prediction-error-icon">
                                <i data-lucide="alert-circle"></i>
                            </div>

                            <div>

                                <strong>
                                    Explanation Error
                                </strong>

                                <p>
                                    ${escapeHtml(
                                        error.message
                                    )}
                                </p>

                            </div>

                        </div>

                    </article>

                `;


                refreshIcons();

            } finally {

                explainAssessment.disabled =
                    false;


                explainAssessment.innerHTML = `

                    <i data-lucide="sparkles"></i>

                    Explain Prediction

                `;


                refreshIcons();

            }

        }
    );


    /* =====================================================
       RENDER SHAP
    ===================================================== */

    function renderExplanation(
        explanations
    ) {

        const container =
            document.getElementById(
                "employeeExplanation"
            );


        if (!explanations.length) {

            container.innerHTML = `

                <article class="explanation-card">

                    <div class="empty-state">

                        <div class="empty-state-icon">
                            <i data-lucide="info"></i>
                        </div>

                        <h3>
                            No significant factors found
                        </h3>

                        <p>
                            The explanation model returned
                            no significant factors.
                        </p>

                    </div>

                </article>

            `;


            refreshIcons();

            return;

        }


        container.innerHTML = `

            <article class="explanation-card">

                <div class="explanation-header">

                    <div>

                        <span class="section-kicker">
                            Explainable AI
                        </span>

                        <h3>
                            Why This Prediction?
                        </h3>

                        <p>
                            SHAP-based explanation of the
                            attrition prediction.
                        </p>

                    </div>

                    <span class="badge badge-medium">
                        XAI
                    </span>

                </div>


                <div class="interpretation-box">

                    <span>
                        Interpretation
                    </span>

                    <p>
                        Higher positive impact values indicate
                        factors associated with a higher predicted
                        attrition risk; negative impact values indicate
                        lower predicted attrition risk.
                    </p>

                </div>


                <div class="shap-result-list">

                    ${explanations.map(
                        item => {

                            const impact =
                                Number(
                                    item.impact
                                );


                            const importance =
                                Number(
                                    item.importance ??
                                    Math.abs(
                                        impact
                                    )
                                );


                            const positive =
                                impact > 0;


                            const width =
                                Math.min(
                                    Math.max(
                                        importance * 1000,
                                        8
                                    ),
                                    100
                                );


                            return `

                                <div class="shap-result-item">

                                    <div class="shap-result-header">

                                        <div>

                                            <strong>
                                                ${escapeHtml(
                                                    formatFeatureName(
                                                        item.feature
                                                    )
                                                )}
                                            </strong>

                                            <span class="
                                                shap-direction
                                                ${
                                                    positive
                                                        ? "shap-positive"
                                                        : "shap-negative"
                                                }
                                            ">

                                                ${
                                                    positive
                                                        ? "Increases"
                                                        : "Decreases"
                                                }
                                                predicted risk

                                            </span>

                                        </div>


                                        <strong class="
                                            shap-impact
                                            ${
                                                positive
                                                    ? "impact-positive"
                                                    : "impact-negative"
                                            }
                                        ">

                                            ${
                                                positive
                                                    ? "↑"
                                                    : "↓"
                                            }

                                            ${Math.abs(
                                                impact
                                            ).toFixed(4)}

                                        </strong>

                                    </div>


                                    <div class="progress-track">

                                        <div
                                            class="
                                                progress-fill
                                                shap-progress
                                                ${
                                                    positive
                                                        ? "shap-positive-fill"
                                                        : "shap-negative-fill"
                                                }
                                            "
                                            style="
                                                width:${width}%;
                                            "
                                        ></div>

                                    </div>

                                </div>

                            `;

                        }
                    ).join("")}

                </div>

            </article>

        `;


        refreshIcons();

    }


    /* =====================================================
       RESET ASSESSMENT
    ===================================================== */

    function resetAssessment() {

        setText(
            "employeeRisk",
            "--"
        );


        const riskBadge =
            document.getElementById(
                "employeeRiskBadge"
            );


        riskBadge.textContent =
            "Not Assessed";


        riskBadge.className =
            "badge badge-medium";


        setText(
            "employeeRiskThreshold",
            ""
        );


        const riskIndicator =
            document.getElementById(
                "employeeRiskIndicator"
            );


        riskIndicator.classList.remove(
            "is-visible"
        );


        const riskBar =
            document.getElementById(
                "employeeRiskBar"
            );


        riskBar.style.width =
            "0%";


        riskBar.classList.remove(
            "risk-low",
            "risk-medium",
            "risk-high"
        );


        setText(
            "employeeRiskPercent",
            "--"
        );


        setText(
            "employeePerformance",
            "--"
        );


        setText(
            "employeePerformanceLabel",
            "Not Assessed"
        );


        setText(
            "employeePerformanceConfidence",
            ""
        );


        document.getElementById(
            "employeeRecommendations"
        ).innerHTML = "";


        employeePolicies.innerHTML =
            "";


        document.getElementById(
            "employeeExplanation"
        ).innerHTML = "";


        explainAssessment.disabled =
            true;

    }


    /* =====================================================
       ASSESSMENT ERROR
    ===================================================== */

    function showAssessmentError(
        message
    ) {

        document.getElementById(
            "employeeRecommendations"
        ).innerHTML = `

            <article class="action-center-card">

                <div class="prediction-error">

                    <div class="prediction-error-icon">
                        <i data-lucide="alert-circle"></i>
                    </div>

                    <div>

                        <strong>
                            Assessment Error
                        </strong>

                        <p>
                            ${escapeHtml(
                                message
                            )}
                        </p>

                    </div>

                </div>

            </article>

        `;


        refreshIcons();

    }


    /* =====================================================
       CLOSE PANEL
    ===================================================== */

    closePanel.addEventListener(
        "click",
        () => {

            panel.classList.add(
                "hidden"
            );


            selectedEmployee =
                null;


            setRosterStatus(
                "Employee roster ready"
            );

        }
    );


    /* =====================================================
       SEARCH
    ===================================================== */

    searchInput.addEventListener(
        "input",
        () => {

            clearTimeout(
                searchTimer
            );


            searchTimer =
                setTimeout(
                    () => {

                        currentPage =
                            1;

                        loadEmployees();

                    },
                    300
                );

        }
    );


    /* =====================================================
       DEPARTMENT FILTER
    ===================================================== */

    departmentFilter.addEventListener(
        "change",
        () => {

            currentPage =
                1;

            loadEmployees();

        }
    );


    /* =====================================================
       CLEAR FILTERS
    ===================================================== */

    clearFilters.addEventListener(
        "click",
        () => {

            searchInput.value =
                "";

            departmentFilter.value =
                "";

            currentPage =
                1;

            loadEmployees();

        }
    );


    /* =====================================================
       PAGINATION
    ===================================================== */

    previousPage.addEventListener(
        "click",
        () => {

            if (
                currentPage > 1
            ) {

                currentPage--;

                loadEmployees();

            }

        }
    );


    nextPage.addEventListener(
        "click",
        () => {

            if (
                currentPage < totalPages
            ) {

                currentPage++;

                loadEmployees();

            }

        }
    );


    /* =====================================================
       HELPERS
    ===================================================== */

    function getRiskBadgeClass(
        risk
    ) {

        if (risk === "HIGH") {
            return "badge-high";
        }


        if (risk === "LOW") {
            return "badge-low";
        }


        return "badge-medium";

    }


    function formatFeatureName(
        feature
    ) {

        return String(
            feature ?? ""
        )
            .replace(
                /^numeric__/,
                ""
            )
            .replace(
                /^categorical__/,
                ""
            )
            .replace(
                /_/g,
                " "
            )
            .replace(
                /\b\w/g,
                char => char.toUpperCase()
            );

    }


    function formatCurrency(
        value
    ) {

        const number =
            Number(value);


        if (
            Number.isNaN(
                number
            )
        ) {

            return value;

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


    function escapeHtml(
        value
    ) {

        return String(
            value ?? ""
        )
            .replace(
                /&/g,
                "&amp;"
            )
            .replace(
                /</g,
                "&lt;"
            )
            .replace(
                />/g,
                "&gt;"
            )
            .replace(
                /"/g,
                "&quot;"
            )
            .replace(
                /'/g,
                "&#039;"
            );

    }


    /* =====================================================
       INITIAL LOAD
    ===================================================== */

    refreshIcons();

    loadEmployees();

});