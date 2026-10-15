"""
FoodGrade AI — Dedicated Unit and Integration Test Suite
Objective 1: Health Scoring Safeguards & Explainability
Objective 2: 5-Tier Claim Verification Hierarchy & Vocabulary Expansion
"""

import math
import sqlite3
import unittest
from pathlib import Path

from app import app, get_db
from services.grading_engine import (
    calculate_foodgrade,
    calculate_health_score,
    verify_claims,
    normalize_nutrition,
    is_beverage_category,
    grade_from_score,
    get_claim_status_label,
)
from services.v3_extractor import extract_claims as v3_extract_claims
from services.v3_nlp import normalize_claim as v3_normalize_claim


class TestHealthGradingSafeguards(unittest.TestCase):
    """Tests for Objective 1: Health scoring improvements."""

    def test_genuine_zero_vs_missing_nutrient(self):
        """Genuine 0g sugar must score 100/100, while missing/None sugar must receive neutral 50/100."""
        # Product A: explicitly declared 0g sugar
        product_zero = {
            "product_name": "Zero Sugar Green Tea",
            "calories": 2.0,
            "sugar": 0.0,
            "total_fat": 0.0,
            "saturated_fat": 0.0,
            "protein": 0.5,
            "fibre": 0.0,
            "salt": 0.02,
        }
        res_zero = calculate_foodgrade(product_zero)
        self.assertEqual(res_zero["dimension_scores"]["sugar"], 100.0)
        self.assertNotIn("sugar", [f.lower() for f in res_zero["missing_fields"]])

        # Product B: undeclared sugar (None)
        product_missing = {
            "product_name": "Unspecified Snack",
            "calories": 250.0,
            "sugar": None,
            "total_fat": 10.0,
            "saturated_fat": 2.0,
            "protein": 8.0,
            "fibre": 3.0,
            "salt": 0.5,
        }
        res_missing = calculate_foodgrade(product_missing)
        self.assertEqual(res_missing["dimension_scores"]["sugar"], 50.0)
        self.assertTrue(any("sugar" in f.lower() for f in res_missing["missing_fields"]))
        self.assertTrue(any("sugar" in f.lower() for f in res_missing["missing_factors"]))

    def test_per_serving_scaling(self):
        """Snack nutrition declared per 30g serving must scale properly to 100g."""
        product_serving = {
            "product_name": "Mini Pretzels",
            "serving_size": "30g",
            "calories": 110.0,
            "sugar": 1.0,
            "total_fat": 1.0,
            "saturated_fat": 0.2,
            "protein": 3.0,
            "fibre": 1.0,
            "salt": 0.3,
        }
        norm, missing_fields, val_warnings = normalize_nutrition(product_serving)
        # 1.0g sugar in 30g becomes 3.33g in 100g
        self.assertAlmostEqual(norm["sugar"], 3.33, places=1)
        # 110 kcal in 30g becomes 366.7 kcal in 100g
        self.assertAlmostEqual(norm["calories"], 366.67, places=1)
        self.assertTrue(any("per-serving" in w.lower() for w in val_warnings))

    def test_energy_kj_fallback_to_kcal(self):
        """If kcal is missing but energy_kj is declared, convert using 1 kcal = 4.184 kJ."""
        product_kj = {
            "product_name": "European Cereal",
            "calories": None,
            "energy_kj": 1673.6,  # 1673.6 kJ = 400.0 kcal
            "sugar": 8.0,
            "total_fat": 4.0,
            "saturated_fat": 0.8,
            "protein": 11.0,
            "fibre": 9.0,
            "salt": 0.2,
        }
        norm, missing_fields, val_warnings = normalize_nutrition(product_kj)
        self.assertAlmostEqual(norm["calories"], 400.0, places=1)
        self.assertTrue(any("kj" in w.lower() or "kcal" in w.lower() for w in val_warnings))

    def test_negative_and_nonfinite_inputs(self):
        """Negative values, NaN, and Inf must be rejected and flagged in validation warnings."""
        product_bad = {
            "product_name": "Corrupted Data Item",
            "calories": -150.0,
            "sugar": float("nan"),
            "total_fat": float("inf"),
            "saturated_fat": -5.0,
            "protein": 10.0,
            "fibre": 2.0,
            "salt": 0.5,
        }
        norm, missing_fields, val_warnings = normalize_nutrition(product_bad)
        self.assertIsNone(norm["calories"])
        self.assertIsNone(norm["sugar"])
        self.assertIsNone(norm["total_fat"])
        self.assertIsNone(norm["saturated_fat"])

    def test_physical_implausibility_guards(self):
        """Nutrients exceeding 100g per 100g or calories exceeding 950 kcal must trigger warnings."""
        product_implausible = {
            "product_name": "Faulty Label Item",
            "calories": 1200.0,  # Physically implausible for food (< 900 kcal/100g pure fat)
            "sugar": 150.0,    # > 100g per 100g
            "total_fat": 5.0,
            "saturated_fat": 1.0,
            "protein": 5.0,
            "fibre": 2.0,
            "salt": 0.1,
        }
        norm, missing_fields, val_warnings = normalize_nutrition(product_implausible)
        self.assertTrue(any("100g" in w or "implausible" in w.lower() for w in val_warnings))

    def test_beverage_vs_solid_thresholds(self):
        """Liquid beverages must be assessed against strict liquid sugar thresholds."""
        self.assertTrue(is_beverage_category("Soft Drinks"))
        self.assertTrue(is_beverage_category("Fruit Juices and Nectars"))
        self.assertFalse(is_beverage_category("Biscuits and Cookies"))

        # Beverage with 7g sugar (high for liquid: soft drink threshold is 5g/100ml)
        bev = {
            "product_name": "Sweet Iced Tea",
            "category": "Beverages",
            "calories": 35.0,
            "sugar": 7.0,
            "total_fat": 0.0,
            "saturated_fat": 0.0,
            "protein": 0.0,
            "fibre": 0.0,
            "salt": 0.01,
        }
        res_bev = calculate_foodgrade(bev)
        self.assertTrue(res_bev["is_beverage"])
        # Sugar dimension score for 7g in beverage must be low (< 60)
        self.assertLess(res_bev["dimension_scores"]["sugar"], 60.0)

    def test_insufficient_data_status(self):
        """Product with no declared calories or macros must return INSUFFICIENT_DATA status."""
        sparse_product = {
            "product_name": "Empty Label Item",
            "claims": "Healthy snack",
        }
        res = calculate_foodgrade(sparse_product)
        self.assertEqual(res["health_status"], "INSUFFICIENT_DATA")
        self.assertIsNone(res["health_score"])
        self.assertEqual(res["health_grade"], "Insufficient Data")

    def test_explainable_factors_generation(self):
        """Scoring output must provide structured positive, negative, and missing factors."""
        product = {
            "product_name": "Whole Grain Oats",
            "calories": 360.0,
            "sugar": 1.2,
            "total_fat": 6.5,
            "saturated_fat": 1.1,
            "protein": 13.5,
            "fibre": 10.0,
            "salt": 0.02,
        }
        res = calculate_foodgrade(product)
        self.assertIsInstance(res["positive_factors"], list)
        self.assertIsInstance(res["negative_factors"], list)
        self.assertIsInstance(res["missing_factors"], list)
        self.assertTrue(len(res["positive_factors"]) >= 2)
        # Should highlight low sugar, low saturated fat, high protein or fibre
        pos_text = " ".join(res["positive_factors"]).lower()
        self.assertTrue("sugar" in pos_text or "protein" in pos_text or "fibre" in pos_text)


