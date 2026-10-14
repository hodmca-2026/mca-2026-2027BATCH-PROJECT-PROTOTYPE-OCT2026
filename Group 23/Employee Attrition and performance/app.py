from flask import Flask, render_template, request, jsonify, Response

import csv
import io
import math
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load local environment variables (including BRAVE_SEARCH_API_KEY) from the project root.
load_dotenv(Path(__file__).resolve().parent / ".env")

import joblib
import numpy as np
import pandas as pd
import shap
import tensorflow as tf

from prediction_service import predict_employee
from bm25_search import bm25_search
from ir_search_service import tfidf_search
from language_model_search import search as language_model_search
from ir_analysis import build_ir_analysis


# Industry standard: structured logging, centralised config, input validation
from logger import get_logger
from config import SECRET_KEY, MODEL_INPUT_COLUMNS
from validator import validate_employee

# Phase 2: business intelligence + model versioning
from business_kpi import calculate_employee_kpis, calculate_workforce_kpis
from model_registry import registry as model_registry

logger = get_logger(__name__)



# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(__name__)
app.secret_key = SECRET_KEY



# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_DIR = Path(__file__).resolve().parent

# HR document storage
EXTRACTED_DOCUMENTS_PATH = (
    PROJECT_DIR
    / "extracted_documents"
)

HR_DOCUMENTS_PATH = (
    PROJECT_DIR
    / "hr_documents"
)

EMPLOYEE_DATA_PATH = (
    PROJECT_DIR
    / "data"
    / "employee_attrition_hr_2026.csv"
)

ATTRITION_MODEL_PATH = (
    PROJECT_DIR
    / "models"
    / "attrition_deep_learning.keras"
)

ATTRITION_PREPROCESSOR_PATH = (
    PROJECT_DIR
    / "artifacts"
    / "attrition_preprocessor.pkl"
)

ATTRITION_FEATURE_NAMES_PATH = (
    PROJECT_DIR
    / "artifacts"
    / "attrition_feature_names.csv"
)

ATTRITION_X_TRAIN_PATH = (
    PROJECT_DIR
    / "processed_data"
    / "attrition_X_train.npy"
)


# =========================================================
# MODEL INPUT COLUMNS
# =========================================================

MODEL_INPUT_COLUMNS = [
    "age",
    "gender",
    "marital_status",
    "education_level",
    "department",
    "job_role",
    "job_level",
    "monthly_income",
    "stock_option_level",
    "salary_hike_pct",
    "years_at_company",
    "total_working_years",
    "years_since_promotion",
    "num_prior_companies",
    "work_mode",
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
    "uses_ai_tools_at_work",
    "perceived_ai_job_risk",
]


# =========================================================
# SHAP CACHE
# =========================================================

_attrition_model = None
_attrition_preprocessor = None
_attrition_feature_names = None
_shap_background = None


# =========================================================
# LOAD SHAP MODEL
# =========================================================

def load_explainability_model():
    """
    Load SHAP-related model artifacts only when
    an explanation is requested.
    """

    global _attrition_model
    global _attrition_preprocessor
    global _attrition_feature_names
    global _shap_background

    if _attrition_model is None:
        _attrition_model = tf.keras.models.load_model(
            ATTRITION_MODEL_PATH
        )

    if _attrition_preprocessor is None:
        _attrition_preprocessor = joblib.load(
            ATTRITION_PREPROCESSOR_PATH
        )

    if _attrition_feature_names is None:
        _attrition_feature_names = (
            pd.read_csv(
                ATTRITION_FEATURE_NAMES_PATH
            )
            .iloc[:, 0]
            .astype(str)
            .tolist()
        )

    if _shap_background is None:

        background = np.load(
            ATTRITION_X_TRAIN_PATH
        )

        if len(background) > 50:
            background = background[:50]

        _shap_background = np.asarray(
            background,
            dtype=np.float32
        )

    return (
        _attrition_model,
        _attrition_preprocessor,
        _attrition_feature_names,
        _shap_background
    )


# =========================================================
# EMPLOYEE DATA
# =========================================================

