"""
Unit & Integration Tests for Deep Learning Syllabus Modules
============================================================
Tests:
- Empty and invalid input handling
- LSTM sequence classifier output shapes, domain categories, and probabilities
- Model loading and missing artifact graceful fallbacks
- Autoencoder reconstruction MSE and anomaly detection
- Neural Named Entity Recognition (token classification and gazetteer normalization)
- Unified dl_engine pipeline and API endpoints
- Database column retention and migration
"""

import os
import tempfile
import unittest
import torch

import app as appmod
import dl_engine
from dl_engine.preprocessing import (
    Vocabulary,
    clean_text,
    tokenize,
    PROJECT_DOMAINS,
)
from dl_engine.lstm_classifier import LSTMClassifierService, ProjectDomainLSTM
from dl_engine.autoencoder import AutoencoderService, ProjectAutoencoder
from dl_engine.ner_extractor import NERService, NeuralNERModel


class TestDLPreprocessing(unittest.TestCase):
    def test_clean_text_and_tokenize(self):
        self.assertEqual(clean_text(""), "")
        self.assertEqual(clean_text("   Hello, World! 123...  "), "hello world 123")
        self.assertEqual(tokenize("Deep-Learning & AI!"), ["deep-learning", "ai"])

    def test_vocab_encoding_padding_truncation(self):
        v = Vocabulary()
        v.build_vocab(["apple banana orange", "banana orange cherry"])
        encoded = v.encode("apple cherry unknown", max_len=5)
        self.assertEqual(len(encoded), 5)
        self.assertEqual(encoded[0], v.word2idx["apple"])
        self.assertEqual(encoded[1], v.word2idx["cherry"])
        self.assertEqual(encoded[2], 1)  # <unk>
        self.assertEqual(encoded[3], 0)  # <pad>
        self.assertEqual(encoded[4], 0)  # <pad>


class TestLSTMClassifier(unittest.TestCase):
    def setUp(self):
        self.service = LSTMClassifierService()

    def test_empty_input(self):
        res = self.service.predict("")
        self.assertEqual(res["status"], "invalid_input")
        self.assertIsNone(res["predicted_domain"])
        self.assertEqual(res["confidence"], 0.0)

    def test_prediction_output_shape_and_labels(self):
        res = self.service.predict("Skin Cancer Detection Using CNN and Transfer Learning")
        self.assertEqual(res["status"], "success")
        self.assertIn(res["predicted_domain"], PROJECT_DOMAINS)
        self.assertTrue(0.0 <= res["confidence"] <= 1.0)
        self.assertEqual(set(res["probabilities"].keys()), set(PROJECT_DOMAINS))

    def test_missing_artifacts_fallback(self):
        empty_service = LSTMClassifierService(artifacts_dir=tempfile.gettempdir())
        res = empty_service.predict("Test project proposal")
        self.assertEqual(res["status"], "model_not_trained")
        self.assertIsNone(res["predicted_domain"])

    def test_crop_yield_classified_as_agriculture(self):
        crop_text = (
            "Crop Yield Prediction Using Machine Learning and IoT Sensors. "
            "Predicts crop yield based on rainfall, soil nutrients, and temperature "
            "using Random Forest and Linear Regression algorithms in Python."
        )
        res = self.service.predict(crop_text)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["predicted_domain"], "Agriculture")
        self.assertFalse(res["is_uncertain"])
        self.assertEqual(res["decision_status"], "Prediction Available")
        # Ensure Unit IV LSTM also evaluated correctly
        self.assertEqual(res["lstm_domain"], "Agriculture")

    def test_uncertainty_handling_on_out_of_distribution(self):
        # Rare/out of vocabulary text should trigger uncertainty warning
        gibberish = "Xylophonic quantum zwitterion flux supercondenser impedance"
        res = self.service.predict(gibberish)
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["is_uncertain"])
        self.assertIn("Needs Faculty Review", res["decision_status"])


class TestAutoencoder(unittest.TestCase):
    def setUp(self):
        self.service = AutoencoderService()

    def test_empty_input(self):
        res = self.service.evaluate_novelty("")
        self.assertEqual(res["status"], "invalid_input")
        self.assertFalse(res["is_unusual"])

    def test_novelty_evaluation(self):
        res = self.service.evaluate_novelty("Online Shopping Management System")
        self.assertEqual(res["status"], "success")
        self.assertIsInstance(res["reconstruction_error"], float)
        self.assertGreater(res["reconstruction_error"], 0.0)
        self.assertIsInstance(res["is_unusual"], bool)
        self.assertIn("interpretation", res)

    def test_zero_vector_unfamiliar_vocabulary_handling(self):
        # Text with completely unfamiliar vocabulary should be flagged as unfamiliar outlier
        res = self.service.evaluate_novelty("Quantum entanglement teleportation in non abelian anyon lattices")
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["is_unusual"])
        self.assertTrue(res["is_unfamiliar_vocabulary"])
        self.assertIn("Experimental Novelty Signal", res["interpretation"])

    def test_missing_artifacts_fallback(self):
        empty_service = AutoencoderService(artifacts_dir=tempfile.gettempdir())
        res = empty_service.evaluate_novelty("Test project proposal")
        self.assertEqual(res["status"], "model_not_trained")
        self.assertFalse(res["is_unusual"])