class TestClaimVerificationHierarchy(unittest.TestCase):
    """Tests for Objective 2: 5-tier claim verification and vocabulary expansion."""

    def test_status_verified(self):
        """Verified claim when product satisfies statutory FSSAI threshold."""
        product = {
            "product_name": "Protein Bar",
            "claims": "High Protein",
            "protein": 15.0,  # FSSAI threshold >= 10g/100g
            "ingredients": "Whey protein, oats",
        }
        score, grade, status, reasons, details = verify_claims(product)
        self.assertEqual(status, "VERIFIED")
        self.assertEqual(grade, "A")
        self.assertEqual(details[0]["status"], "VERIFIED")

    def test_status_claim_detected_unverified(self):
        """Packaging text with puffery or non-statutory claims must receive CLAIM_DETECTED_UNVERIFIED."""
        product = {
            "product_name": "Chocolate Cookies",
            "claims": "Tasty, Energy Rich",
            "calories": 480.0,
            "sugar": 32.0,
            "total_fat": 20.0,
            "saturated_fat": 10.0,
            "protein": 5.0,
            "fibre": 1.5,
            "salt": 0.8,
            "ingredients": "Wheat flour, sugar, palm oil, cocoa powder",
        }
        score, grade, status, reasons, details = verify_claims(product)
        self.assertEqual(status, "CLAIM_DETECTED_UNVERIFIED")
        self.assertEqual(grade, "C")
        self.assertEqual(score, 50.0)
        self.assertEqual(details[0]["status"], "CLAIM_DETECTED_UNVERIFIED")
        evidence_lower = details[0]["evidence"].lower()
        self.assertTrue("marketing" in evidence_lower or "qualitative" in evidence_lower or "unverified" in evidence_lower)

    def test_status_not_verified_claim_failed(self):
        """Statutory claim that fails FSSAI threshold must receive NOT_VERIFIED."""
        product = {
            "product_name": "Diet Biscuit",
            "claims": "Sugar Free",
            "sugar": 4.5,  # FSSAI Sugar Free threshold is <= 0.5g/100g
            "ingredients": "Wheat flour, sugar, vegetable oil",
        }
        score, grade, status, reasons, details = verify_claims(product)
        self.assertEqual(status, "NOT_VERIFIED")
        self.assertEqual(grade, "E")
        self.assertEqual(details[0]["status"], "NOT_VERIFIED")

    def test_status_insufficient_evidence(self):
        """Claim made but corresponding nutrient undeclared receives INSUFFICIENT_EVIDENCE."""
        product = {
            "product_name": "Fibre Cracker",
            "claims": "High Fibre",
            "fibre": None,
            "ingredients": "Whole wheat flour",
        }
        score, grade, status, reasons, details = verify_claims(product)
        self.assertEqual(status, "INSUFFICIENT_EVIDENCE")
        self.assertEqual(details[0]["status"], "INSUFFICIENT_EVIDENCE")

    def test_status_no_claims_detected(self):
        """Assessed product with empty or 'None' claim field receives NO_CLAIMS_DETECTED."""
        product_empty = {
            "product_name": "Basmati Rice",
            "claims": "",
            "calories": 350.0,
            "sugar": 0.2,
            "protein": 7.0,
        }
        score, grade, status, reasons, details = verify_claims(product_empty)
        self.assertEqual(status, "NO_CLAIMS_DETECTED")
        self.assertEqual(grade, "No Claim")
        self.assertEqual(score, 0.0)

        product_none_word = {
            "product_name": "Table Salt",
            "claims": "None",
            "salt": 98.0,
        }
        _, grade2, status2, _, _ = verify_claims(product_none_word)
        self.assertEqual(status2, "NO_CLAIMS_DETECTED")

    def test_status_not_assessed(self):
        """Product where claims field is NULL / None receives NOT_ASSESSED."""
        product_null = {
            "product_name": "Raw Wheat Grain",
            "claims": None,
            "calories": 340.0,
        }
        score, grade, status, reasons, details = verify_claims(product_null)
        self.assertEqual(status, "NOT_ASSESSED")
        self.assertEqual(grade, "Not Assessed")
        self.assertIsNone(score)

    def test_expanded_vocabulary_extractor_and_nlp(self):
        """Extractor and NLP layer must recognize newly added nutrition claim types."""
        test_phrases = [
            ("Contains Source of Protein for daily health", "source_of_protein"),
            ("Good source of dietary fibre", "source_of_fibre"),
            ("Rich source of dietary fibre", "high_fibre"),
            ("Low in sugar for healthy snacking", "low_sugar"),
            ("Sugar free recipe", "sugar_free"),
            ("No added sugars in this jam", "no_added_sugar"),
            ("Low fat content", "low_fat"),
            ("100% Fat Free", "fat_free"),
            ("Zero Trans Fat baked goods", "trans_fat_free"),
            ("Low sodium seasoning", "low_sodium"),
        ]
        for phrase, expected_type in test_phrases:
            extracted = v3_extract_claims(phrase)
            self.assertTrue(len(extracted) >= 1, f"Failed to extract: {phrase}")
            norm = v3_normalize_claim(extracted[0]["text"])
            self.assertEqual(norm["normalized"], expected_type, f"Mismatched type for: {phrase}")


