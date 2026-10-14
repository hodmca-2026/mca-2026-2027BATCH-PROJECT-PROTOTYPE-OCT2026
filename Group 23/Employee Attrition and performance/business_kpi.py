# ==============================================================
# business_kpi.py
#
# Business KPI Calculator — Cost of Attrition & Workforce ROI
#
# Industry standard: HR analytics must translate ML predictions
# into business-language numbers that executives can act on.
#
# References:
#   - SHRM: cost to replace an employee ≈ 50–200% of annual salary
#   - Gallup: cost of a disengaged employee ≈ 34% of their salary
#   - MIT/Deloitte: early retention saves 60–80% of replacement cost
# ==============================================================

from typing import Any, Dict, List, Optional

from logger import get_logger

logger = get_logger(__name__)


# ==============================================================
# CONSTANTS
# ==============================================================

# Replacement cost as a fraction of annual salary (SHRM midpoint)
REPLACEMENT_COST_RATIO = 0.75

# Disengagement cost as a fraction of annual salary (Gallup)
DISENGAGEMENT_COST_RATIO = 0.34

# Percentage of replacement cost saved by early intervention
EARLY_INTERVENTION_SAVINGS_RATIO = 0.65

# Working months per year (for annualisation)
MONTHS_PER_YEAR = 12

# Risk tier thresholds (must match config.py)
HIGH_RISK_THRESHOLD   = 0.64
MEDIUM_RISK_THRESHOLD = 0.40

# Performance labels
PERFORMANCE_LABELS = {
    2: "Needs Improvement",
    3: "Average",
    4: "Good",
    5: "Excellent",
}


# ==============================================================
# SINGLE EMPLOYEE KPIs
# ==============================================================

