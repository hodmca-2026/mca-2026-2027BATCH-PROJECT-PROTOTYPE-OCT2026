# ============================================================
# tests/test_business_kpi.py
#
# Unit tests for the business KPI calculator.
# ============================================================

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from business_kpi import (
    calculate_employee_kpis,
    calculate_workforce_kpis,
    REPLACEMENT_COST_RATIO,
    DISENGAGEMENT_COST_RATIO,
    MONTHS_PER_YEAR,
)


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def high_risk_employee():
    return {
        "employee_id":        "EMP001",
        "monthly_income":     80000,
        "department":         "Engineering",
        "engagement_score":   3,
        "performance_rating": 3,
    }


@pytest.fixture
def high_risk_prediction():
    return {
        "attrition": {
            "probability": 0.80,
            "risk_level":  "HIGH",
        },
        "performance": {
            "predicted_rating": 3,
            "rating":           3,
        },
    }


@pytest.fixture
def low_risk_employee():
    return {
        "employee_id":        "EMP002",
        "monthly_income":     60000,
        "department":         "Finance",
        "engagement_score":   8,
        "performance_rating": 4,
    }


@pytest.fixture
def low_risk_prediction():
    return {
        "attrition": {
            "probability": 0.10,
            "risk_level":  "LOW",
        },
        "performance": {
            "predicted_rating": 4,
            "rating":           4,
        },
    }


# ============================================================
# TEST — EMPLOYEE KPIs
# ============================================================

class TestEmployeeKPIs:

    def test_annual_salary_correct(self, high_risk_employee, high_risk_prediction):
        kpis = calculate_employee_kpis(high_risk_employee, high_risk_prediction)
        assert kpis["annual_salary"] == 80000 * MONTHS_PER_YEAR

    def test_replacement_cost_positive(self, high_risk_employee, high_risk_prediction):
        kpis = calculate_employee_kpis(high_risk_employee, high_risk_prediction)
        assert kpis["expected_replacement_cost"] > 0

    def test_high_risk_has_intervention_saving(
        self, high_risk_employee, high_risk_prediction
    ):
        kpis = calculate_employee_kpis(high_risk_employee, high_risk_prediction)
        assert kpis["intervention_saving"] > 0

    def test_low_risk_has_no_intervention_saving(
        self, low_risk_employee, low_risk_prediction
    ):
        kpis = calculate_employee_kpis(low_risk_employee, low_risk_prediction)
        assert kpis["intervention_saving"] == 0.0

    def test_disengaged_employee_has_disengagement_cost(
        self, high_risk_employee, high_risk_prediction
    ):
        # high_risk_employee has engagement_score=3 (below threshold 5)
        kpis = calculate_employee_kpis(high_risk_employee, high_risk_prediction)
        assert kpis["disengagement_cost"] > 0

    def test_engaged_employee_has_no_disengagement_cost(
        self, low_risk_employee, low_risk_prediction
    ):
        kpis = calculate_employee_kpis(low_risk_employee, low_risk_prediction)
        assert kpis["disengagement_cost"] == 0.0

    def test_net_exposure_sum(self, high_risk_employee, high_risk_prediction):
        kpis = calculate_employee_kpis(high_risk_employee, high_risk_prediction)
        expected = kpis["expected_replacement_cost"] + kpis["disengagement_cost"]
        assert abs(kpis["net_risk_exposure"] - expected) < 0.01

    def test_zero_income_is_safe(self):
        emp   = {"monthly_income": 0, "engagement_score": 5}
        pred  = {"attrition": {"probability": 0.5}, "performance": {"rating": 3}}
        kpis  = calculate_employee_kpis(emp, pred)
        assert kpis["annual_salary"] == 0.0

    def test_returns_currency_label(self, high_risk_employee, high_risk_prediction):
        kpis = calculate_employee_kpis(high_risk_employee, high_risk_prediction)
        assert kpis["currency"] == "INR"

    def test_assumptions_present(self, high_risk_employee, high_risk_prediction):
        kpis = calculate_employee_kpis(high_risk_employee, high_risk_prediction)
        assert "assumptions" in kpis
        assert "source" in kpis["assumptions"]


# ============================================================
# TEST — WORKFORCE KPIs
# ============================================================

class TestWorkforceKPIs:

    def test_total_employees_count(self, high_risk_employee, low_risk_employee):
        kpis = calculate_workforce_kpis(
            [high_risk_employee, low_risk_employee]
        )
        assert kpis["total_employees"] == 2

    def test_risk_breakdown_sums_to_total(
        self,
        high_risk_employee,
        low_risk_employee,
        high_risk_prediction,
        low_risk_prediction,
    ):
        kpis = calculate_workforce_kpis(
            [high_risk_employee, low_risk_employee],
            [high_risk_prediction, low_risk_prediction],
        )
        breakdown = kpis["risk_breakdown"]
        total     = breakdown["high"] + breakdown["medium"] + breakdown["low"]
        assert total == 2

    def test_empty_workforce(self):
        kpis = calculate_workforce_kpis([])
        assert kpis["total_employees"] == 0
        assert kpis["total_risk_exposure"] == 0.0

    def test_total_payroll_is_sum(self, high_risk_employee, low_risk_employee):
        kpis = calculate_workforce_kpis(
            [high_risk_employee, low_risk_employee]
        )
        expected_payroll = (
            (80000 + 60000) * MONTHS_PER_YEAR
        )
        assert abs(kpis["total_annual_payroll"] - expected_payroll) < 1.0
