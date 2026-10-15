"""
Unit and Integration Tests for Project Similarity Engine and Concise DL Review
==============================================================================
Tests:
- Exact duplicate detection
- Paraphrased duplicate detection across varied vocabularies
- False positive resistance against common template phrases
- Distinct proposal discrimination
- Multi-field comparison (title + description + domain)
- Graceful handling of empty/invalid inputs
- Graceful fallback when semantic models are unavailable
- Decision-oriented concise DL review endpoint
"""

import os
import tempfile
import unittest
from unittest.mock import patch

import app as appmod
import ml_engine
from ml_engine import engine, SimilarityEngine, SemanticEmbeddingService


class TestSimilarityEngine(unittest.TestCase):
    def setUp(self):
        self.engine = engine

    def test_exact_title_match(self):
        is_rejected, similar, analysis = self.engine.check_title(
            "Face Recognition Attendance System",
            ["face recognition attendance system", "Online Shopping"]
        )
        self.assertTrue(is_rejected)
        self.assertTrue(len(similar) >= 1)
        self.assertEqual(similar[0]["similarity"], 100)
        self.assertTrue(similar[0]["is_exact_match"])
        self.assertEqual(similar[0]["risk_level"], "High Risk")

    def test_paraphrased_duplicate_detection(self):
        # Paraphrased: Heart Disease Prediction vs Cardiac Illness Forecasting
        is_rejected, similar, analysis = self.engine.check_title(
            new_title="Heart Disease Risk Prediction System",
            existing_titles=["Cardiac Illness Probability Forecasting Tool"],
            new_description="Estimates cardiovascular illness probability from patient clinical records.",
            existing_projects=[{
                "title": "Cardiac Illness Probability Forecasting Tool",
                "description": "Assesses patient heart health and cardiovascular failure risk from medical data.",
                "domain": "Healthcare"
            }]
        )
        self.assertTrue(len(similar) >= 1)
        match = similar[0]
        self.assertGreaterEqual(match["similarity"], 58)
        self.assertEqual(match["risk_level"], "High Risk")
        self.assertEqual(match["recommendation"], "Review for possible duplication")

    def test_paraphrased_synonyms_without_lexical_overlap(self):
        # Fake news vs Disinformation
        is_rejected, similar, analysis = self.engine.check_title(
            new_title="Fake News Detection Using Natural Language Processing",
            existing_titles=["Rumor and Disinformation Filtering with Text Analytics"],
            new_description="Classifies online news articles as legitimate or deceptive.",
            existing_projects=[{
                "title": "Rumor and Disinformation Filtering with Text Analytics",
                "description": "Identifies deceptive internet articles and misinformation using NLP algorithms.",
                "domain": "Information Retrieval"
            }]
        )
        self.assertTrue(len(similar) >= 1)
        self.assertGreaterEqual(similar[0]["similarity"], 42)
        self.assertIn(similar[0]["risk_level"], ["Needs Review", "High Risk"])

    def test_false_positive_reduction_on_shared_boilerplate(self):
        # Both share "Forecasting Using LSTM", but tasks are completely different
        is_rejected, similar, analysis = self.engine.check_title(
            new_title="Air Quality Index Forecasting Using LSTM",
            existing_titles=["Stock Market Price Forecasting Using LSTM"],
            new_description="Predicts urban PM2.5 atmospheric pollution levels from environmental weather sensors.",
            existing_projects=[{
                "title": "Stock Market Price Forecasting Using LSTM",
                "description": "Predicts equity share valuations from financial ticker trade sequences.",
                "domain": "Finance"
            }]
        )
        # Should NOT trigger outright rejection (score must remain below 58% High Risk)
        if similar:
            self.assertLess(similar[0]["similarity"], 58)
        self.assertFalse(is_rejected)

    def test_distinct_projects_classified_as_low_risk(self):
        is_rejected, similar, analysis = self.engine.check_title(
            new_title="Employee Payroll and Tax Calculation System",
            existing_titles=["Underwater Robotic Submarine Navigation with Sonar"],
            new_description="Calculates employee net salary, tax withholdings, and paid leaves.",
            existing_projects=[{
                "title": "Underwater Robotic Submarine Navigation with Sonar",
                "description": "Navigates autonomous submersible vehicles mapping deep sea coral reefs.",
                "domain": "Robotics"
            }]
        )
        self.assertFalse(is_rejected)
        self.assertEqual(len(similar), 0)
        self.assertEqual(analysis["overall_risk"], "Low Risk")

    def test_empty_and_missing_inputs(self):
        # Empty inputs should not crash
        is_rejected, similar, analysis = self.engine.check_title("", [])
        self.assertFalse(is_rejected)
        self.assertEqual(similar, [])

        # Missing description should work on title alone
        is_rejected, similar, analysis = self.engine.check_title("Smart Attendance System", ["Smart Attendance System"])
        self.assertTrue(is_rejected)

    def test_unavailable_semantic_model_graceful_fallback(self):
        # Simulate semantic model unavailable
        with patch.object(ml_engine.semantic_service, "is_available", False):
            with patch.object(ml_engine.semantic_service, "status_message", "Simulated unavailable"):
                is_rejected, similar, analysis = self.engine.check_title(
                    new_title="Automated Library Book Lending System",
                    existing_titles=["Automated Library Book Lending System"]
                )
                self.assertTrue(is_rejected)
                self.assertFalse(analysis["semantic_model_active"])
                self.assertFalse(analysis["methods"][0]["active"])


class TestConciseFacultyDLReview(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        appmod.DB_PATH = self.path
        appmod.init_db()
        appmod.app.config["TESTING"] = True
        self.client = appmod.app.test_client()

        # Faculty login
        self.client.post("/api/auth/login", json={"username": "faculty", "password": "faculty123"})

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_decision_review_payload_structure(self):
        # Get first project ID from seeded projects
        res = self.client.get("/api/faculty/projects")
        self.assertEqual(res.status_code, 200)
        projects = res.get_json()["projects"]
        self.assertGreater(len(projects), 0)
        pid = projects[0]["id"]

        # Call dl-analysis endpoint
        dl_res = self.client.get(f"/api/faculty/project/{pid}/dl-analysis")
        self.assertEqual(dl_res.status_code, 200)
        data = dl_res.get_json()

        # Both dl_analysis (backward compatibility) and decision_review (new concise review) present
        self.assertIn("dl_analysis", data)
        self.assertIn("decision_review", data)

        rev = data["decision_review"]
        # Verify required concise fields
        self.assertIn("overall_review", rev)
        self.assertIn(rev["overall_review"], ["High Risk", "Needs Review", "Low Risk"])

        self.assertIn("similarity_score", rev)
        self.assertIsInstance(rev["similarity_score"], int)

        self.assertIn("similarity_risk", rev)
        self.assertIn(rev["similarity_risk"], ["High Risk", "Needs Review", "Low Risk"])

        self.assertIn("closest_matches", rev)
        self.assertIsInstance(rev["closest_matches"], list)

        self.assertIn("predicted_domain", rev)
        self.assertIsInstance(rev["predicted_domain"], str)

        self.assertIn("key_technologies", rev)
        self.assertIsInstance(rev["key_technologies"], list)

        self.assertIn("novelty_signal", rev)
        self.assertTrue(any(rev["novelty_signal"].startswith(s) for s in ["Normal", "Unusual", "Needs Review"]))

        self.assertIn("final_recommendation", rev)
        self.assertIn("model_reliability", rev)
        self.assertIn("semantic_active", rev["model_reliability"])


if __name__ == "__main__":
    unittest.main()
