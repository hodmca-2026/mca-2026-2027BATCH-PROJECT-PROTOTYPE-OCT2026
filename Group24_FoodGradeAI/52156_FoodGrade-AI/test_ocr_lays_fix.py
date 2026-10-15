"""
test_ocr_lays_fix.py — Comprehensive regression test suite for FoodGrade AI OCR Fix.

Verifies:
1. Lay's image OCR extraction:
   - Product name: Lay's Classic Salted Potato Chips
   - Brand: PepsiCo
   - Category: Snacks
   - Serving size: 20.0 g
   - FSSAI License Number: 10014064000435
   - Ingredients: Potatoes, Edible Vegetable Oil (Palmolein Oil), Iodised Salt, Antioxidant (INS 319)
   - OCR Confidence: high
2. All 9 Nutrition values targeting Per 100g (uncoerced):
   - Energy: 536.0 kcal (not 5% RDA)
   - Protein: 6.6 g
   - Carbohydrates: 53.6 g
   - Sugar: 0.6 g
   - Total Fat: 34.2 g
   - Saturated Fat: 15.2 g (not 15% RDA, not 152.0)
   - Trans Fat: 0.1 g
   - Cholesterol: 0.0 mg (genuine zero preserved)
   - Sodium: 670.0 mg (salt = 1.675 g)
3. Grading behavior:
   - Real Lay's scores Health Grade E (high fat, sat fat, salt), NOT false Grade C
   - Claim status: NO_CLAIMS_DETECTED, Claim Grade: No Claim
4. Incomplete / Blank images:
   - Evaluated as INSUFFICIENT_DATA, score None, grade Insufficient Data (never false Grade C)
5. Recommender:
   - All recommended items have > 0% similarity and match category/content
   - Zero-similarity items are excluded
6. Product name validator:
   - Rejects 'a QF yay @ d', 'leo acts', 'OCR Product', 'Food Product'
   - Accepts 'Lay\'s Classic Salted Potato Chips', 'Lay\'s Classic 26g'
"""

import os
import unittest
from pathlib import Path

from services.v5_ocr import (
    extract_product_from_text,
    extract_table_nutrients,
    extract_serving_size,
    extract_fssai,
    extract_ingredients,
    extract_product_name,
    extract_brand,
    extract_category,
    is_valid_product_name,
    perform_ocr_and_extract,
)
from services.grading_engine import calculate_foodgrade
from services.v5_recommender import recommend_similar_products