class TestDatabaseAndIntegration(unittest.TestCase):
    """Tests for database persistence and full route rendering."""

    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_database_claim_status_column_and_sync(self):
        """Database products table must contain claim_status and keep it synchronized."""
        conn = get_db()
        cols = [c[1] for c in conn.execute("PRAGMA table_info(products)").fetchall()]
        self.assertIn("claim_status", cols)

        # Check existing seeded products
        row2 = conn.execute("SELECT * FROM products WHERE id = 2").fetchone()
        if row2:
            self.assertEqual(row2["claim_status"], "CLAIM_DETECTED_UNVERIFIED")
            self.assertEqual(row2["claim_grade"], "C")
        conn.close()

    def test_catalog_and_detail_route_rendering(self):
        """Catalogue and product detail pages must render HTTP 200 with new badges."""
        # Test /products
        resp = self.client.get("/products")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Claim Status", resp.data)

        # Test /product/2 (Chocolate Cream Biscuits - Unverified Claim)
        resp2 = self.client.get("/product/2")
        self.assertEqual(resp2.status_code, 200)
        self.assertIn(b"Claim Detected", resp2.data)
        self.assertIn(b"Positive Factors", resp2.data)
        self.assertIn(b"Negative Factors", resp2.data)


if __name__ == "__main__":
    unittest.main()
