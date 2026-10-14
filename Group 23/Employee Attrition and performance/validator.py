# ============================================================
# validator.py
#
# Input validation layer for the prediction API.
# Validates employee data before it reaches the ML models.
#
# Industry pattern: fail fast at the boundary, never inside
# the model inference path.
# ============================================================

from typing import Any, Dict, List, Tuple


# ============================================================
# VALID CATEGORICAL VALUES
# ============================================================

VALID_GENDERS = {"male", "female", "non-binary", "other"}

VALID_MARITAL_STATUSES = {"single", "married", "divorced", "widowed"}

VALID_EDUCATION_LEVELS = {
    "high school",
    "associates",
    "bachelors",
    "masters",
    "phd",
    "doctorate",
}

VALID_WORK_MODES = {"remote", "hybrid", "onsite"}

VALID_DEPARTMENTS = {
    "engineering",
    "sales",
    "operations",
    "customer support",
    "marketing",
    "finance",
    "research & development",
    "human resources",
}

VALID_JOB_ROLES = {
    "engineering manager",
    "software engineer",
    "data engineer",
    "devops engineer",
    "qa engineer",
    "sales manager",
    "sales representative",
    "account executive",
    "operations manager",
    "operations analyst",
    "customer support specialist",
    "customer support manager",
    "marketing specialist",
    "marketing manager",
    "finance manager",
    "financial analyst",
    "accountant",
    "research scientist",
    "hr manager",
    "hr specialist",
    "recruiter",
    "finance specialist",
}


# ============================================================
# NUMERIC FIELD RANGES
# ============================================================

FIELD_RANGES: Dict[str, Tuple[float, float]] = {
    "age":                          (18.0,  80.0),
    "job_level":                    (1.0,   5.0),
    "monthly_income":               (1000.0, 500000.0),
    "stock_option_level":           (0.0,   3.0),
    "salary_hike_pct":              (0.0,   50.0),
    "years_at_company":             (0.0,   50.0),
    "total_working_years":          (0.0,   50.0),
    "years_since_promotion":        (0.0,   30.0),
    "num_prior_companies":          (0.0,   20.0),
    "commute_minutes":              (0.0,   300.0),
    "overtime_hours_per_week":      (0.0,   60.0),
    "business_travel_days_per_year": (0.0,  365.0),
    "training_hours":               (0.0,   500.0),
    "manager_support_score":        (0.0,   10.0),
    "burnout_score":                (0.0,   10.0),
    "engagement_score":             (0.0,   10.0),
    "work_life_balance_score":      (0.0,   10.0),
    "performance_rating":           (1.0,   5.0),
    "last_review_score":            (0.0,   10.0),
    "perceived_ai_job_risk":        (0.0,   10.0),
}

# Required fields (model cannot run without these)
REQUIRED_FIELDS: List[str] = [
    "age",
    "gender",
    "marital_status",
    "education_level",
    "department",
    "job_role",
    "job_level",
    "monthly_income",
    "performance_rating",
]


# ============================================================
# VALIDATION RESULT
# ============================================================

class ValidationResult:
    """Lightweight result object returned by validate_employee."""

    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid":    self.is_valid,
            "errors":   self.errors,
            "warnings": self.warnings,
        }


# ============================================================
# MAIN VALIDATOR
# ============================================================

def validate_employee(data: Dict[str, Any]) -> ValidationResult:
    """
    Validate a single employee record before model inference.

    Checks:
    - Required fields are present and non-null
    - Numeric fields are within expected ranges
    - Categorical fields contain recognised values (soft check)

    Args:
        data: Raw dictionary from API request JSON body.

    Returns:
        :class:`ValidationResult` with ``.is_valid``, ``.errors``,
        and ``.warnings`` attributes.
    """

    result = ValidationResult()

    if not isinstance(data, dict):
        result.add_error("Request body must be a JSON object.")
        return result

    # ----------------------------------------------------------
    # 1. Required fields
    # ----------------------------------------------------------
    for field in REQUIRED_FIELDS:
        if field not in data or data[field] is None or str(data[field]).strip() == "":
            result.add_error(f"Missing required field: '{field}'.")

    # ----------------------------------------------------------
    # 2. Numeric range checks
    # ----------------------------------------------------------
    for field, (low, high) in FIELD_RANGES.items():
        if field not in data:
            continue  # Already flagged as missing if required

        raw = data[field]
        if raw is None or str(raw).strip() == "":
            continue

        try:
            value = float(raw)
        except (TypeError, ValueError):
            result.add_error(
                f"Field '{field}' must be numeric; got '{raw}'."
            )
            continue

        if not (low <= value <= high):
            result.add_error(
                f"Field '{field}' = {value} is outside the expected "
                f"range [{low}, {high}]."
            )

    # ----------------------------------------------------------
    # 3. Soft categorical checks (warnings, not errors)
    # ----------------------------------------------------------
    _soft_check(
        data, "gender", VALID_GENDERS, result,
        "Gender value '{}' is not in the standard set {}."
    )
    _soft_check(
        data, "marital_status", VALID_MARITAL_STATUSES, result,
        "Marital status '{}' is not in the standard set {}."
    )
    _soft_check(
        data, "education_level", VALID_EDUCATION_LEVELS, result,
        "Education level '{}' is not in the standard set {}."
    )
    _soft_check(
        data, "work_mode", VALID_WORK_MODES, result,
        "Work mode '{}' is not in the standard set {}."
    )
    _soft_check(
        data, "department", VALID_DEPARTMENTS, result,
        "Department '{}' is not in the training set {}."
    )

    # ----------------------------------------------------------
    # 4. Logical consistency checks
    # ----------------------------------------------------------
    try:
        years_at = float(data.get("years_at_company", 0) or 0)
        total    = float(data.get("total_working_years", 0) or 0)
        if total < years_at:
            result.add_warning(
                "total_working_years cannot be less than years_at_company."
            )
    except (TypeError, ValueError):
        pass

    return result


# ============================================================
# HELPER
# ============================================================

def _soft_check(
    data: Dict[str, Any],
    field: str,
    valid_set: set,
    result: ValidationResult,
    message_template: str,
) -> None:
    """Issue a warning (not an error) for unrecognised categorical values."""
    raw = data.get(field)
    if raw is None:
        return
    if str(raw).strip().lower() not in valid_set:
        result.add_warning(
            message_template.format(raw, sorted(valid_set))
        )