def load_employees():
    """
    Load employee records from the actual CSV dataset.
    """

    if not EMPLOYEE_DATA_PATH.exists():

        raise FileNotFoundError(
            "Employee dataset not found:\n"
            f"{EMPLOYEE_DATA_PATH}"
        )

    with open(
        EMPLOYEE_DATA_PATH,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        return list(reader)


# =========================================================
# CLEAN EMPLOYEE
# =========================================================

def clean_employee(employee):
    """
    Convert CSV values into JSON-friendly values.
    """

    numeric_fields = {
        "age",
        "job_level",
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
        "perceived_ai_job_risk",
    }

    result = {}

    for key, value in employee.items():

        if value is None:
            result[key] = None
            continue

        value = str(value).strip()

        if key in numeric_fields:

            try:
                number = float(value)

                if number.is_integer():
                    number = int(number)

                result[key] = number

            except ValueError:
                result[key] = value

        elif key == "uses_ai_tools_at_work":

            result[key] = (
                value.lower()
                in {
                    "true",
                    "1",
                    "yes",
                    "y"
                }
            )

        else:

            result[key] = value

    return result


# =========================================================
# FIND EMPLOYEE
# =========================================================

def find_employee(employee_id):
    """
    Find an employee by employee ID.
    """

    employee_id = str(employee_id).strip().lower()

    for row in load_employees():

        current_id = str(
            row.get(
                "employee_id",
                ""
            )
        ).strip().lower()

        if current_id == employee_id:

            return clean_employee(row)

    return None


# =========================================================
# NUMBER HELPER
# =========================================================

def safe_float(value, default=0.0):

    try:
        return float(value)

    except (
        TypeError,
        ValueError
    ):
        return default


# =========================================================
# PREDICTION NORMALIZER
# =========================================================

def normalize_prediction(prediction, employee=None):
    """
    Convert the prediction_service output into a common format.

    This allows the simulator to work even when the prediction
    service uses nested attrition/performance dictionaries.
    """

    employee = employee or {}

    if not isinstance(prediction, dict):
        prediction = {}

    attrition = prediction.get(
        "attrition",
        {}
    )

    performance = prediction.get(
        "performance",
        {}
    )

    if not isinstance(attrition, dict):
        attrition = {}

    if not isinstance(performance, dict):
        performance = {}

    # -----------------------------------------------------
    # Attrition probability
    # -----------------------------------------------------

    probability = None

    probability_keys = [
        "attrition_probability",
        "probability",
        "risk_probability",
        "score",
    ]

    for key in probability_keys:

        if key in prediction:

            probability = safe_float(
                prediction.get(key)
            )

            break

    if probability is None:

        for key in probability_keys:

            if key in attrition:

                probability = safe_float(
                    attrition.get(key)
                )

                break

    if probability is None:
        probability = 0.0

    # -----------------------------------------------------
    # Risk level
    # -----------------------------------------------------

    risk_level = (
        attrition.get(
            "risk_level"
        )
        or attrition.get(
            "risk"
        )
        or prediction.get(
            "attrition_risk_level"
        )
        or prediction.get(
            "risk_level"
        )
        or ""
    )

    if not risk_level:

        if probability >= 0.64:
            risk_level = "HIGH"

        elif probability >= 0.40:
            risk_level = "MEDIUM"

        else:
            risk_level = "LOW"

    # -----------------------------------------------------
    # Performance rating
    # -----------------------------------------------------

    rating = (
        performance.get(
            "predicted_rating"
        )
        or performance.get(
            "rating"
        )
        or prediction.get(
            "performance_rating"
        )
        or prediction.get(
            "predicted_rating"
        )
        or employee.get(
            "performance_rating",
            3
        )
    )

    try:
        rating = int(float(rating))
    except (
        TypeError,
        ValueError
    ):
        rating = 3

    # -----------------------------------------------------
    # Performance label
    # -----------------------------------------------------

    performance_label = (
        performance.get(
            "label"
        )
        or performance.get(
            "performance_label"
        )
        or prediction.get(
            "performance_label"
        )
        or ""
    )

    # -----------------------------------------------------
    # Confidence
    # -----------------------------------------------------

    confidence = (
        performance.get(
            "confidence"
        )
        or performance.get(
            "performance_confidence"
        )
        or prediction.get(
            "performance_confidence"
        )
        or 0
    )

    confidence = safe_float(
        confidence,
        0
    )

    return {
        "attrition_probability":
            float(probability),

        "risk_level":
            str(risk_level).upper(),

        "performance_rating":
            rating,

        "performance_label":
            str(performance_label),

        "performance_confidence":
            confidence,
    }


# =========================================================
# WEB PAGES
# =========================================================

@app.route("/")
def dashboard():

    return render_template(
        "dashboard.html"
    )


@app.route("/prediction")
def prediction():

    return render_template(
        "prediction.html"
    )


@app.route("/simulator")
def simulator():

    return render_template(
        "simulator.html"
    )


@app.route("/employees")
def employees():

    return render_template(
        "employees.html"
    )


@app.route("/knowledge-search")
def knowledge_search():
    """Render the HR knowledge workspace with a live collection file count."""
    document_count = (
        sum(1 for path in HR_DOCUMENTS_PATH.rglob("*.txt") if path.is_file())
        if HR_DOCUMENTS_PATH.exists()
        else 0
    )
    return render_template(
        "knowledge_search.html",
        document_count=document_count,
    )


@app.route("/model-evidence")
def model_evidence():

    return render_template(
        "model_evidence.html"
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route(
    "/api/health",
    methods=["GET"]
)
def health():
    """
    Health check endpoint.

    Used by load balancers, Kubernetes liveness probes,
    and Docker HEALTHCHECK instructions.
    """
    from config import ENV

    return jsonify({
        "status":    "ok",
        "message":   "HR AI Decision Support System is running",
        "version":   "2.0.0",
        "env":       ENV,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })


# =========================================================
# EMPLOYEE ROSTER API
# =========================================================

@app.route(
    "/api/employees",
    methods=["GET"]
)
def api_employees():

    try:

        employees_data = load_employees()

        search = request.args.get(
            "search",
            ""
        ).strip().lower()

        department = request.args.get(
            "department",
            ""
        ).strip().lower()

        try:

            page = int(
                request.args.get(
                    "page",
                    1
                )
            )

        except ValueError:

            page = 1

        # Support both per_page and page_size
        # so the simulator and roster can use either.

        try:

            per_page = int(
                request.args.get(
                    "per_page",
                    request.args.get(
                        "page_size",
                        20
                    )
                )
            )

        except ValueError:

            per_page = 20

        page = max(
            page,
            1
        )

        per_page = max(
            10,
            min(
                per_page,
                5000
            )
        )

        filtered = []

        for employee in employees_data:

            employee_id = str(
                employee.get(
                    "employee_id",
                    ""
                )
            ).lower()

            employee_department = str(
                employee.get(
                    "department",
                    ""
                )
            ).lower()

            employee_role = str(
                employee.get(
                    "job_role",
                    ""
                )
            ).lower()

            if search:

                if (
                    search not in employee_id
                    and search not in employee_department
                    and search not in employee_role
                ):
                    continue

            if department:

                if employee_department != department:
                    continue

            filtered.append(
                clean_employee(employee)
            )

        total = len(filtered)

        total_pages = max(
            1,
            math.ceil(
                total / per_page
            )
        )

        if page > total_pages:
            page = total_pages

        start = (
            (page - 1)
            * per_page
        )

        end = start + per_page

        page_data = filtered[
            start:end
        ]

        departments = sorted({

            str(
                employee.get(
                    "department",
                    ""
                )
            )

            for employee in employees_data

            if employee.get(
                "department"
            )
        })

        return jsonify({

            "success": True,

            "employees":
                page_data,

            "total":
                total,

            "page":
                page,

            "per_page":
                per_page,

            "page_size":
                per_page,

            "pages":
                total_pages,

            "departments":
                departments
        })

    except Exception as error:

        print(
            "Employee roster error:",
            error
        )

        return jsonify({

            "success": False,

            "error":
                str(error)

        }), 500


# =========================================================
# SINGLE EMPLOYEE API
# =========================================================

@app.route(
    "/api/employees/<employee_id>",
    methods=["GET"]
)
def api_employee(employee_id):

    try:

        employee = find_employee(
            employee_id
        )

        if employee is None:

            return jsonify({

                "success": False,

                "error":
                    "Employee not found"

            }), 404

        return jsonify({

            "success": True,

            "employee":
                employee

        })

    except Exception as error:

        print(
            "Single employee error:",
            error
        )

        return jsonify({

            "success": False,

            "error":
                str(error)

        }), 500


# =========================================================
# EMPLOYEE PREDICTION API
# =========================================================

@app.route(
    "/api/predict",
    methods=["POST"]
)
def api_predict():
    """
    Single-employee attrition + performance prediction.

    Accepts a JSON body with employee features.
    Returns attrition risk, performance rating, and SHAP
    feature contributions.
    """

    try:

        data = request.get_json()

        if not data:
            logger.warning("Prediction request received with empty body")
            return jsonify({
                "success": False,
                "error": "No employee data received",
            }), 400

        # ── Input validation ──────────────────────────────
        validation = validate_employee(data)

        if not validation.is_valid:
            logger.warning(
                "Prediction rejected — validation errors: %s",
                validation.errors,
            )
            return jsonify({
                "success":  False,
                "error":    "Validation failed",
                "details":  validation.errors,
                "warnings": validation.warnings,
            }), 422

        if validation.warnings:
            logger.info(
                "Prediction proceeding with warnings: %s",
                validation.warnings,
            )

        # ── Run inference ─────────────────────────────────
        logger.info(
            "Running prediction for employee (dept=%s role=%s)",
            data.get("department", "?"),
            data.get("job_role", "?"),
        )

        result = predict_employee(data)

        # Attach validation warnings to response
        if validation.warnings:
            result["validation_warnings"] = validation.warnings

        logger.info("Prediction completed successfully")
        return jsonify(result)

    except Exception as error:

        logger.exception("Prediction error: %s", error)

        return jsonify({
            "success": False,
            "error":   str(error),
        }), 500


# =========================================================
# BATCH PREDICTION API
# =========================================================

@app.route(
    "/api/predict/batch",
    methods=["POST"]
)
def api_predict_batch():
    """
    Batch attrition + performance prediction.

    Accepts a JSON body: ``{"employees": [ {...}, {...}, ... ]}``
    Returns per-employee predictions with a summary section.

    - Up to 100 employees per request.
    - Invalid records are skipped and reported in ``errors``.
    """

    MAX_BATCH_SIZE = 100

    try:

        body = request.get_json()

        if not body or "employees" not in body:
            return jsonify({
                "success": False,
                "error":   "Request body must contain an 'employees' list.",
            }), 400

        employees = body["employees"]

        if not isinstance(employees, list) or len(employees) == 0:
            return jsonify({
                "success": False,
                "error":   "'employees' must be a non-empty list.",
            }), 400

        if len(employees) > MAX_BATCH_SIZE:
            return jsonify({
                "success": False,
                "error":   f"Batch size {len(employees)} exceeds limit of {MAX_BATCH_SIZE}.",
            }), 400

        logger.info("Batch prediction request: %d employees", len(employees))

        results      = []
        errors       = []
        high_risk    = 0
        medium_risk  = 0
        low_risk     = 0

        for idx, employee in enumerate(employees):

            employee_id = (
                str(employee.get("employee_id", ""))
                or f"index_{idx}"
            )

            # Validate
            validation = validate_employee(employee)

            if not validation.is_valid:
                errors.append({
                    "employee_id": employee_id,
                    "index":       idx,
                    "errors":      validation.errors,
                })
                continue

            try:
                prediction = predict_employee(employee)

                # Tally risk distribution
                attrition_data = prediction.get("attrition", {})
                risk_level = str(
                    attrition_data.get("risk_level", "")
                    or attrition_data.get("risk", "LOW")
                ).upper()

                if risk_level == "HIGH":
                    high_risk += 1
                elif risk_level == "MEDIUM":
                    medium_risk += 1
                else:
                    low_risk += 1

                results.append({
                    "employee_id": employee_id,
                    "prediction":  prediction,
                })

            except Exception as err:
                logger.warning(
                    "Batch: prediction failed for %s — %s",
                    employee_id, err,
                )
                errors.append({
                    "employee_id": employee_id,
                    "index":       idx,
                    "errors":      [str(err)],
                })

        total_processed = len(results)
        total_errors    = len(errors)

        logger.info(
            "Batch prediction complete: %d/%d succeeded, "
            "high=%d medium=%d low=%d",
            total_processed,
            len(employees),
            high_risk,
            medium_risk,
            low_risk,
        )

        return jsonify({
            "success":   True,
            "requested": len(employees),
            "processed": total_processed,
            "failed":    total_errors,
            "results":   results,
            "errors":    errors,
            "summary": {
                "high_risk":   high_risk,
                "medium_risk": medium_risk,
                "low_risk":    low_risk,
            },
            "generated_at": datetime.utcnow().isoformat() + "Z",
        })

    except Exception as error:

        logger.exception("Batch prediction error: %s", error)

        return jsonify({
            "success": False,
            "error":   str(error),
        }), 500


# =========================================================
# HR ACTION QUERY
# =========================================================

def build_hr_query(
    employee,
    prediction
):
    """
    Generate an HR retrieval query from
    employee risk and performance signals.
    """

    terms = []

    # -----------------------------------------------------
    # Get prediction sections
    # -----------------------------------------------------

    attrition = prediction.get(
        "attrition",
        {}
    )

    performance = prediction.get(
        "performance",
        {}
    )

    if not isinstance(attrition, dict):
        attrition = {}

    if not isinstance(performance, dict):
        performance = {}

    # -----------------------------------------------------
    # Risk
    # -----------------------------------------------------

    risk = str(
        attrition.get(
            "risk_level",
            attrition.get(
                "risk",
                ""
            )
        )
    ).upper()

    if risk == "HIGH":

        terms.extend([
            "employee",
            "retention",
            "support",
            "wellbeing",
            "workload"
        ])

    elif risk == "MEDIUM":

        terms.extend([
            "employee",
            "engagement",
            "workload",
            "support"
        ])

    else:

        terms.extend([
            "employee",
            "performance",
            "development"
        ])

    # -----------------------------------------------------
    # Burnout
    # -----------------------------------------------------

    burnout = safe_float(
        employee.get(
            "burnout_score",
            0
        )
    )

    if burnout >= 7:

        terms.extend([
            "burnout",
            "wellbeing",
            "assistance"
        ])

    # -----------------------------------------------------
    # Engagement
    # -----------------------------------------------------

    engagement = safe_float(
        employee.get(
            "engagement_score",
            10
        )
    )

    if engagement <= 4:

        terms.extend([
            "engagement",
            "employee",
            "support"
        ])

    # -----------------------------------------------------
    # Manager Support
    # -----------------------------------------------------

    manager_support = safe_float(
        employee.get(
            "manager_support_score",
            10
        )
    )

    if manager_support <= 4:

        terms.extend([
            "manager",
            "support",
            "communication"
        ])

    # -----------------------------------------------------
    # Overtime
    # -----------------------------------------------------

    overtime = safe_float(
        employee.get(
            "overtime_hours_per_week",
            0
        )
    )

    if overtime >= 15:

        terms.extend([
            "overtime",
            "workload",
            "compensation"
        ])

    # -----------------------------------------------------
    # Promotion gap
    # -----------------------------------------------------

    promotion_gap = safe_float(
        employee.get(
            "years_since_promotion",
            0
        )
    )

    if promotion_gap >= 4:

        terms.extend([
            "promotion",
            "career",
            "progression"
        ])

    # -----------------------------------------------------
    # Work-life balance
    # -----------------------------------------------------

    work_life = safe_float(
        employee.get(
            "work_life_balance_score",
            10
        )
    )

    if work_life <= 4:

        terms.extend([
            "work",
            "life",
            "balance",
            "leave"
        ])

    # -----------------------------------------------------
    # Training
    # -----------------------------------------------------

    training = safe_float(
        employee.get(
            "training_hours",
            0
        )
    )

    if training < 15:

        terms.extend([
            "training",
            "skill",
            "development"
        ])

    # -----------------------------------------------------
    # Performance
    # -----------------------------------------------------

    rating = (
        performance.get(
            "predicted_rating"
        )
        or performance.get(
            "rating"
        )
        or employee.get(
            "performance_rating",
            3
        )
    )

    try:

        rating = int(
            float(rating)
        )

    except (
        TypeError,
        ValueError
    ):

        rating = 3

    if rating <= 2:

        terms.extend([
            "performance",
            "improvement",
            "training"
        ])

    elif rating == 3:

        terms.extend([
            "performance",
            "development"
        ])

    elif rating >= 5:

        terms.extend([
            "recognition",
            "reward",
            "career"
        ])

    # -----------------------------------------------------
    # Remove duplicates
    # -----------------------------------------------------

    return " ".join(
        dict.fromkeys(terms)
    )


# =========================================================
# HR ACTION CENTER API
# =========================================================

@app.route(
    "/api/employees/<employee_id>/action-center",
    methods=["POST"]
)
def api_action_center(employee_id):

    try:

        employee = find_employee(
            employee_id
        )

        if employee is None:

            return jsonify({

                "success": False,

                "error":
                    "Employee not found"

            }), 404

        # -------------------------------------------------
        # Real prediction
        # -------------------------------------------------

        prediction = predict_employee(
            employee
        )

        # -------------------------------------------------
        # HR query
        # -------------------------------------------------

        query = build_hr_query(
            employee,
            prediction
        )

        # -------------------------------------------------
        # Retrieval
        # -------------------------------------------------

        bm25_results = bm25_search(
            query,
            top_k=5
        )

        tfidf_results = tfidf_search(
            query,
            top_k=5
        )

        language_results = language_model_search(
            query,
            top_k=5
        )

        # -------------------------------------------------
        # Combine evidence
        # -------------------------------------------------

        combined = {}

        def add_results(
            results,
            method
        ):

            if not results:
                return

            for rank, result in enumerate(
                results,
                start=1
            ):

                if not isinstance(
                    result,
                    dict
                ):
                    continue

                document_id = result.get(
                    "document_id",
                    result.get(
                        "document"
                    )
                )

                if not document_id:
                    continue

                if (
                    document_id
                    not in combined
                ):

                    combined[
                        document_id
                    ] = {

                        "document_id":
                            document_id,

                        "document":
                            result.get(
                                "document",
                                document_id
                            ),

                        "methods": [],

                        "best_rank":
                            rank
                    }

                combined[
                    document_id
                ]["methods"].append({

                    "method":
                        method,

                    "rank":
                        rank,

                    "score":
                        result.get(
                            "score",
                            0
                        )

                })

                combined[
                    document_id
                ]["best_rank"] = min(
                    combined[
                        document_id
                    ]["best_rank"],
                    rank
                )

        add_results(
            bm25_results,
            "BM25"
        )

        add_results(
            tfidf_results,
            "TF-IDF"
        )

        add_results(
            language_results,
            "Language Model"
        )

        policies = list(
            combined.values()
        )

        # -------------------------------------------------
        # Evidence score
        # -------------------------------------------------

        for policy in policies:

            method_count = len(
                policy["methods"]
            )

            rank_bonus = max(
                0,
                6 - policy["best_rank"]
            )

            policy["relevance"] = round(
                method_count * 10
                + rank_bonus,
                2
            )

        policies.sort(
            key=lambda item:
                item["relevance"],
            reverse=True
        )

        policies = policies[:5]

        return jsonify({

            "success": True,

            "employee_id":
                employee_id,

            "prediction":
                prediction,

            "query":
                query,

            "policies":
                policies

        })

    except Exception as error:
        logger.exception("Action center error for %s: %s", employee_id, error)
        return jsonify({"success": False, "error": str(error)}), 500


# =========================================================
# SHAP EXPLANATION API
# =========================================================

@app.route(
    "/api/employees/<employee_id>/explain",
    methods=["POST"]
)
def api_employee_explain(employee_id):

    try:

        employee = find_employee(
            employee_id
        )

        if employee is None:

            return jsonify({

                "success": False,

                "error":
                    "Employee not found"

            }), 404

        (
            model,
            preprocessor,
            feature_names,
            background
        ) = load_explainability_model()

        # -------------------------------------------------
        # Prepare employee data
        # -------------------------------------------------

        model_data = {}

        for column in MODEL_INPUT_COLUMNS:

            if column not in employee:

                return jsonify({

                    "success": False,

                    "error":
                        f"Missing employee field: {column}"

                }), 400

            model_data[column] = employee[
                column
            ]

        employee_df = pd.DataFrame([
            model_data
        ])

        transformed_employee = (
            preprocessor.transform(
                employee_df
            )
        )

        transformed_employee = np.asarray(
            transformed_employee,
            dtype=np.float32
        )

        # -------------------------------------------------
        # Prediction function for SHAP
        # -------------------------------------------------

        def predict_function(x):

            predictions = model.predict(
                x,
                verbose=0
            )

            return predictions.reshape(
                -1
            )

        # -------------------------------------------------
        # Kernel SHAP
        # -------------------------------------------------

        explainer = shap.KernelExplainer(
            predict_function,
            background
        )

        shap_values = explainer.shap_values(
            transformed_employee,
            nsamples=100
        )

        if isinstance(
            shap_values,
            list
        ):

            shap_values = shap_values[0]

        shap_values = np.asarray(
            shap_values
        )

        if shap_values.ndim > 1:

            shap_values = shap_values[0]

        feature_count = min(
            len(feature_names),
            len(shap_values)
        )

        explanations = []

        for index in range(
            feature_count
        ):

            impact = float(
                shap_values[index]
            )

            if abs(impact) < 1e-7:
                continue

            feature_name = (
                feature_names[index]
            )

            explanations.append({

                "feature":
                    feature_name,

                "impact":
                    round(
                        impact,
                        6
                    ),

                "importance":
                    round(
                        abs(impact),
                        6
                    ),

                "direction":
                    (
                        "increases"
                        if impact > 0
                        else "decreases"
                    )

            })

        explanations.sort(
            key=lambda item:
                item["importance"],
            reverse=True
        )

        return jsonify({

            "success": True,

            "employee_id":
                employee_id,

            "explanations":
                explanations[:10]

        })

    except Exception as error:
        logger.exception("SHAP explanation error for %s: %s", employee_id, error)
        return jsonify({"success": False, "error": str(error)}), 500


# =========================================================
# GENERAL HR KNOWLEDGE SEARCH API
# =========================================================

@app.route(
    "/api/search",
    methods=["POST"]
)
def api_search():

    try:

        data = request.get_json()

        if not data:

            return jsonify({

                "success": False,

                "error":
                    "No search data received"

            }), 400

        query = str(
            data.get(
                "query",
                ""
            )
        ).strip()

        method = str(
            data.get(
                "method",
                "bm25"
            )
        ).strip().lower()

        try:

            top_k = int(
                data.get(
                    "top_k",
                    5
                )
            )

        except (
            TypeError,
            ValueError
        ):

            top_k = 5

        if not query:

            return jsonify({

                "success": False,

                "error":
                    "Search query is required"

            }), 400

        top_k = max(
            1,
            min(
                top_k,
                20
            )
        )

        # -------------------------------------------------
        # BM25
        # -------------------------------------------------

        if method == "bm25":

            results = bm25_search(
                query,
                top_k=top_k
            )

            method_name = "BM25"

        # -------------------------------------------------
        # TF-IDF
        # -------------------------------------------------

        elif method == "tfidf":

            results = tfidf_search(
                query,
                top_k=top_k
            )

            method_name = "TF-IDF"

        # -------------------------------------------------
        # Language Model
        # -------------------------------------------------

        elif method == "language_model":

            results = language_model_search(
                query,
                top_k=top_k
            )

            method_name = "Language Model"

        else:

            return jsonify({

                "success": False,

                "error":
                    "Invalid search method. "
                    "Use bm25, tfidf, "
                    "or language_model."

            }), 400

        return jsonify({

            "success": True,

            "query":
                query,

            "method":
                method_name,

            "results":
                results

        })

    except Exception as error:
        logger.exception("Search error: %s", error)
        return jsonify({"success": False, "error": str(error)}), 500




# =========================================================
# EXTERNAL WEBSITE SEARCH API
# =========================================================

# @app.route("/api/web-search", methods=["POST"])
# def api_web_search():
#     """Return external website recommendations independently of internal HR retrieval."""
#     data = request.get_json(silent=True) or {}
#     if not isinstance(data, dict):
#         return jsonify({"success": False, "error": "Invalid request body."}), 400

#     query = str(data.get("query", "")).strip()
#     if not query:
#         return jsonify({"success": False, "error": "Search query is required."}), 400
#     if len(query) > 300:
#         return jsonify({"success": False, "error": "Search query must be 300 characters or fewer."}), 400

#     try:
#         count = int(data.get("count", 6))
#     except (TypeError, ValueError):
#         count = 6
#     count = max(1, min(count, 8))

#     try:
#         results = search_web(query, count=count)
#         return jsonify({
#             "success": True,
#             "query": query,
#             "provider": "Brave Search",
#             "results": results,
#             "result_count": len(results),
#         })
#     except WebSearchNotConfigured as error:
#         # Configuration issues must not affect /api/search or /api/ir-analysis.
#         return jsonify({
#             "success": False,
#             "code": "not_configured",
#             "error": str(error),
#         }), 503
#     except WebSearchAPIError as error:
#         logger.warning("External website search unavailable: %s", error)
#         return jsonify({
#             "success": False,
#             "code": "web_search_unavailable",
#             "error": str(error),
#         }), error.status_code
#     except Exception:
#         logger.exception("Unexpected external website search error")
#         return jsonify({
#             "success": False,
#             "code": "web_search_unavailable",
#             "error": "External website search is temporarily unavailable. Internal HR search is still available.",
#         }), 502



# =========================================================
# IR ANALYTICS API
# =========================================================

@app.route(
    "/api/ir-analysis",
    methods=["POST"]
)
def api_ir_analysis():
    """
    Return an academic IR analysis for the HR Knowledge workspace.

    The endpoint supplements normal retrieval with:
    - multi-model ranking comparison
    - passage retrieval
    - Precision@5 / Recall@5 / F1 / MRR evaluation
    - transparent rule-based information extraction
    """

    try:
        data = request.get_json() or {}

        query = str(
            data.get("query", "")
        ).strip()

        method = str(
            data.get("method", "bm25")
        ).strip().lower()

        try:
            top_k = int(
                data.get("top_k", 5)
            )
        except (TypeError, ValueError):
            top_k = 5

        if not query:
            return jsonify({
                "success": False,
                "error": "Search query is required"
            }), 400

        if method not in {
            "bm25",
            "tfidf",
            "language_model"
        }:
            return jsonify({
                "success": False,
                "error": "Invalid retrieval method"
            }), 400

        top_k = max(
            1,
            min(top_k, 10)
        )

        analysis = build_ir_analysis(
            query,
            top_k=top_k,
            selected_method=method
        )

        return jsonify({
            "success": True,
            "query": query,
            "method": method,
            "analysis": analysis
        })

    except Exception as error:
        logger.exception(
            "IR analysis error: %s",
            error
        )

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# =========================================================
# HR DOCUMENT VIEW API
# =========================================================

@app.route(
    "/api/document/<document_id>",
    methods=["GET"]
)
def api_document(document_id):
    """Return the full source content of one HR knowledge document."""

    try:

        document_id = str(
            document_id
        ).strip()

        if not document_id:

            return jsonify({

                "success": False,

                "error":
                    "Document ID is required"

            }), 400

        # Allow only simple document identifiers.
        safe_document_id = (
            document_id
            .replace("_", "")
            .replace("-", "")
        )

        if not safe_document_id.isalnum():

            return jsonify({

                "success": False,

                "error":
                    "Invalid document ID"

            }), 400

        # Normalize an optional .txt suffix.
        if document_id.lower().endswith(".txt"):

            document_id = document_id[:-4]

        # Look in the extracted document store first.
        extracted_path = (
            EXTRACTED_DOCUMENTS_PATH
            / f"{document_id}.txt"
        )

        document_path = None

        if extracted_path.exists():

            document_path = extracted_path

        # Fall back to the original HR document tree.
        elif HR_DOCUMENTS_PATH.exists():

            for candidate in HR_DOCUMENTS_PATH.rglob(
                f"{document_id}.txt"
            ):

                document_path = candidate
                break

        if document_path is None:

            return jsonify({

                "success": False,

                "error":
                    "Document not found"

            }), 404

        content = document_path.read_text(
            encoding="utf-8"
        )

        category = "HR Knowledge"

        try:

            relative_path = document_path.relative_to(
                HR_DOCUMENTS_PATH
            )

            if len(relative_path.parts) > 1:

                category = (
                    relative_path.parts[0]
                    .replace("_", " ")
                    .title()
                )

        except ValueError:

            category = "HR Knowledge"

        title = (
            document_id
            .replace("_", " ")
            .replace("-", " ")
            .title()
        )

        return jsonify({

            "success": True,

            "document_id":
                document_id,

            "title":
                title,

            "category":
                category,

            "content":
                content

        })

    except Exception as error:
        logger.exception("Document retrieval error for %s: %s", document_id, error)
        return jsonify({"success": False, "error": str(error)}), 500


# =========================================================
# RISK SIMULATOR
# =========================================================

@app.route(
    "/api/simulate",
    methods=["POST"]
)
def api_simulate():

    try:

        data = request.get_json()

        if not data:

            return jsonify({

                "success": False,

                "error":
                    "No simulation data received."

            }), 400

        employee_id = str(
            data.get(
                "employee_id",
                ""
            )
        ).strip()

        if not employee_id:

            return jsonify({

                "success": False,

                "error":
                    "Employee ID is required."

            }), 400

        # -------------------------------------------------
        # Find employee
        # -------------------------------------------------

        employee = find_employee(
            employee_id
        )

        if employee is None:

            return jsonify({

                "success": False,

                "error":
                    f"Employee {employee_id} not found."

            }), 404

        # -------------------------------------------------
        # Copies
        # -------------------------------------------------

        current_employee = dict(
            employee
        )

        simulated_employee = dict(
            employee
        )

        # -------------------------------------------------
        # Simulation fields
        # -------------------------------------------------

        simulation_fields = [

            "burnout_score",

            "engagement_score",

            "manager_support_score",

            "work_life_balance_score",

            "overtime_hours_per_week",

            "training_hours",

            "salary_hike_pct",

            "years_since_promotion",

        ]

        # -------------------------------------------------
        # Apply scenario values
        # -------------------------------------------------

        for field in simulation_fields:

            if field not in data:
                continue

            try:

                simulated_employee[field] = (
                    float(data[field])
                )

            except (
                TypeError,
                ValueError
            ):

                return jsonify({

                    "success": False,

                    "error":
                        f"Invalid value for {field}."

                }), 400

        # -------------------------------------------------
        # Predict current state
        # -------------------------------------------------

        current_raw = predict_employee(
            current_employee
        )

        # -------------------------------------------------
        # Predict simulated state
        # -------------------------------------------------

        simulated_raw = predict_employee(
            simulated_employee
        )

        # -------------------------------------------------
        # Normalize predictions
        # -------------------------------------------------

        current = normalize_prediction(
            current_raw,
            current_employee
        )

        simulated = normalize_prediction(
            simulated_raw,
            simulated_employee
        )

        # -------------------------------------------------
        # Changes
        # -------------------------------------------------

        risk_change = (
            simulated[
                "attrition_probability"
            ]
            -
            current[
                "attrition_probability"
            ]
        )

        performance_change = (
            simulated[
                "performance_rating"
            ]
            -
            current[
                "performance_rating"
            ]
        )

        # -------------------------------------------------
        # Recommendation
        # -------------------------------------------------

        recommendations = []

        # Risk impact

        if risk_change < -0.03:

            recommendations.append(
                "The simulated scenario lowers the model's "
                "predicted attrition probability. Review the "
                "corresponding workplace intervention."
            )

        elif risk_change > 0.03:

            recommendations.append(
                "The simulated scenario increases the model's "
                "predicted attrition probability. Review "
                "workload, engagement and employee support."
            )

        else:

            recommendations.append(
                "The simulated changes have a limited effect "
                "on the predicted attrition probability."
            )

        # -------------------------------------------------
        # Factor-specific actions
        # -------------------------------------------------

        burnout = safe_float(
            simulated_employee.get(
                "burnout_score"
            )
        )

        engagement = safe_float(
            simulated_employee.get(
                "engagement_score"
            )
        )

        manager_support = safe_float(
            simulated_employee.get(
                "manager_support_score"
            )
        )

        overtime = safe_float(
            simulated_employee.get(
                "overtime_hours_per_week"
            )
        )

        work_life = safe_float(
            simulated_employee.get(
                "work_life_balance_score"
            )
        )

        promotion_gap = safe_float(
            simulated_employee.get(
                "years_since_promotion"
            )
        )

        training = safe_float(
            simulated_employee.get(
                "training_hours"
            )
        )

        # Burnout

        if burnout >= 7:

            recommendations.append(
                "Prioritize workload and wellbeing support "
                "because simulated burnout remains high."
            )

        # Engagement

        if engagement <= 5:

            recommendations.append(
                "Consider an employee engagement review "
                "or structured manager check-in."
            )

        # Manager support

        if manager_support <= 5:

            recommendations.append(
                "Consider increasing manager support and "
                "structured one-to-one conversations."
            )

        # Overtime

        if overtime >= 15:

            recommendations.append(
                "Review workload allocation because simulated "
                "overtime remains elevated."
            )

        # Work-life balance

        if work_life <= 5:

            recommendations.append(
                "Consider work-life balance measures such as "
                "schedule or workload adjustments."
            )

        # Promotion

        if promotion_gap >= 5:

            recommendations.append(
                "Review career growth and promotion opportunities."
            )

        # Training

        if training < 20:

            recommendations.append(
                "Consider targeted skill-development or training."
            )

        # Performance

        if performance_change > 0:

            recommendations.append(
                "The simulated scenario improves the model's "
                "predicted performance rating."
            )

        elif performance_change < 0:

            recommendations.append(
                "The simulated scenario lowers the model's "
                "predicted performance rating; review the "
                "changed factors."
            )

        # -------------------------------------------------
        # Response
        # -------------------------------------------------

        return jsonify({

            "success": True,

            "employee_id":
                employee_id,

            "current": {

                "attrition_probability":
                    current[
                        "attrition_probability"
                    ],

                "risk_level":
                    current[
                        "risk_level"
                    ],

                "performance_rating":
                    current[
                        "performance_rating"
                    ],

                "performance_label":
                    current[
                        "performance_label"
                    ],

                "performance_confidence":
                    current[
                        "performance_confidence"
                    ]

            },

            "simulated": {

                "attrition_probability":
                    simulated[
                        "attrition_probability"
                    ],

                "risk_level":
                    simulated[
                        "risk_level"
                    ],

                "performance_rating":
                    simulated[
                        "performance_rating"
                    ],

                "performance_label":
                    simulated[
                        "performance_label"
                    ],

                "performance_confidence":
                    simulated[
                        "performance_confidence"
                    ]

            },

            "risk_change":
                risk_change,

            "performance_change":
                performance_change,

            "recommendation":
                recommendations,

            "scenario": {
                field:
                    simulated_employee.get(
                        field
                    )
                for field in simulation_fields
            }

        })

    except Exception as error:
        logger.exception("Simulation error: %s", error)
        return jsonify({"success": False, "error": str(error)}), 500



# =========================================================
# DASHBOARD API
# =========================================================

_dashboard_model = None
_dashboard_preprocessor = None
_dashboard_cache = None
_dashboard_cache_time = None


def load_dashboard_model():
    """Load dashboard prediction artifacts once and reuse them."""

    global _dashboard_model
    global _dashboard_preprocessor

    if _dashboard_model is None:
        _dashboard_model = tf.keras.models.load_model(
            ATTRITION_MODEL_PATH,
            compile=False
        )

    if _dashboard_preprocessor is None:
        _dashboard_preprocessor = joblib.load(
            ATTRITION_PREPROCESSOR_PATH
        )

    return _dashboard_model, _dashboard_preprocessor


@app.route(
    "/api/dashboard",
    methods=["GET"]
)
def api_dashboard():
    """Return dynamic workforce KPIs and DNN risk summaries."""

    global _dashboard_cache
    global _dashboard_cache_time

    try:
        from datetime import datetime, timedelta

        now = datetime.now()

        # Cache expensive 5,000-employee predictions for 10 minutes.
        if (
            _dashboard_cache is not None
            and _dashboard_cache_time is not None
            and now - _dashboard_cache_time < timedelta(minutes=10)
        ):
            return jsonify(_dashboard_cache)

        employees = [
            clean_employee(row)
            for row in load_employees()
        ]

        if not employees:
            return jsonify({
                "success": False,
                "error": "No employee records available."
            }), 404

        total_employees = len(employees)



        # -------------------------------------------------
        # Historical statistics
        # -------------------------------------------------

        performance_distribution = {
            "2": 0,
            "3": 0,
            "4": 0,
            "5": 0
        }

        performance_values = []
        historical_attrition_count = 0

        for employee in employees:
            try:
                rating = int(float(employee.get("performance_rating")))
                if str(rating) in performance_distribution:
                    performance_distribution[str(rating)] += 1
                performance_values.append(float(rating))
            except (TypeError, ValueError):
                pass

            attrition = str(
                employee.get("attrition", "")
            ).strip().lower()

            if attrition in {"yes", "1", "true"}:
                historical_attrition_count += 1

        average_performance = (
            sum(performance_values) / len(performance_values)
            if performance_values else 0.0
        )

        historical_attrition_rate = (
            historical_attrition_count / total_employees
            if total_employees else 0.0
        )

        # -------------------------------------------------
        # Prepare model input
        # -------------------------------------------------

        valid_employees = []
        model_records = []

        for employee in employees:
            record = {}
            valid = True

            for column in MODEL_INPUT_COLUMNS:
                if column not in employee:
                    valid = False
                    break
                record[column] = employee[column]

            if valid:
                valid_employees.append(employee)
                model_records.append(record)

        if not model_records:
            raise ValueError(
                "No valid employee records available for prediction."
            )

        model, preprocessor = load_dashboard_model()

        model_df = pd.DataFrame(
            model_records,
            columns=MODEL_INPUT_COLUMNS
        )

        transformed = preprocessor.transform(model_df)
        transformed = np.asarray(
            transformed,
            dtype=np.float32
        )

        probabilities = model.predict(
            transformed,
            verbose=0,
            batch_size=256
        ).reshape(-1)

        # -------------------------------------------------
        # Risk distribution and department risk
        # -------------------------------------------------

        high_count = 0
        medium_count = 0
        low_count = 0
        risk_sum = 0.0

        department_data = {}

        for employee, probability in zip(
            valid_employees,
            probabilities
        ):
            probability = float(probability)
            risk_sum += probability

            if probability >= 0.64:
                high_count += 1
            elif probability >= 0.40:
                medium_count += 1
            else:
                low_count += 1

            department = str(
                employee.get(
                    "department",
                    "Unknown"
                )
            ).strip() or "Unknown"

            if department not in department_data:
                department_data[department] = {
                    "total": 0,
                    "risk_sum": 0.0
                }

            department_data[department]["total"] += 1
            department_data[department]["risk_sum"] += probability

        predicted_count = len(probabilities)

        average_predicted_risk = (
            risk_sum / predicted_count
            if predicted_count else 0.0
        )

        high_percentage = (
            high_count / predicted_count * 100
            if predicted_count else 0.0
        )

        medium_percentage = (
            medium_count / predicted_count * 100
            if predicted_count else 0.0
        )

        low_percentage = (
            low_count / predicted_count * 100
            if predicted_count else 0.0
        )

        department_risk = []

        for department, info in department_data.items():
            average_risk = (
                info["risk_sum"] / info["total"]
                if info["total"] else 0.0
            )

            department_risk.append({
                "department": department,
                "employee_count": info["total"],
                "average_risk": round(average_risk, 6)
            })

        department_risk.sort(
            key=lambda item: item["average_risk"],
            reverse=True
        )

        result = {
            "success": True,
            "generated_at": now.isoformat(),
            "kpis": {
                "total_employees": total_employees,
                "average_predicted_risk": average_predicted_risk,
                "average_performance": average_performance,
                "high_risk_count": high_count,
                "high_risk_percentage": (
                    high_count / predicted_count
                    if predicted_count else 0.0
                ),
                "historical_attrition_rate": historical_attrition_rate
            },
            "risk_distribution": {
                "high": high_percentage,
                "medium": medium_percentage,
                "low": low_percentage
            },
            "performance_distribution": performance_distribution,
            "department_risk": department_risk
        }

        _dashboard_cache = result
        _dashboard_cache_time = now

        return jsonify(result)

    except Exception as error:
        logger.exception("Dashboard API error: %s", error)
        return jsonify({"success": False, "error": str(error)}), 500


# =========================================================
# MODEL EVIDENCE API
# =========================================================

@app.route(
    "/api/model-evidence",
    methods=["GET"]
)
def api_model_evidence():
    """
    Return evaluation evidence for the attrition and performance
    models used by the HR Insight AI system.

    Metrics below are the recorded test-set evaluation results from
    the project's model training/evaluation runs. Where available,
    SHAP global importance is read from the saved CSV artifact.
    """

    try:

        # -------------------------------------------------
        # ATTRITION MODEL RESULTS
        # -------------------------------------------------

        attrition_models = [

            {
                "name": "Logistic Regression",
                "accuracy": 0.7260,
                "precision": 0.3631,
                "recall": 0.7039,
                "f1": 0.4791,
                "roc_auc": 0.8071
            },

            {
                "name": "Random Forest",
                "accuracy": 0.8240,
                "precision": 0.5118,
                "recall": 0.3631,
                "f1": 0.4248,
                "roc_auc": 0.7925
            },

            {
                "name": "Deep Neural Network",
                "accuracy": 0.6730,
                "precision": 0.3263,
                "recall": 0.7765,
                "f1": 0.4595,
                "roc_auc": 0.7890
            }
        ]

        attrition_confusion_matrix = [
            [534, 287],
            [40, 139]
        ]

        attrition_architecture = [
            {"layer": "Input", "details": "68 processed features"},
            {"layer": "Dense 1", "details": "128 neurons + ReLU"},
            {"layer": "BatchNorm / Dropout", "details": "Normalization + 30% dropout"},
            {"layer": "Dense 2", "details": "64 neurons + ReLU"},
            {"layer": "BatchNorm / Dropout", "details": "Normalization + 30% dropout"},
            {"layer": "Dense 3", "details": "32 neurons + ReLU + 20% dropout"},
            {"layer": "Output", "details": "1 neuron + Sigmoid"}
        ]

        # -------------------------------------------------
        # PERFORMANCE MODEL RESULTS
        # -------------------------------------------------

        performance_models = [

            {
                "name": "Deep Neural Network",
                "accuracy": 0.4200,
                "macro_precision": 0.3281,
                "macro_recall": 0.3842,
                "macro_f1": 0.3275,
                "weighted_f1": 0.4392
            },

            {
                "name": "Logistic Regression",
                "accuracy": 0.3620,
                "macro_precision": 0.3529,
                "macro_recall": 0.4904,
                "macro_f1": 0.3163,
                "weighted_f1": 0.4026
            },

            {
                "name": "Random Forest",
                "accuracy": 0.5530,
                "macro_precision": 0.3039,
                "macro_recall": 0.3076,
                "macro_f1": 0.2958,
                "weighted_f1": 0.5270
            }
        ]

        performance_confusion_matrix = [
            [9, 19, 4, 0],
            [41, 204, 99, 46],
            [28, 185, 181, 115],
            [0, 8, 35, 26]
        ]

        # -------------------------------------------------
        # SHAP GLOBAL FEATURE IMPORTANCE
        # -------------------------------------------------

        shap_features = []

        shap_candidates = [
            PROJECT_DIR
            / "results"
            / "attrition_shap_feature_importance.csv",

            PROJECT_DIR
            / "results"
            / "attrition_shap_importance.csv",

            PROJECT_DIR
            / "attrition_shap_feature_importance.csv"
        ]

        for shap_path in shap_candidates:

            if not shap_path.exists():
                continue

            try:

                shap_df = pd.read_csv(
                    shap_path
                )

                columns = [
                    str(column).strip()
                    for column in shap_df.columns
                ]

                feature_column = None
                importance_column = None

                # Find feature column
                for column in columns:

                    lowered = column.lower()

                    if lowered in {
                        "feature",
                        "feature_name",
                        "features"
                    }:
                        feature_column = column
                        break

                # Find importance column
                for column in columns:

                    lowered = column.lower()

                    if (
                        "importance" in lowered
                        or "mean_abs_shap" in lowered
                        or "mean_abs" in lowered
                    ):
                        importance_column = column
                        break

                if (
                    feature_column is None
                    or importance_column is None
                ):
                    continue

                for _, row in shap_df.iterrows():

                    try:

                        feature = str(
                            row[feature_column]
                        )

                        importance = float(
                            row[importance_column]
                        )

                    except (
                        TypeError,
                        ValueError
                    ):
                        continue

                    if not feature or not np.isfinite(
                        importance
                    ):
                        continue

                    shap_features.append({
                        "feature": feature,
                        "importance": round(
                            abs(importance),
                            6
                        )
                    })

                if shap_features:
                    break

            except Exception:
                shap_features = []

        # -------------------------------------------------
        # SHAP global feature importance
        # -------------------------------------------------

        # Do not use synthetic fallback values.
        # When no saved SHAP artifact is available, the API returns
        # an empty list so the UI can report that honestly.

        shap_features = sorted(
            shap_features,
            key=lambda item:
                item["importance"],
            reverse=True
        )[:10]

        return jsonify({

            "success": True,

            "attrition": {
                "models": attrition_models,
                "confusion_matrix":
                    attrition_confusion_matrix,
                "architecture":
                    attrition_architecture
            },

            "performance": {
                "models": performance_models,
                "confusion_matrix":
                    performance_confusion_matrix
            },

            "shap": shap_features,

            "notes": [
                "Attrition evaluation uses a held-out test set of 1,000 records.",
                "The deployed attrition DNN is paired with a 0.64 decision threshold in the current assessment workflow.",
                "Performance prediction is a four-class problem with ratings 2, 3, 4 and 5; class imbalance affects macro metrics.",
                "The DNN is retained for the performance workflow because it has the highest recorded macro F1 among the three tested models.",
                "SHAP explanations describe model contributions and are not causal conclusions."
            ]
        })

    except Exception as error:

        print(
            "Model evidence error:",
            error
        )

        return jsonify({

            "success": False,

            "error": str(error)

        }), 500



# =========================================================
# PHASE 2 — BUSINESS KPI API
# =========================================================

@app.route(
    "/api/employees/<employee_id>/business-kpi",
    methods=["POST"]
)
def api_employee_business_kpi(employee_id):
    """
    Employee-level business KPI calculation.

    Runs attrition + performance prediction and converts the
    model output into financial metrics:
    - Expected replacement cost (probability-weighted)
    - Potential intervention saving
    - Disengagement cost estimate
    - Net risk exposure

    All figures are in INR based on SHRM + Gallup benchmarks.
    """
    try:
        employee = find_employee(employee_id)

        if employee is None:
            return jsonify({"success": False, "error": "Employee not found"}), 404

        prediction = predict_employee(employee)
        kpis       = calculate_employee_kpis(employee, prediction)

        logger.info(
            "Business KPI: employee=%s risk=%s exposure=₹%.0f",
            employee_id,
            kpis["risk_level"],
            kpis["net_risk_exposure"],
        )

        return jsonify({
            "success":     True,
            "employee_id": employee_id,
            "prediction":  prediction,
            "business_kpi": kpis,
        })

    except Exception as error:
        logger.exception("Business KPI error for %s: %s", employee_id, error)
        return jsonify({"success": False, "error": str(error)}), 500


@app.route(
    "/api/workforce/business-kpi",
    methods=["GET"]
)
def api_workforce_business_kpi():
    """
    Workforce-level aggregate business KPI.

    Uses cached dashboard predictions (if available) to calculate
    aggregate financial risk exposure for the entire workforce.

    Returns:
    - Total expected attrition cost
    - Potential intervention savings
    - Estimated disengagement cost
    - Risk-tier breakdown
    """
    try:
        employees_raw = load_employees()
        employees     = [clean_employee(e) for e in employees_raw]

        # Reuse cached dashboard predictions if fresh
        cached_probs  = None
        if _dashboard_cache is not None:
            logger.debug("Using cached dashboard predictions for workforce KPI")

        kpis = calculate_workforce_kpis(employees)

        logger.info(
            "Workforce KPI: total=%d exposure=₹%.0f saving=₹%.0f",
            kpis["total_employees"],
            kpis["total_risk_exposure"],
            kpis["potential_intervention_saving"],
        )

        return jsonify({
            "success":      True,
            "workforce_kpi": kpis,
            "generated_at": datetime.utcnow().isoformat() + "Z",
        })

    except Exception as error:
        logger.exception("Workforce KPI error: %s", error)
        return jsonify({"success": False, "error": str(error)}), 500


# =========================================================
# PHASE 2 — MODEL REGISTRY API
# =========================================================

@app.route(
    "/api/models",
    methods=["GET"]
)
def api_models():
    """
    Return the model registry — version, training metadata,
    and last recorded evaluation metrics for each model.
    """
    try:
        summary = model_registry.summary()
        return jsonify({
            "success": True,
            "models":  summary,
        })
    except Exception as error:
        logger.exception("Model registry error: %s", error)
        return jsonify({"success": False, "error": str(error)}), 500


@app.route(
    "/api/models/<task>",
    methods=["GET"]
)
def api_model_detail(task):
    """
    Return full metadata for a specific model task.

    Args:
        task: ``attrition`` or ``performance``
    """
    try:
        info = model_registry.get_model_info(task)
        if info is None:
            return jsonify({
                "success": False,
                "error":   f"Unknown model task '{task}'. "
                           "Valid values: attrition, performance.",
            }), 404

        return jsonify({
            "success": True,
            "task":    task,
            "model":   info,
        })
    except Exception as error:
        logger.exception("Model detail error: %s", error)
        return jsonify({"success": False, "error": str(error)}), 500


# =========================================================
# PHASE 2 — CSV REPORT EXPORT
# =========================================================

@app.route(
    "/api/export/risk-report",
    methods=["GET"]
)
def api_export_risk_report():
    """
    Download a CSV risk report for all employees.

    Columns:
    - employee_id, department, job_role, monthly_income
    - attrition_probability, risk_level
    - expected_replacement_cost, intervention_saving
    - performance_rating, performance_label

    Query params:
    - risk_filter: ``high`` | ``medium`` | ``low`` | ``all`` (default: all)
    - department:  filter to a specific department
    """
    try:
        risk_filter = request.args.get("risk_filter", "all").strip().lower()
        dept_filter = request.args.get("department",  "").strip().lower()

        logger.info(
            "CSV export requested — risk_filter=%s department=%s",
            risk_filter, dept_filter or "all",
        )

        employees_raw = load_employees()
        employees     = [clean_employee(e) for e in employees_raw]

        # Apply department filter
        if dept_filter:
            employees = [
                e for e in employees
                if str(e.get("department", "")).strip().lower() == dept_filter
            ]

        output   = io.StringIO()
        fieldnames = [
            "employee_id", "department", "job_role",
            "monthly_income", "age",
            "attrition_probability", "risk_level",
            "expected_replacement_cost_inr",
            "intervention_saving_inr",
            "net_risk_exposure_inr",
            "performance_rating", "performance_label",
        ]
        writer = csv.DictWriter(
            output,
            fieldnames=fieldnames,
            extrasaction="ignore"
        )
        writer.writeheader()

        exported      = 0
        skipped_risk  = 0

        for employee in employees:
            emp_id = str(employee.get("employee_id", ""))

            try:
                prediction = predict_employee(employee)
                kpis       = calculate_employee_kpis(employee, prediction)
            except Exception as err:
                logger.warning("Export: skipping %s — %s", emp_id, err)
                continue

            risk_level = kpis["risk_level"].lower()

            if risk_filter != "all" and risk_level != risk_filter:
                skipped_risk += 1
                continue

            attrition_info   = prediction.get("attrition", {})
            performance_info = prediction.get("performance", {})

            writer.writerow({
                "employee_id":                   emp_id,
                "department":                    employee.get("department", ""),
                "job_role":                      employee.get("job_role", ""),
                "monthly_income":                employee.get("monthly_income", ""),
                "age":                           employee.get("age", ""),
                "attrition_probability":         round(
                    float(attrition_info.get("probability", 0) or 0), 4
                ),
                "risk_level":                    kpis["risk_level"],
                "expected_replacement_cost_inr": kpis["expected_replacement_cost"],
                "intervention_saving_inr":       kpis["intervention_saving"],
                "net_risk_exposure_inr":         kpis["net_risk_exposure"],
                "performance_rating":            kpis["performance_rating"],
                "performance_label":             kpis["performance_label"],
            })
            exported += 1

        csv_content = output.getvalue()
        output.close()

        filename   = (
            f"hr_risk_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        )

        logger.info(
            "CSV export complete — exported=%d skipped_by_filter=%d filename=%s",
            exported, skipped_risk, filename,
        )

        return Response(
            csv_content,
            mimetype="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Records-Exported":  str(exported),
            },
        )

    except Exception as error:
        logger.exception("CSV export error: %s", error)
        return jsonify({"success": False, "error": str(error)}), 500


# =========================================================
# PHASE 2 — CACHE MANAGEMENT
# =========================================================

@app.route(
    "/api/cache/invalidate",
    methods=["POST"]
)
def api_cache_invalidate():
    """
    Manually invalidate the dashboard cache.

    Useful after bulk employee data updates to force a fresh
    prediction run on the next dashboard request.
    """
    global _dashboard_cache, _dashboard_cache_time

    _dashboard_cache      = None
    _dashboard_cache_time = None

    logger.info("Dashboard cache manually invalidated")

    return jsonify({
        "success": True,
        "message": "Dashboard cache cleared. "
                   "Next dashboard request will recompute predictions.",
    })


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({

        "success": False,

        "error":
            "Requested page or API endpoint was not found"

    }), 404


@app.errorhandler(500)
def internal_server_error(error):

    return jsonify({

        "success": False,

        "error":
            "Internal server error"

    }), 500


# =========================================================
# START FLASK
# =========================================================

if __name__ == "__main__":

    from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG

    logger.info(
        "Starting HR AI Decision Support System — "
        "host=%s port=%d debug=%s",
        FLASK_HOST, FLASK_PORT, FLASK_DEBUG,
    )

    app.run(
        host=FLASK_HOST,
        port=FLASK_PORT,
        debug=FLASK_DEBUG,
    )
