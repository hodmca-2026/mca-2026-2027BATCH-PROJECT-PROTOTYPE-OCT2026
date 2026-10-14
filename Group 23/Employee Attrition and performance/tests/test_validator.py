# ============================================================
# tests/test_validator.py
#
# Unit tests for the input validation layer.
# Run with: pytest tests/ -v
# ============================================================

import pytest
import sys
from pathlib import Path

# Make project root importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validator import validate_employee, ValidationResult


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def valid_employee():
    """A complete, valid employee record."""
    return {
        "age": 30,
        "gender": "Male",
        "marital_status": "Single",
        "education_level": "Bachelors",
        "department": "Engineering",
        "job_role": "Software Engineer",
        "job_level": 2,
        "monthly_income": 60000,
        "stock_option_level": 1,
        "salary_hike_pct": 12.5,
        "years_at_company": 4,
        "total_working_years": 7,
        "years_since_promotion": 2,
        "num_prior_companies": 2,
        "work_mode": "Hybrid",
        "commute_minutes": 30,
        "overtime_hours_per_week": 5,
        "business_travel_days_per_year": 10,
        "training_hours": 20,
        "manager_support_score": 8,
        "burnout_score": 3,
        "engagement_score": 7,
        "work_life_balance_score": 8,
        "performance_rating": 4,
        "last_review_score": 8.5,
        "uses_ai_tools_at_work": True,
        "perceived_ai_job_risk": 3,
    }


# ============================================================
# TESTS — VALID INPUT
# ============================================================

class TestValidInput:

    def test_valid_employee_passes(self, valid_employee):
        result = validate_employee(valid_employee)
        assert result.is_valid, result.errors

    def test_returns_validation_result(self, valid_employee):
        result = validate_employee(valid_employee)
        assert isinstance(result, ValidationResult)

    def test_no_errors_for_valid_input(self, valid_employee):
        result = validate_employee(valid_employee)
        assert len(result.errors) == 0

    def test_to_dict_shape(self, valid_employee):
        result = validate_employee(valid_employee)
        d = result.to_dict()
        assert "valid" in d
        assert "errors" in d
        assert "warnings" in d


# ============================================================
# TESTS — MISSING REQUIRED FIELDS
# ============================================================

class TestMissingFields:

    def test_missing_age(self, valid_employee):
        del valid_employee["age"]
        result = validate_employee(valid_employee)
        assert not result.is_valid
        assert any("age" in e for e in result.errors)

    def test_missing_gender(self, valid_employee):
        del valid_employee["gender"]
        result = validate_employee(valid_employee)
        assert not result.is_valid
        assert any("gender" in e for e in result.errors)

    def test_missing_performance_rating(self, valid_employee):
        del valid_employee["performance_rating"]
        result = validate_employee(valid_employee)
        assert not result.is_valid
        assert any("performance_rating" in e for e in result.errors)

    def test_null_required_field(self, valid_employee):
        valid_employee["age"] = None
        result = validate_employee(valid_employee)
        assert not result.is_valid

    def test_empty_string_required_field(self, valid_employee):
        valid_employee["age"] = ""
        result = validate_employee(valid_employee)
        assert not result.is_valid


# ============================================================
# TESTS — NUMERIC RANGE VIOLATIONS
# ============================================================

class TestNumericRanges:

    def test_age_below_minimum(self, valid_employee):
        valid_employee["age"] = 10
        result = validate_employee(valid_employee)
        assert not result.is_valid
        assert any("age" in e for e in result.errors)

    def test_age_above_maximum(self, valid_employee):
        valid_employee["age"] = 200
        result = validate_employee(valid_employee)
        assert not result.is_valid

    def test_performance_rating_zero(self, valid_employee):
        valid_employee["performance_rating"] = 0
        result = validate_employee(valid_employee)
        assert not result.is_valid

    def test_performance_rating_six(self, valid_employee):
        valid_employee["performance_rating"] = 6
        result = validate_employee(valid_employee)
        assert not result.is_valid

    def test_negative_monthly_income(self, valid_employee):
        valid_employee["monthly_income"] = -1000
        result = validate_employee(valid_employee)
        assert not result.is_valid

    def test_non_numeric_field(self, valid_employee):
        valid_employee["age"] = "not-a-number"
        result = validate_employee(valid_employee)
        assert not result.is_valid

    def test_burnout_above_range(self, valid_employee):
        valid_employee["burnout_score"] = 11
        result = validate_employee(valid_employee)
        assert not result.is_valid


# ============================================================
# TESTS — LOGICAL CONSISTENCY
# ============================================================

class TestLogicalConsistency:

    def test_total_working_years_less_than_years_at_company(
        self, valid_employee
    ):
        valid_employee["years_at_company"] = 10
        valid_employee["total_working_years"] = 5
        result = validate_employee(valid_employee)
        # Should produce a warning, not an error
        assert result.is_valid
        assert any(
            "total_working_years" in w for w in result.warnings
        )


# ============================================================
# TESTS — BAD REQUEST BODY
# ============================================================

class TestBadBody:

    def test_non_dict_input(self):
        result = validate_employee("not a dict")
        assert not result.is_valid
        assert len(result.errors) > 0

    def test_empty_dict(self):
        result = validate_employee({})
        assert not result.is_valid

    def test_none_input(self):
        result = validate_employee(None)
        assert not result.is_valid
