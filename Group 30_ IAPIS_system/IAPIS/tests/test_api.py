"""Tests for the FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient


def _can_import_api():
    try:
        from api.main import app
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _can_import_api(), reason="API module not importable")
def test_health_endpoint():
    """GET /health should return 200 with status ok."""
    from api.main import app
    client = TestClient(app)
    
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.skipif(not _can_import_api(), reason="API module not importable")
def test_search_endpoint():
    """POST /search should return results."""
    from api.main import app
    client = TestClient(app)
    
    response = client.post("/search", json={
        "query": "overheating motor",
        "top_k": 3,
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data


@pytest.mark.skipif(not _can_import_api(), reason="API module not importable")
def test_analyze_endpoint():
    """POST /analyze should return results, risk_summary, and recommendation."""
    from api.main import app
    client = TestClient(app)
    
    response = client.post("/analyze", json={
        "query": "overheating motor incidents",
        "top_k": 3,
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "risk_summary" in data
    assert "recommendation" in data
    assert data["recommendation"] != ""


def test_recommendation_fallback():
    """Recommendation should work without any API keys (fallback template)."""
    from recommend.llm_client import generate_recommendation
    
    test_evidence = [
        {
            "id": "RPT-0001",
            "title": "Motor Overheating",
            "text": "The motor overheated causing smoke.",
            "equipment": "induction motor",
            "hazard_type": "overheating",
            "severity": "high",
            "location": "Building 3",
            "metadata": {},
        }
    ]
    
    test_risk_flags = {
        "equipment_flags": {},
        "recurrence_pattern": "Test pattern",
    }
    
    # This should work even without API keys
    result = generate_recommendation(
        query="overheating motor",
        evidence=test_evidence,
        risk_flags=test_risk_flags,
    )
    
    assert result["success"] is True
    assert result["recommendation"] != ""
    assert len(result["recommendation"]) > 50