class TestLaysOCRFix(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.lays_image_path = Path("data/ocr/WhatsApp_Image_2026-10-13_at_23.03.42.jpeg")
        if not cls.lays_image_path.exists():
            raise unittest.SkipTest(f"Test image not found at {cls.lays_image_path}")

        cls.text, cls.product, cls.rows = perform_ocr_and_extract(str(cls.lays_image_path))
        cls.grade_result = calculate_foodgrade(cls.product)

    def test_product_identification(self):
        """Lay's chips image must identify product name, brand, and category correctly."""
        self.assertEqual(self.product.get("product_name"), "Lay's Classic Salted Potato Chips")
        self.assertEqual(self.product.get("brand"), "PepsiCo")
        self.assertEqual(self.product.get("category"), "Snacks")

    def test_serving_size_and_fssai(self):
        """Serving size (20g) and 14-digit FSSAI license number must be accurately extracted."""
        self.assertEqual(self.product.get("serving_size"), 20.0)
        self.assertEqual(self.product.get("fssai"), "10014064000435")

    def test_ingredients_extraction(self):
        """Ingredients must be extracted cleanly without OCR noise fragments."""
        ing = self.product.get("ingredients", "")
        self.assertIn("Potatoes", ing)
        self.assertIn("Edible Vegetable Oil", ing)
        self.assertIn("Iodised Salt", ing)
        self.assertIn("Antioxidant (INS 319)", ing)
        self.assertNotIn("a QF yay", ing)

    def test_per_100g_nutrition_values(self):
        """All 9 Per 100g nutrition values must match label declarations without confusion."""
        raw = self.product.get("raw_nutrition", {})
        self.assertEqual(raw.get("energy_kcal"), 536.0)
        self.assertEqual(raw.get("protein_g"), 6.6)
        self.assertEqual(raw.get("carbohydrates_g"), 53.6)
        self.assertEqual(raw.get("sugar_g"), 0.6)
        self.assertEqual(raw.get("total_fat_g"), 34.2)
        self.assertEqual(raw.get("saturated_fat_g"), 15.2)
        self.assertEqual(raw.get("trans_fat_g"), 0.1)
        self.assertEqual(raw.get("cholesterol_mg"), 0.0)
        self.assertEqual(raw.get("sodium_mg"), 670.0)
        self.assertEqual(raw.get("salt_g"), 1.675)

    def test_genuine_zero_preservation(self):
        """Cholesterol must be preserved as genuine 0.0 mg rather than None."""
        raw = self.product.get("raw_nutrition", {})
        self.assertIsNotNone(raw.get("cholesterol_mg"))
        self.assertEqual(raw.get("cholesterol_mg"), 0.0)

    def test_ocr_confidence(self):
        """When complete nutrition table is detected, confidence should be high."""
        self.assertEqual(self.product.get("ocr_confidence"), "high")

    def test_health_grading_accuracy(self):
        """High-fat chips with 34.2g fat and 15.2g saturated fat must receive Grade E, not false Grade C."""
        self.assertEqual(self.grade_result.get("health_grade"), "E")
        self.assertLess(self.grade_result.get("health_score"), 45.0)
        self.assertEqual(self.grade_result.get("health_status"), "GRADED")

    def test_claim_assessment_accuracy(self):
        """Lay's classic salted chips have no nutritional claims; should be NO_CLAIMS_DETECTED."""
        self.assertEqual(self.grade_result.get("claim_status"), "NO_CLAIMS_DETECTED")
        self.assertEqual(self.grade_result.get("claim_grade"), "No Claim")
        self.assertEqual(self.grade_result.get("claim_score"), 0.0)

    def test_blank_image_insufficient_data(self):
        """Blank or non-nutrition label must return INSUFFICIENT_DATA and not a false Grade C."""
        blank_text = "Some non food text without any nutrition table or declarations."
        blank_prod = extract_product_from_text(blank_text)
        res = calculate_foodgrade(blank_prod)
        self.assertIsNone(res.get("health_score"))
        self.assertEqual(res.get("health_grade"), "Insufficient Data")
        self.assertEqual(res.get("health_status"), "INSUFFICIENT_DATA")

    def test_name_validation_rejections(self):
        """Malformed and junk strings must be rejected."""
        self.assertFalse(is_valid_product_name("a QF yay @ d"))
        self.assertFalse(is_valid_product_name("leo acts"))
        self.assertFalse(is_valid_product_name("OCR Product"))
        self.assertFalse(is_valid_product_name("Food Product"))
        self.assertFalse(is_valid_product_name(""))

    def test_name_validation_acceptances(self):
        """Legitimate product names must be accepted."""
        self.assertTrue(is_valid_product_name("Lay's Classic Salted Potato Chips"))
        self.assertTrue(is_valid_product_name("Lay's Classic 26g"))
        self.assertTrue(is_valid_product_name("Haldiram's Aloo Bhujia Sev"))
        self.assertTrue(is_valid_product_name("Parle-G"))

    def test_recommendations_exclude_zero_similarity(self):
        """Recommender must return authentic snacks with > 0% similarity and no unrelated 0% items."""
        sample_catalogue = [
            {"product_name": "Haldiram's Aloo Bhujia Sev", "brand": "Haldiram's", "category": "Snacks", "ingredients": "Potatoes, Edible Vegetable Oil, Salt", "claims": ""},
            {"product_name": "Balaji Wafers Masala", "brand": "Balaji", "category": "Snacks", "ingredients": "Potatoes, Palmolein Oil, Salt, Spices", "claims": ""},
            {"product_name": "Amul Fresh Toned Milk", "brand": "Amul", "category": "Dairy", "ingredients": "Toned Milk, Vitamin A, Vitamin D", "claims": ""},
            {"product_name": "Colgate Dental Cream", "brand": "Colgate", "category": "Oral Care", "ingredients": "Calcium Carbonate, Sodium Monofluorophosphate", "claims": ""},
        ]
        recs = recommend_similar_products(self.product, sample_catalogue, top_n=5)
        self.assertTrue(len(recs) > 0)
        for r in recs:
            self.assertGreater(r["similarity"], 0.0)
            self.assertEqual(r["product"]["category"], "Snacks")


if __name__ == "__main__":
    unittest.main()