class TestNERExtractor(unittest.TestCase):
    def setUp(self):
        self.service = NERService()

    def test_empty_input(self):
        res = self.service.extract_entities("")
        self.assertEqual(res["status"], "invalid_input")
        self.assertEqual(res["entities"], [])

    def test_entity_extraction_and_grouping(self):
        text = "Deep Learning Project Using Python, Flask, PyTorch, and LSTM for Healthcare Attendance"
        res = self.service.extract_entities(text)
        self.assertEqual(res["status"], "success")
        self.assertIn("Python", res["grouped"]["languages"])
        self.assertTrue(any(t in res["grouped"]["frameworks"] for t in ["Flask", "PyTorch"]))
        self.assertTrue(any(m in res["grouped"]["methods"] for m in ["LSTM", "Deep Learning"]))
        # Verify separation of neural predictions and gazetteer entities
        self.assertIn("neural_entities", res)
        self.assertIn("gazetteer_entities", res)
        self.assertIn("dataset_note", res)

    def test_crop_yield_ner_cleaning_no_stopword_clutter(self):
        crop_text = (
            "Crop Yield Prediction Using Machine Learning and IoT Sensors. "
            "Predicts crop yield based on rainfall, soil nutrients, and temperature "
            "using Random Forest and Linear Regression algorithms in Python."
        )
        res = self.service.extract_entities(crop_text)
        self.assertEqual(res["status"], "success")
        # Ensure meaningful methods are extracted
        methods = res["grouped"]["methods"]
        self.assertIn("Random Forest", methods)
        self.assertIn("Linear Regression", methods)
        self.assertIn("Machine Learning", methods)
        # Ensure language extracted
        self.assertIn("Python", res["grouped"]["languages"])
        # Ensure ordinary stopwords like 'predicts', 'based', 'using', 'and', 'on' are strictly filtered out
        all_extracted_texts = [e["text"].lower() for e in res["entities"]]
        for spurious in ["predicts", "based", "using", "and", "on", "in", "with"]:
            self.assertNotIn(spurious, all_extracted_texts)
            self.assertNotIn(spurious.title(), res["grouped"]["languages"])
            self.assertNotIn(spurious.title(), res["grouped"]["frameworks"])
            self.assertNotIn(spurious.title(), res["grouped"]["methods"])


class TestDLApisAndIntegration(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        appmod.DB_PATH = self.path
        appmod.init_db()
        appmod.app.config["TESTING"] = True
        self.c = appmod.app.test_client()

    def tearDown(self):
        try:
            os.remove(self.path)
        except Exception:
            pass

    def test_analyze_proposal_endpoint(self):
        # Requires login
        res_unauth = self.c.post("/api/dl/analyze", json={"title": "Test Title"})
        self.assertEqual(res_unauth.status_code, 401)

        # Login student
        self.c.post("/api/auth/register", json={"username": "21CS999", "password": "pass123", "name": "Student Test"})
        res = self.c.post("/api/dl/analyze", json={
            "title": "Heart Disease Risk Prediction System",
            "description": "Uses machine learning models trained in Python with Flask web application."
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("domain_classification", data)
        self.assertIn("novelty_analysis", data)
        self.assertIn("named_entities", data)

    def test_submit_project_persists_dl_fields(self):
        self.c.post("/api/auth/register", json={"username": "21CS888", "password": "pass123", "name": "Alice ML"})
        res = self.c.post("/api/student/project", json={
            "title": "Smart Farm Irrigation and Crop Disease Detection",
            "description": "Utilizes PyTorch deep learning and IoT sensors in Python."
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertIn("dl_analysis", data)
        self.assertIn("Agriculture", data["project"]["domain"])

        # Check faculty review endpoint
        f = appmod.app.test_client()
        f.post("/api/auth/login", json={"username": "faculty", "password": "faculty123"})
        pid = data["project"]["id"]
        rev_res = f.get(f"/api/faculty/project/{pid}/dl-analysis")
        self.assertEqual(rev_res.status_code, 200)
        rev_data = rev_res.get_json()
        self.assertEqual(rev_data["project"]["id"], pid)
        self.assertIn("named_entities", rev_data["dl_analysis"])

        # Check faculty stats & projects endpoints
        stats_res = f.get("/api/faculty/stats")
        self.assertEqual(stats_res.status_code, 200)
        stats_data = stats_res.get_json()
        self.assertIn("stats", stats_data)
        self.assertGreaterEqual(stats_data["stats"]["totalProjects"], 1)

        proj_res = f.get("/api/faculty/projects")
        self.assertEqual(proj_res.status_code, 200)
        proj_data = proj_res.get_json()
        self.assertIn("projects", proj_data)
        self.assertGreaterEqual(len(proj_data["projects"]), 1)

    def test_faculty_html_template_integrity(self):
        # Verify public/faculty.html structure and scripts
        with open("public/faculty.html", "r", encoding="utf-8") as f:
            html = f.read()
        self.assertIn('id="stat-students"', html)
        self.assertIn('id="projects-content"', html)
        self.assertIn('id="dl-modal"', html)
        self.assertIn('id="warn-modal"', html)
        # Ensure only 1 script tag exists and modal HTML is outside the script block
        script_open_count = html.count("<script>")
        script_close_count = html.count("</script>")
        self.assertEqual(script_open_count, 1)
        self.assertEqual(script_close_count, 1)
        script_content = html.split("<script>")[1].split("</script>")[0]
        self.assertNotIn("<!-- DL Review Modal -->", script_content)
        self.assertNotIn('id="dl-modal"', script_content)
        self.assertNotIn('id="warn-modal"', script_content)


if __name__ == "__main__":
    unittest.main()
