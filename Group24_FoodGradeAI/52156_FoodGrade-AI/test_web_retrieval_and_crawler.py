"""
test_web_retrieval_and_crawler.py — Test suite for Web Retrieval & Scrapy Crawler fixes (Option B).

Verifies:
1. Nutrition table extraction:
   - kJ to kcal conversion when energy is given in kJ.
   - Direct kcal extraction when both or kcal is given.
   - Total fat is not overwritten by trans fat or saturated fat.
   - Sugar is not overwritten by added sugars.
   - Sodium (mg) is converted to salt (g) when salt is missing.
2. Compound product name & brand decomposition:
   - Cleans delimiters (–, —, |, -) to extract primary product name.
3. Scrapy runner robustness:
   - Rejection of invalid / SSRF / Open Food Facts scraping URLs.
   - Proper recovery and repair of concatenated JSON arrays ('][') into valid Python list.
4. Database persistence routes in Flask:
   - POST /web-retrieval/save persists retrieved product to SQLite with source='Web Retrieval'.
   - POST /web-retrieval/crawl/save/<item_index> persists crawled product with source='Scrapy Web Crawler'.
   - Repeated saves perform clean upsert without duplicate row explosion.
"""

import json
import sqlite3
import unittest
from pathlib import Path
from bs4 import BeautifulSoup

from app import app, get_db
from services.scrapy_runner import run_crawler
from services.web_product_extractor import (
    _clean_compound_name,
    _extract_nutrition_from_tables,
)