def calculate_employee_kpis(
    employee:   Dict[str, Any],
    prediction: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Calculate business KPIs for a single employee.

    Args:
        employee:   Employee data dict (must contain ``monthly_income``).
        prediction: Output from ``predict_employee()``; must contain
                    ``attrition`` and ``performance`` sub-dicts.

    Returns:
        Dict with attrition cost, intervention saving, and
        disengagement cost estimates in currency units.
    """

    monthly_income = float(employee.get("monthly_income", 0) or 0)
    annual_salary  = monthly_income * MONTHS_PER_YEAR

    attrition_info   = prediction.get("attrition", {})
    performance_info = prediction.get("performance", {})

    probability = float(
        attrition_info.get("probability", 0)
        or attrition_info.get("attrition_probability", 0)
        or 0
    )
    risk_level = str(
        attrition_info.get("risk_level", "")
        or attrition_info.get("risk", "LOW")
    ).upper()

    perf_rating = int(
        performance_info.get("predicted_rating", 0)
        or performance_info.get("rating", 3)
        or 3
    )

    # ----------------------------------------------------------
    # 1. Expected replacement cost (probability-weighted)
    # ----------------------------------------------------------
    full_replacement_cost = annual_salary * REPLACEMENT_COST_RATIO
    expected_replacement_cost = full_replacement_cost * probability

    # ----------------------------------------------------------
    # 2. Potential saving from early intervention
    # ----------------------------------------------------------
    if risk_level in ("HIGH", "MEDIUM") and probability > 0:
        intervention_saving = (
            full_replacement_cost * EARLY_INTERVENTION_SAVINGS_RATIO
        )
    else:
        intervention_saving = 0.0

    # ----------------------------------------------------------
    # 3. Disengagement cost (for below-average performers)
    # ----------------------------------------------------------
    disengagement_cost = 0.0

    engagement = float(employee.get("engagement_score", 10) or 10)
    if engagement <= 5 or perf_rating <= 3:
        disengagement_cost = annual_salary * DISENGAGEMENT_COST_RATIO

    # ----------------------------------------------------------
    # 4. Net risk exposure
    # ----------------------------------------------------------
    net_risk_exposure = expected_replacement_cost + disengagement_cost

    return {
        "annual_salary":              round(annual_salary, 2),
        "full_replacement_cost":      round(full_replacement_cost, 2),
        "expected_replacement_cost":  round(expected_replacement_cost, 2),
        "intervention_saving":        round(intervention_saving, 2),
        "disengagement_cost":         round(disengagement_cost, 2),
        "net_risk_exposure":          round(net_risk_exposure, 2),
        "risk_level":                 risk_level,
        "attrition_probability":      round(probability, 4),
        "performance_rating":         perf_rating,
        "performance_label": PERFORMANCE_LABELS.get(perf_rating, "Unknown"),
        "currency":                   "INR",
        "assumptions": {
            "replacement_cost_ratio":            REPLACEMENT_COST_RATIO,
            "disengagement_cost_ratio":          DISENGAGEMENT_COST_RATIO,
            "early_intervention_savings_ratio":  EARLY_INTERVENTION_SAVINGS_RATIO,
            "source": "SHRM + Gallup benchmarks",
        },
    }


# ==============================================================
# PORTFOLIO / WORKFORCE KPIs
# ==============================================================

def calculate_workforce_kpis(
    employees:   List[Dict[str, Any]],
    predictions: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Calculate aggregate business KPIs for the workforce.

    If ``predictions`` is not provided, uses the ``attrition``
    column from the employee records (historical data only).

    Args:
        employees:   List of employee dicts.
        predictions: Optional list of prediction dicts, one per employee.

    Returns:
        Dict with workforce-level attrition risk cost,
        disengagement cost, and intervention savings.
    """

    total             = len(employees)
    total_salary      = 0.0
    total_replacement = 0.0
    total_saving      = 0.0
    total_disengagement = 0.0
    high_risk_count   = 0
    medium_risk_count = 0
    low_risk_count    = 0

    if predictions is None:
        predictions = [{}] * total

    for employee, prediction in zip(employees, predictions):
        monthly_income = float(employee.get("monthly_income", 0) or 0)
        annual_salary  = monthly_income * MONTHS_PER_YEAR
        total_salary  += annual_salary

        attrition_info = prediction.get("attrition", {})
        probability = float(
            attrition_info.get("probability", 0)
            or attrition_info.get("attrition_probability", 0)
            or 0
        )
        risk_level = str(
            attrition_info.get("risk_level", "")
            or attrition_info.get("risk", "LOW")
        ).upper()

        if not risk_level:
            if probability >= HIGH_RISK_THRESHOLD:
                risk_level = "HIGH"
            elif probability >= MEDIUM_RISK_THRESHOLD:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"

        if risk_level == "HIGH":
            high_risk_count += 1
        elif risk_level == "MEDIUM":
            medium_risk_count += 1
        else:
            low_risk_count += 1

        replacement_cost = annual_salary * REPLACEMENT_COST_RATIO
        expected_cost    = replacement_cost * probability
        total_replacement += expected_cost

        if risk_level in ("HIGH", "MEDIUM") and probability > 0:
            total_saving += replacement_cost * EARLY_INTERVENTION_SAVINGS_RATIO

        engagement = float(employee.get("engagement_score", 10) or 10)
        if engagement <= 5:
            total_disengagement += annual_salary * DISENGAGEMENT_COST_RATIO

    total_exposure = total_replacement + total_disengagement

    return {
        "total_employees":              total,
        "total_annual_payroll":         round(total_salary, 2),
        "expected_attrition_cost":      round(total_replacement, 2),
        "potential_intervention_saving": round(total_saving, 2),
        "estimated_disengagement_cost": round(total_disengagement, 2),
        "total_risk_exposure":          round(total_exposure, 2),
        "risk_breakdown": {
            "high":   high_risk_count,
            "medium": medium_risk_count,
            "low":    low_risk_count,
        },
        "currency": "INR",
        "assumptions": {
            "replacement_cost_ratio":           REPLACEMENT_COST_RATIO,
            "disengagement_cost_ratio":         DISENGAGEMENT_COST_RATIO,
            "early_intervention_savings_ratio": EARLY_INTERVENTION_SAVINGS_RATIO,
            "source": "SHRM + Gallup benchmarks",
        },
    }
