document.addEventListener("DOMContentLoaded", () => {

    const loading =
        document.getElementById(
            "evidenceLoading"
        );

    const content =
        document.getElementById(
            "evidenceContent"
        );

    const errorBox =
        document.getElementById(
            "evidenceError"
        );


    /* =====================================================
       HELPERS
    ===================================================== */

    const percent = value => {

        const number =
            Number(value || 0);

        return `${(
            number * 100
        ).toFixed(1)}%`;

    };


    const escapeHtml = value => {

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

    };


    function refreshIcons() {

        if (window.lucide) {
            lucide.createIcons();
        }

    }


    /* =====================================================
       METRIC TABLE
    ===================================================== */

    function renderTable(
        id,
        rows,
        columns
    ) {

        const body =
            document.getElementById(id);


        if (!body) {
            return;
        }


        if (!Array.isArray(rows) || !rows.length) {

            body.innerHTML = `

                <tr>

                    <td colspan="${columns.length + 1}">

                        <div class="evidence-table-empty">
                            No evaluation rows available.
                        </div>

                    </td>

                </tr>

            `;

            return;

        }


        body.innerHTML =
            rows.map(
                row => {

                    return `

                        <tr>

                            <td class="model-name">
                                ${escapeHtml(
                                    row.model ||
                                    row.name ||
                                    "Model"
                                )}
                            </td>

                            ${columns.map(
                                column => `

                                    <td>
                                        ${percent(
                                            row[column]
                                        )}
                                    </td>

                                `
                            ).join("")}

                        </tr>

                    `;

                }
            ).join("");

    }


    /* =====================================================
       CONFUSION MATRIX
    ===================================================== */

    function renderMatrix(
        id,
        matrix,
        labels
    ) {

        const host =
            document.getElementById(id);


        if (!host) {
            return;
        }


        if (
            !Array.isArray(matrix) ||
            !matrix.length
        ) {

            host.innerHTML = `

                <div class="matrix-empty">
                    No confusion matrix available.
                </div>

            `;

            return;

        }


        const flatValues =
            matrix
                .flat()
                .map(
                    value =>
                        Number(value || 0)
                );


        const maximum =
            Math.max(
                ...flatValues,
                1
            );


        let html = `

            <div class="matrix-axis-top">
                Predicted
            </div>

            <table class="matrix-table">

                <thead>

                    <tr>

                        <th>
                            Actual
                        </th>

                        ${labels.map(
                            label => `
                                <th>
                                    ${escapeHtml(
                                        label
                                    )}
                                </th>
                            `
                        ).join("")}

                    </tr>

                </thead>

                <tbody>

        `;


        matrix.forEach(
            (row, rowIndex) => {

                html += `

                    <tr>

                        <th>
                            ${escapeHtml(
                                labels[rowIndex] ||
                                `Class ${rowIndex + 1}`
                            )}
                        </th>

                `;


                row.forEach(
                    (value, columnIndex) => {

                        const numericValue =
                            Number(value || 0);


                        const intensity =
                            numericValue /
                            maximum;


                        const diagonal =
                            rowIndex ===
                            columnIndex
                                ? "matrix-diagonal"
                                : "";


                        html += `

                            <td
                                class="${diagonal}"
                                style="
                                    --matrix-intensity:
                                        ${Math.min(
                                            intensity,
                                            1
                                        )};
                                "
                            >
                                ${numericValue}
                            </td>

                        `;

                    }
                );


                html += `
                    </tr>
                `;

            }
        );


        html += `

                </tbody>

            </table>

            <div class="matrix-axis-bottom">
                Rows = actual • Columns = predicted
            </div>

        `;


        host.innerHTML =
            html;

    }


    /* =====================================================
       ARCHITECTURE
    ===================================================== */

    function renderArchitecture(
        architecture
    ) {

        const host =
            document.getElementById(
                "attritionArchitecture"
            );


        if (!host) {
            return;
        }


        if (
            !Array.isArray(
                architecture
            ) ||
            !architecture.length
        ) {

            host.innerHTML = `

                <div class="architecture-empty">
                    No architecture information available.
                </div>

            `;

            return;

        }


        host.innerHTML =
            architecture.map(
                (item, index) => {

                    const isLast =
                        index ===
                        architecture.length - 1;


                    return `

                        <div class="architecture-step">

                            <div class="architecture-index">
                                ${index + 1}
                            </div>

                            <div class="architecture-content">

                                <span>
                                    ${escapeHtml(
                                        item.layer ||
                                        "Layer"
                                    )}
                                </span>

                                <strong>
                                    ${escapeHtml(
                                        item.details ||
                                        ""
                                    )}
                                </strong>

                            </div>

                            ${
                                !isLast
                                    ? `
                                        <div class="
                                            architecture-arrow
                                        ">
                                            <i data-lucide="arrow-down"></i>
                                        </div>
                                    `
                                    : ""
                            }

                        </div>

                    `;

                }
            ).join("");

    }


    /* =====================================================
       EVALUATION NOTES
    ===================================================== */

    function renderNotes(
        notes
    ) {

        const host =
            document.getElementById(
                "evaluationNotes"
            );


        if (!host) {
            return;
        }


        if (
            !Array.isArray(notes) ||
            !notes.length
        ) {

            host.innerHTML = `

                <div class="evaluation-note-empty">
                    No evaluation notes available.
                </div>

            `;

            return;

        }


        host.innerHTML =
            notes.map(
                (note, index) => `

                    <div class="
                        evaluation-note-item
                    ">

                        <span class="
                            evaluation-note-number
                        ">
                            ${index + 1}
                        </span>

                        <p>
                            ${escapeHtml(
                                note
                            )}
                        </p>

                    </div>

                `
            ).join("");

    }


    /* =====================================================
       GLOBAL SHAP
    ===================================================== */

    function renderGlobalShap(
        rows
    ) {

        const host =
            document.getElementById(
                "globalShapTable"
            );


        if (!host) {
            return;
        }


        if (
            !Array.isArray(rows) ||
            !rows.length
        ) {

            host.innerHTML = `

                <div class="shap-empty">

                    <i data-lucide="database-zap"></i>

                    <h3>
                        No saved global SHAP artifact
                    </h3>

                    <p>
                        Global SHAP feature importance is not
                        currently available from the model evidence API.
                    </p>

                </div>

            `;

            refreshIcons();

            return;

        }


        const maxImportance =
            Math.max(
                ...rows.map(
                    row =>
                        Number(
                            row.importance || 0
                        )
                ),
                1
            );


        host.innerHTML = `

            <div class="shap-global-list">

                ${rows.map(
                    (row, index) => {

                        const importance =
                            Number(
                                row.importance ||
                                0
                            );


                        const width =
                            (
                                importance /
                                maxImportance
                            ) * 100;


                        return `

                            <div class="
                                shap-global-item
                            ">

                                <div class="
                                    shap-global-header
                                ">

                                    <div class="
                                        shap-feature-name
                                    ">

                                        <span class="
                                            shap-rank
                                        ">
                                            ${index + 1}
                                        </span>

                                        <strong>
                                            ${escapeHtml(
                                                row.feature
                                            )}
                                        </strong>

                                    </div>

                                    <span class="
                                        shap-value
                                    ">
                                        ${importance.toFixed(6)}
                                    </span>

                                </div>


                                <div class="
                                    shap-global-track
                                ">

                                    <div
                                        class="
                                            shap-global-fill
                                        "
                                        style="
                                            width:${Math.min(
                                                width,
                                                100
                                            )}%;
                                        "
                                    ></div>

                                </div>

                            </div>

                        `;

                    }
                ).join("")}

            </div>

        `;

    }


    /* =====================================================
       LOAD EVIDENCE
    ===================================================== */

    async function loadEvidence() {

        try {

            const response =
                await fetch(
                    "/api/model-evidence",
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
                    "Unable to load model evidence."
                );

            }


            /* ATTRITION */

            renderTable(
                "attritionTable",
                data.attrition?.models || [],
                [
                    "accuracy",
                    "precision",
                    "recall",
                    "f1",
                    "roc_auc"
                ]
            );


            renderMatrix(
                "attritionMatrix",
                data.attrition?.confusion_matrix || [],
                [
                    "No Attrition",
                    "Attrition"
                ]
            );


            renderArchitecture(
                data.attrition?.architecture || []
            );


            /* PERFORMANCE */

            renderTable(
                "performanceTable",
                data.performance?.models || [],
                [
                    "accuracy",
                    "macro_precision",
                    "macro_recall",
                    "macro_f1",
                    "weighted_f1"
                ]
            );


            renderMatrix(
                "performanceMatrix",
                data.performance?.confusion_matrix || [],
                [
                    "Rating 2",
                    "Rating 3",
                    "Rating 4",
                    "Rating 5"
                ]
            );


            /* NOTES */

            renderNotes(
                data.notes || []
            );


            /* SHAP */

            renderGlobalShap(
                data.shap || []
            );


            loading.classList.add(
                "hidden"
            );

            content.classList.remove(
                "hidden"
            );


            refreshIcons();


        } catch (error) {

            console.error(
                "Model evidence error:",
                error
            );


            loading.classList.add(
                "hidden"
            );


            const message =
                errorBox.querySelector(
                    "p"
                );


            if (message) {
                message.textContent =
                    error.message;
            }


            errorBox.classList.remove(
                "hidden"
            );


            refreshIcons();

        }

    }


    loadEvidence();

});