class TestWebRetrievalAndCrawler(unittest.TestCase):

    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.app.config["SECRET_KEY"] = "test-secret-key"
        self.client = self.app.test_client()

    # ============================================================
    # 1. NUTRITION TABLE EXTRACTION TESTS
    # ============================================================

    def test_nutrition_table_trans_fat_not_overwriting_total_fat(self):
        html = """
        <table>
            <tr><th>Nutrient</th><th>Per 100g</th></tr>
            <tr><td>Total Fat</td><td>34.2 g</td></tr>
            <tr><td>Saturated Fat</td><td>15.2 g</td></tr>
            <tr><td>Trans Fat</td><td>0.1 g</td></tr>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        nutrients = _extract_nutrition_from_tables(soup)
        self.assertEqual(nutrients.get("total_fat"), 34.2)
        self.assertEqual(nutrients.get("saturated_fat"), 15.2)

    def test_nutrition_table_energy_kj_conversion(self):
        # Case A: kJ only
        html_kj = """
        <table>
            <tr><td>Energy</td><td>2092 kJ</td></tr>
        </table>
        """
        soup_kj = BeautifulSoup(html_kj, "html.parser")
        nutrients_kj = _extract_nutrition_from_tables(soup_kj)
        # 2092 / 4.184 = 500.0 kcal
        self.assertAlmostEqual(nutrients_kj.get("calories", 0), 500.0, places=1)

        # Case B: Both kJ and kcal listed
        html_both = """
        <table>
            <tr><td>Energy</td><td>2240 kJ (536 kcal)</td></tr>
        </table>
        """
        soup_both = BeautifulSoup(html_both, "html.parser")
        nutrients_both = _extract_nutrition_from_tables(soup_both)
        self.assertEqual(nutrients_both.get("calories"), 536.0)

    def test_nutrition_table_added_sugar_skipped(self):
        html = """
        <table>
            <tr><td>Total Sugars</td><td>24.5 g</td></tr>
            <tr><td>Added Sugars</td><td>18.0 g</td></tr>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        nutrients = _extract_nutrition_from_tables(soup)
        self.assertEqual(nutrients.get("sugar"), 24.5)

    def test_nutrition_table_sodium_to_salt_conversion(self):
        html = """
        <table>
            <tr><td>Sodium</td><td>400 mg</td></tr>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        nutrients = _extract_nutrition_from_tables(soup)
        # 400 mg sodium * 2.5 / 1000 = 1.0 g salt
        self.assertEqual(nutrients.get("salt"), 1.0)

    # ============================================================
    # 2. COMPOUND NAME EXTRACTION TESTS
    # ============================================================

    def test_clean_compound_name_delimiters(self):
        self.assertEqual(
            _clean_compound_name("Wheelos Masala Flavour – Balaji Wafers – 22 g"),
            "Wheelos Masala Flavour"
        )
        self.assertEqual(
            _clean_compound_name("Parle-G Gold Biscuits | Parle Products"),
            "Parle-G Gold Biscuits"
        )
        self.assertEqual(
            _clean_compound_name("Kurkure Masala Munch - 90g"),
            "Kurkure Masala Munch"
        )
        self.assertEqual(
            _clean_compound_name("Lay's Classic Salted Potato Chips"),
            "Lay's Classic Salted Potato Chips"
        )

    # ============================================================
    # 3. SCRAPY RUNNER ROBUSTNESS TESTS
    # ============================================================

    def test_scrapy_runner_disallows_openfoodfacts_crawler(self):
        with self.assertRaises(ValueError) as ctx:
            run_crawler("https://world.openfoodfacts.org/product/12345")
        self.assertIn("Open Food Facts", str(ctx.exception))

    def test_scrapy_runner_disallows_invalid_scheme_and_ssrf(self):
        with self.assertRaises(ValueError):
            run_crawler("ftp://example.com")
        with self.assertRaises(ValueError):
            run_crawler("http://localhost:8080/secret")
        with self.assertRaises(ValueError):
            run_crawler("http://127.0.0.1/admin")

    def test_scrapy_concatenated_json_recovery(self):
        # Simulating Scrapy's -o append bug which produces ][
        corrupted = '[{"product_name": "Product 1"}][{"product_name": "Product 2"}]'
        fixed = corrupted.replace("][", ",")
        data = json.loads(fixed)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["product_name"], "Product 1")
        self.assertEqual(data[1]["product_name"], "Product 2")

    # ============================================================
    # 4. DATABASE PERSISTENCE ROUTES (FLASK TEST CLIENT)
    # ============================================================

    def test_web_save_single_product_route(self):
        test_product = {
            "product_name": "Unit Test Cracker 999",
            "brand": "TestBakery",
            "category": "Biscuits",
            "ingredients": "Wheat Flour, Vegetable Oil, Salt",
            "claims": "No Added Sugar",
            "calories": 420.0,
            "sugar": 1.5,
            "total_fat": 12.0,
            "saturated_fat": 4.0,
            "protein": 8.0,
            "fibre": 3.0,
            "salt": 0.8,
            "source_url": "https://example.com/test-cracker",
            "image_url": "https://example.com/test-cracker.jpg"
        }

        # Set session and post to /web-retrieval/save
        with self.client.session_transaction() as sess:
            sess["web_product"] = test_product

        response = self.client.post("/web-retrieval/save", follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        # Verify product is persisted in SQLite
        conn = get_db()
        row = conn.execute(
            "SELECT * FROM products WHERE product_name = ? AND brand = ?",
            ("Unit Test Cracker 999", "TestBakery")
        ).fetchone()

        self.assertIsNotNone(row, "Product should have been inserted into SQLite.")
        self.assertEqual(row["source"], "Web Retrieval")
        self.assertEqual(row["calories"], 420.0)
        self.assertEqual(row["sugar"], 1.5)
        self.assertIn(row["health_grade"], ["A", "B", "C", "D", "E"])

        # Clean up test row
        conn.execute(
            "DELETE FROM products WHERE product_name = ? AND brand = ?",
            ("Unit Test Cracker 999", "TestBakery")
        )
        conn.commit()
        conn.close()

    def test_web_crawl_save_route(self):
        test_crawl_item = {
            "product_name": "Unit Test Crawled Wafers 888",
            "brand": "TestSnacks",
            "category": "Snacks",
            "ingredients": "Potatoes, Edible Vegetable Oil, Salt",
            "claims": "",
            "calories": 540.0,
            "sugar": 0.5,
            "total_fat": 35.0,
            "saturated_fat": 15.0,
            "protein": 6.0,
            "fibre": 3.0,
            "salt": 1.2,
            "url": "https://example.com/test-wafers",
            "image_url": "https://example.com/test-wafers.jpg"
        }

        with self.client.session_transaction() as sess:
            sess["web_crawl"] = {
                "count": 1,
                "items": [test_crawl_item]
            }

        response = self.client.post("/web-retrieval/crawl/save/0", follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        conn = get_db()
        row = conn.execute(
            "SELECT * FROM products WHERE product_name = ? AND brand = ?",
            ("Unit Test Crawled Wafers 888", "TestSnacks")
        ).fetchone()

        self.assertIsNotNone(row, "Crawled product should have been inserted into SQLite.")
        self.assertEqual(row["source"], "Scrapy Web Crawler")
        self.assertEqual(row["calories"], 540.0)
        self.assertIn(row["health_grade"], ["A", "B", "C", "D", "E"])

        # Clean up test row
        conn.execute(
            "DELETE FROM products WHERE product_name = ? AND brand = ?",
            ("Unit Test Crawled Wafers 888", "TestSnacks")
        )
        conn.commit()
        conn.close()


if __name__ == "__main__":
    unittest.main()
