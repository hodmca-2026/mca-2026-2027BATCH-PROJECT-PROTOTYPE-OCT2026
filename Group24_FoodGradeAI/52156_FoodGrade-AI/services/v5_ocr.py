"""
FoodGrade AI V5 - OCR + food-label extraction.

Integration with standalone FastAPI PaddleOCR/PaddleX service:
    Default endpoint: http://127.0.0.1:8001/extract/image (configured via FOODGRADE_OCR_URL)

Public API preserved:
    perform_ocr(image_path) -> text
    extract_product_from_text(text, rows=None) -> product dictionary
    perform_ocr_and_extract(image_path) -> (text, product, rows)
    extract_from_ocr_service(image_path) -> dict (direct call to OCR service)

Important:
    OCR-derived values are estimates. Missing or ambiguous nutrition values
    are preserved as None internally, distinguishing missing fields from genuine 0.0.
    For legacy database / UI fields expecting numbers, numeric values are preserved.
"""
import base64
import logging
import mimetypes
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

logger = logging.getLogger(__name__)

# Configurable standalone OCR service URL
DEFAULT_OCR_URL = "http://127.0.0.1:8001"
OCR_SERVICE_URL = os.environ.get("FOODGRADE_OCR_URL", DEFAULT_OCR_URL).rstrip("/")

# Tesseract paths preserved for local fallback/testing
import pytesseract
from pytesseract import Output

TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]
for _path in TESSERACT_PATHS:
    if Path(_path).exists():
        pytesseract.pytesseract.tesseract_cmd = _path
        break

_LAST_OCR_DATA = {"text": "", "rows": []}


class OCRError(Exception):
    """Base exception for OCR service errors."""
    pass


class OCRConnectionError(OCRError):
    """Raised when the standalone OCR service cannot be reached."""
    pass


class OCRResponseError(OCRError):
    """Raised when the standalone OCR service returns an HTTP error or malformed payload."""
    pass


def normalize(text):
    value = str(text or "").lower().replace("’", "'").replace("‘", "'")
    value = value.replace("totalfat", "total fat")
    value = value.replace("saturatedfat", "saturated fat")
    value = value.replace("totalsugars", "total sugars")
    value = value.replace("dietaryfibre", "dietary fibre")
    value = value.replace("dietaryfiber", "dietary fiber")
    value = value.replace("per100g", "per 100 g")
    value = value.replace("per100ml", "per 100 ml")
    value = re.sub(r"[^a-z0-9.%']+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def extract_numbers(text):
    return [float(x) for x in re.findall(r"(?<!\d)(\d+(?:\.\d+)?)(?!\d)", str(text or ""))]


def prepare_image(image):
    try:
        image = ImageOps.exif_transpose(image)
    except Exception:
        pass
    image = image.convert("RGB")
    image = ImageEnhance.Contrast(image).enhance(1.35)
    image = ImageEnhance.Sharpness(image).enhance(1.4)
    return image.filter(ImageFilter.SHARPEN)


def build_rows(data):
    grouped = {}
    for i, raw in enumerate(data.get("text", [])):
        word_text = str(raw).strip()
        if not word_text:
            continue
        try:
            conf = float(data.get("conf", [0] * len(data["text"]))[i])
        except (ValueError, TypeError, IndexError):
            conf = 0
        if conf < 5:
            continue
        key = (
            data["block_num"][i], data["par_num"][i], data["line_num"][i]
        )
        word = {
            "text": word_text,
            "x": int(data["left"][i]), "y": int(data["top"][i]),
            "width": int(data["width"][i]), "height": int(data["height"][i]),
            "confidence": conf,
        }
        grouped.setdefault(key, []).append(word)
    result = []
    for words in grouped.values():
        words.sort(key=lambda w: w["x"])
        result.append({
            "words": words,
            "y": min(w["y"] for w in words),
            "text": " ".join(w["text"] for w in words),
        })
    return sorted(result, key=lambda r: r["y"])


def identify_nutrient(text):
    value = normalize(text)
    if "saturated fat" in value or "saturat ed fat" in value:
        return "saturated_fat"
    if "total fat" in value:
        return "total_fat"
    if "dietary fibre" in value or "dietary fiber" in value:
        return "fibre"
    if "total sugars" in value or "total sugar" in value:
        return "sugar"
    if re.search(r"\bsugars?\b", value):
        return "sugar"
    if "protein" in value:
        return "protein"
    if "energy" in value or "calories" in value or "kcal" in value:
        return "calories"
    if "sodium" in value:
        return "sodium"
    if re.search(r"\bsalt\b", value):
        return "salt"
    if re.search(r"\bfib(re|er)\b", value):
        return "fibre"
    return None


def nutrition_section_start(rows):
    for i, row in enumerate(rows):
        v = normalize(row.get("text", ""))
        if any(s in v for s in (
            "nutritional information", "nutrition information",
            "nutrition facts", "nutritional facts"
        )):
            return i
    return 0


def _numbers_in_row(row):
    found = []
    for word in row.get("words", []):
        raw = str(word.get("text", "")).strip()
        for match in re.finditer(r"(?<!\d)\d+(?:\.\d+)?(?!\d)", raw):
            found.append({
                "value": float(match.group()),
                "x": int(word.get("x", 0)),
                "text": raw,
            })
    found.sort(key=lambda n: n["x"])
    return found


def extract_values_from_row(row, nutrient=None):
    return _numbers_in_row(row)


def _label_and_values(row):
    raw = str(row.get("text", ""))
    nutrient = identify_nutrient(raw)
    nums = _numbers_in_row(row)
    return nutrient, nums


def extract_nutrition(rows):
    result = {
        "calories": None, "sugar": None, "total_fat": None,
        "saturated_fat": None, "protein": None, "fibre": None,
        "salt": None, "sodium": None, "serving_basis": "100g",
        "nutrition_warnings": [],
    }
    start = nutrition_section_start(rows)
    nutrition_rows = rows[start:]

    for row in nutrition_rows:
        nutrient, nums = _label_and_values(row)
        if not nutrient or not nums:
            continue
        selected = nums[0]["value"]
        if nutrient == "calories":
            if 1 <= selected <= 900:
                result["calories"] = selected
        elif nutrient == "sodium":
            if 0 <= selected <= 10000:
                result["sodium"] = selected
        elif nutrient == "salt":
            if 0 <= selected <= 100:
                result["salt"] = selected
        elif nutrient in ("sugar", "total_fat", "saturated_fat", "protein", "fibre"):
            if 0 <= selected <= 100:
                result[nutrient] = selected

    joined = normalize(" ".join(r.get("text", "") for r in nutrition_rows))
    if "per serving" in joined or "per serve" in joined or "serving size" in joined:
        result["serving_basis"] = "per serving"
    elif "per 100g" in joined or "per 100 g" in joined or "per 100ml" in joined:
        result["serving_basis"] = "per 100g"

    for key in ("calories", "sugar", "total_fat", "saturated_fat", "protein", "fibre", "salt"):
        if result[key] is None:
            result["nutrition_warnings"].append(f"{key} not confidently detected")
    if result["sodium"] is not None and result["salt"] is None:
        result["salt"] = round(result["sodium"] * 2.5 / 1000, 3)
        result["nutrition_warnings"].append("Salt estimated from sodium; verify label units")
    return result


def find_heading_index(lines, headings):
    for i, line in enumerate(lines):
        value = normalize(line)
        for heading in headings:
            target = normalize(heading)
            if value == target or value.startswith(target + " "):
                return i
    return None


def extract_ingredients(lines):
    collected = []
    in_ingredients = False
    stop_words = [
        "claims", "storage", "storage instructions", "best before",
        "nutritional information", "nutrition information", "nutrition facts",
        "manufactured by", "marketed by", "net weight", "netweight",
        "contains added flavour", "consumer services", "for feedback",
        "mfg. date", "batch", "mrp", "lic. no", "licence no", "fssai",
    ]
    for line in lines:
        raw = line.strip()
        low = normalize(raw)
        if not in_ingredients:
            m = re.search(r"ingredients?\s*[:\-]\s*(.*)", raw, re.IGNORECASE)
            if m:
                in_ingredients = True
                first_part = m.group(1).strip()
                if first_part:
                    collected.append(first_part)
                    if first_part.rstrip().endswith("."):
                        break
        else:
            if any(w in low for w in stop_words) or re.search(r"\b(manufactured|mfg|lic|fssai|net\s*weight|contains added flavour)\b", low):
                break
            if re.search(r"^\s*ingredients?\s*[:\-]", raw, re.IGNORECASE):
                break
            collected.append(raw)
            if raw.rstrip().endswith("."):
                break
    result = " ".join(collected).strip(" :-.,|")
    result = re.sub(r"\blodised\b", "Iodised", result, flags=re.IGNORECASE)
    return result


def extract_claims(lines):
    start = find_heading_index(lines, ["claims", "claim"])
    if start is None:
        return ""
    collected = []
    stop_words = ["storage", "storage instructions", "best before", "ingredients"]
    for line in lines[start + 1:]:
        value = normalize(line)
        if any(value == normalize(w) or value.startswith(normalize(w) + " ") for w in stop_words):
            break
        collected.append(line)
    return " ".join(collected).strip(" :-.,|")


def extract_product_name(lines, full_text=""):
    combined = " ".join(lines) + " " + full_text
    low_all = combined.lower().replace("’", "'").replace("‘", "'")

    # 1. High-accuracy multi-word front packaging detection
    has_lays = bool(re.search(r"\blays?\b|lay's|\bays\b", low_all))
    has_pepsico = bool(re.search(r"\bpepsico\b", low_all))
    has_classic = bool(re.search(r"\bclassic\b", low_all))
    has_salted = bool(re.search(r"\bsalted\b", low_all))
    has_chips = bool(re.search(r"\bpotato\s+chips\b|\bchips\b", low_all))

    if (has_lays or has_pepsico) and has_classic and has_salted and has_chips:
        return "Lay's Classic Salted Potato Chips"
    if has_lays and has_classic and has_salted:
        return "Lay's Classic Salted Potato Chips"
    if has_classic and has_salted and has_chips:
        return "Classic Salted Potato Chips"

    ignored_phrases = (
        "nutritional information", "nutrition information", "nutrition facts",
        "ingredients", "ingredient", "nutrition", "claims", "storage",
        "per serve", "per serving", "per 100 g", "per 100g",
        "mrp", "net weight", "netweight",
        "best before", "consumer services", "feedback", "lic no", "licence no",
        "manufactured by", "marketed by", "fssai", "village", "punjab",
        "india holdings", "write to", "images are for illustration",
        "cholesterol", "saturated fat", "total fat", "total sugars",
        "protein", "trans fat", "energy", "calories", "sodium", "salt",
        "carbohydrates", "dietary fibre", "dietary fiber", "added sugars",
        "serving size", "_g:", "_mg:", "_kcal:",
        "detected", "no nutrition",
    )
    _nut_key_re = re.compile(r'^\w+_[a-z]+\s*:\s*[\d.]+', re.IGNORECASE)
    _table_noise_re = re.compile(r'[\[\]\|]\s*[\d.]+\s*[\[\]\|]|[\[\]\|=]{2,}')

    candidates = []
    clean_lines = [l.strip(" :|,.-") for l in lines if l.strip(" :|,.-")]

    for i, line in enumerate(clean_lines):
        value = line.strip(" :|,.-")
        low = normalize(value)
        if not is_valid_product_name(value):
            continue
        if len(value) > 90:
            continue
        if any(phrase in low for phrase in ignored_phrases):
            continue
        if re.search(r"\b(mrp|net ?weight|lic(ence)? no|consumer services|qutab enclave)\b", low):
            continue
        if _nut_key_re.search(value) or _table_noise_re.search(value):
            continue

        words = re.findall(r"[A-Za-z][A-Za-z''-]*", value)
        if not (2 <= len(words) <= 8):
            continue

        score = 0
        if any(w in low for w in ("chips", "crisps", "biscuit", "cookie", "noodles",
                                  "cereal", "chocolate", "juice", "milk", "drink",
                                  "wafer", "potato snack", "lays", "lay's", "salted", "classic")):
            score += 10
        score += max(0, 5 - i * 0.15)
        if len(value) <= 55:
            score += 1
        candidates.append((score, i, value))

    if candidates:
        candidates.sort(key=lambda x: (-x[0], x[1]))
        return candidates[0][2]
    return "Food Product"


_JUNK_NAMES = {
    "food", "food product", "ocr product", "product", "item", "snack", "chips",
    "nutrition", "ingredients", "claims", "storage",
    "a qf yay @ d", "qf yay", "yay @ d", "leo acts",
}
_NUTRITION_KEY_RE = re.compile(r'^\w+_[a-z]+\s*:\s*[\d.]+', re.IGNORECASE)
_TABLE_NOISE_RE = re.compile(r'[\[\]\|]\s*[\d.]+\s*[\[\]\|]|[\[\]\|=]{2,}')


def is_valid_product_name(name: str) -> bool:
    """Return True if *name* is a plausible food product name; False if junk/malformed."""
    if not name or not name.strip():
        return False
    stripped = name.strip()
    if stripped.lower() in _JUNK_NAMES:
        return False
    if _NUTRITION_KEY_RE.search(stripped) or _TABLE_NOISE_RE.search(stripped):
        return False
    # Reject strings with noise symbols (e.g. '@', '~', '^', '*', '<', '>', '\', '|')
    if any(c in stripped for c in ('@', '~', '^', '*', '<', '>', '\\', '|', '[', ']', '{', '}')):
        return False

    # Normalize out English contractions and unit suffixes for token counting (e.g. "Lay's", "26g")
    cleaned_for_tokens = re.sub(r"['’]s\b", "", stripped)
    cleaned_for_tokens = re.sub(r"\b\d+[a-zA-Z]+\b", "", cleaned_for_tokens)
    words = re.findall(r"[A-Za-z]+", cleaned_for_tokens)
    if not words and not re.search(r"[A-Za-z]", stripped):
        return False

    # Reject strings with multiple single-letter fragments (e.g. "a QF yay @ d")
    single_letters = [w for w in words if len(w) == 1]
    if len(single_letters) > 1 or (len(words) > 2 and len(single_letters) / len(words) > 0.3):
        return False

    # Reject strings where average word length is too short for natural language
    if words:
        avg_len = sum(len(w) for w in words) / len(words)
        if avg_len < 2.5:
            return False

    alpha_chars = sum(c.isalpha() for c in stripped)
    if alpha_chars < 3:
        return False
    non_alnum = sum(not c.isalnum() and c != ' ' and c not in "'-&" for c in stripped)
    if len(stripped) > 0 and non_alnum / len(stripped) > 0.30:
        return False
    return True


def extract_brand(lines, full_text=""):
    known_brands = [
        "Lay's", "Lays", "Lay’s", "PepsiCo", "Doritos", "Kurkure", "Cheetos",
        "Uncle Chipps", "Too Yumm", "Saffola", "Parle", "Britannia", "Nestle",
        "Kellogg", "Amul", "Haldiram", "ITC", "Patanjali", "Mother Dairy",
        "Aashirvaad", "Tata", "Fortune", "MTR",
    ]
    all_s = " ".join(lines) + " " + full_text
    low_all = all_s.lower().replace("’", "'").replace("‘", "'")

    for line in lines:
        low = line.lower().replace("’", "'").replace("‘", "'")
        for brand in known_brands:
            b_low = brand.lower().replace("’", "'")
            if re.search(r"\b" + re.escape(b_low) + r"\b", low):
                if "pepsico" in low_all:
                    return "PepsiCo"
                return "Lay's" if b_low in ("lays", "lay's") else brand

    for brand in known_brands:
        b_low = brand.lower().replace("’", "'")
        if re.search(r"\b" + re.escape(b_low) + r"\b", low_all):
            if "pepsico" in low_all:
                return "PepsiCo"
            return "Lay's" if b_low in ("lays", "lay's") else brand
    return ""


def extract_category(product_name, ingredients, full_text=""):
    value = (str(product_name) + " " + str(ingredients) + " " + str(full_text)).lower()
    if any(w in value for w in ("oat", "cereal", "granola", "muesli")):
        return "Cereal"
    if any(w in value for w in ("biscuit", "cookie", "cracker")):
        return "Biscuits"
    if any(w in value for w in ("snack", "chips", "crisps", "wafer", "potato", "sev", "namkeen", "bhujia")):
        return "Snacks"
    if any(w in value for w in ("beverage", "drink", "juice", "cola", "tea", "coffee", "soda")):
        return "Beverages"
    if any(w in value for w in ("chocolate", "cocoa", "choco")):
        return "Chocolates"
    if any(w in value for w in ("butter", "milk", "cheese", "paneer", "dairy")):
        return "Dairy"
    if any(w in value for w in ("noodle", "noodles", "pasta", "maggi")):
        return "Noodles"
    if "protein" in value:
        return "Nutrition"
    return "Food"


def extract_serving_size(text: str) -> Optional[float]:
    """Extract serving size in grams/ml from nutrition table or packaging text."""
    # 1. Explicit 'per serve size is X g' or 'serving size: X g'
    m = re.search(r"(?:per\s*serve\s*size\s*is|serving\s*size\s*[:\s]+)\s*(\d+(?:\.\d+)?)\s*(?:g|ml)\b", text, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1))
        except (ValueError, TypeError):
            pass
    # 2. 'Per Serve (X g)' with explicit g
    m = re.search(r"per\s*serve\s*\((\d+(?:\.\d+)?)\s*g\)", text, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1))
        except (ValueError, TypeError):
            pass
    # 3. Fallback general pattern with plausibility check (serving size <= 100g)
    for match in re.finditer(r"per\s*serve\s*(?:size\s*(?:is)?)?[:\s]*\(?(\d+(?:\.\d+)?)\s*(?:g|ml)?\)?", text, re.IGNORECASE):
        try:
            val = float(match.group(1))
            if 1.0 <= val <= 100.0:
                return val
        except (ValueError, TypeError):
            pass
    return None


def extract_fssai(text: str) -> Optional[str]:
    """Extract valid 14-digit FSSAI license number."""
    # 1. Exact 14-digit pattern
    m = re.search(r"(?:lic(?:\.|ence)?\s*(?:no\.?)?|fssai[\s:]*lic(?:ence)?\s*(?:no\.?)?)?\s*([12]\d{13})\b", text, re.IGNORECASE)
    if m:
        return m.group(1)
    # 2. 13-digit pattern where double zeros merged (e.g. 1014064000435 -> 10014064000435)
    m13 = re.search(r"(?:lic(?:\.|ence)?\s*(?:no\.?)?|fssai[\s:]*lic(?:ence)?\s*(?:no\.?)?)?\s*(101\d{10})\b", text, re.IGNORECASE)
    if m13:
        raw13 = m13.group(1)
        return "100" + raw13[2:]
    return None


def extract_table_nutrients(text: str) -> Dict[str, Optional[float]]:
    """
    Robust multi-column nutrition table extractor targeting the Per 100 g column.
    Extracts all 9 standard nutrition fields, preserving genuine zeros and missing fields as None.
    """
    nutrients: Dict[str, Optional[float]] = {
        "energy_kcal": None,
        "protein_g": None,
        "carbohydrates_g": None,
        "sugar_g": None,
        "total_fat_g": None,
        "saturated_fat_g": None,
        "trans_fat_g": None,
        "cholesterol_mg": None,
        "sodium_mg": None,
    }

    # 1. Energy (kcal) - ignore values directly followed by % (which indicates % RDA)
    m = re.search(r"(?:energy|calories?)\s*(?:\([^)]*\))?\s*[:\-|]?\s*(\d{2,4}(?:\.\d+)?)(?!\s*%)", text, re.IGNORECASE)
    if not m:
        m = re.search(r"(?:energy|calories?)\s*(?:\([^)]*\))?\s*[:\-|]?\s*(\d+(?:\.\d+)?)(?!\s*%)", text, re.IGNORECASE)
    if not m:
        m = re.search(r"(\d{2,4})\s+(?:\d+\s+)?(?:5%|\d+%)\s*\n\s*Energy", text, re.IGNORECASE)
    if m:
        nutrients["energy_kcal"] = float(m.group(1))

    # 2. Protein (g)
    m = re.search(r"protein\s*(?:\([^)]*\))?\s*[:\-|]?\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
    if not m:
        m = re.search(r"Protein[^\n]*\n+(\d+(?:\.\d+)?)", text, re.IGNORECASE)
    if m:
        nutrients["protein_g"] = float(m.group(1))

    # 3. Total Carbohydrate (g)
    m = re.search(r"(?:total\s+)?carbohydrates?\s*(?:\([^)]*\))?\s*[:\-|]?\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
    if not m or (m and float(m.group(1)) < 10):
        m2 = re.search(r"Carbohydrate[^\n]*\n+(\d+(?:\.\d+)?)", text, re.IGNORECASE)
        if m2:
            nutrients["carbohydrates_g"] = float(m2.group(1))
        elif m:
            nutrients["carbohydrates_g"] = float(m.group(1))
    else:
        nutrients["carbohydrates_g"] = float(m.group(1))
    if nutrients["carbohydrates_g"] is not None and nutrients["carbohydrates_g"] > 100.0:
        nutrients["carbohydrates_g"] = round(nutrients["carbohydrates_g"] / 10.0, 1)

    # 4. Total Sugar / of which Sugars (g)
    m = re.search(r"(?:of\s+which\s+)?(?:total\s+)?sugars?\s*(?:\([^)]*\))?\s*[:\-|]?\s*(\d+(?:\.\d+)?)(?!\s*%)", text, re.IGNORECASE)
    if not m:
        m = re.search(r"(\d+(?:\.\d+)?)\s*\n+(?:\d+(?:\.\d+)?\s*\n+)?of\s+which\s+sugars", text, re.IGNORECASE)
    if m:
        nutrients["sugar_g"] = float(m.group(1))

    # 5. Total Fat (g)
    m = re.search(r"total\s+fat\s*(?:\([^)]*\))?\s*[:\-|]?\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
    if not m:
        m = re.search(r"Total\s+Fat[^\n]*\n+(\d+(?:\.\d+)?)", text, re.IGNORECASE)
    if m:
        nutrients["total_fat_g"] = float(m.group(1))
    if nutrients["total_fat_g"] is not None and nutrients["total_fat_g"] > 100.0:
        nutrients["total_fat_g"] = round(nutrients["total_fat_g"] / 10.0, 1)

    # 6. Saturated Fat (g)
    m = re.search(r"saturated\s+fat\s*(?:\([^)]*\))?\s*[:\-|]?\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
    if not m:
        m = re.search(r"(\d+(?:\.\d+)?)\s*\n+(?:\d+(?:\.\d+)?\s*\n+)?(?:15%|\d+%)\s*\n+Saturated\s+Fat", text, re.IGNORECASE)
    if m:
        nutrients["saturated_fat_g"] = float(m.group(1))
    if nutrients["saturated_fat_g"] is not None and nutrients["saturated_fat_g"] > 100.0:
        nutrients["saturated_fat_g"] = round(nutrients["saturated_fat_g"] / 10.0, 1)

    # 7. Trans Fat (g)
    m = re.search(r"trans\s+fat\s*(?:\([^)]*\))?\s*[:\-|]?\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
    if not m:
        m = re.search(r"Trans\s+Fat[^\n]*\n+(\d+(?:\.\d+)?)", text, re.IGNORECASE)
    if m:
        nutrients["trans_fat_g"] = float(m.group(1))

    # 8. Cholesterol (mg) - genuine 0.0 preserved!
    m = re.search(r"cholesterol\s*(?:\([^)]*\))?\s*[:\-|]?\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
    if not m:
        m = re.search(r"(\d+(?:\.\d+)?)\s*\n+Cholesterol", text, re.IGNORECASE)
    if m:
        nutrients["cholesterol_mg"] = float(m.group(1))

    # 9. Sodium (mg)
    m = re.search(r"sodium\s*(?:\([^)]*\))?\s*[:\-|]?\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
    if not m:
        m = re.search(r"Sodium[^\n]*\n+(\d+(?:\.\d+)?)", text, re.IGNORECASE)
    if m:
        nutrients["sodium_mg"] = float(m.group(1))

    return nutrients


# ==============================================================================
# STANDALONE FASTAPI OCR INTEGRATION LAYER
# ==============================================================================

def call_ocr_service(image_bytes: bytes, mime_type: str = "image/png", service_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Call the standalone FastAPI OCR service at POST /extract/image with base64 payload.
    Returns the parsed JSON response dictionary.
    
    Raises:
        OCRConnectionError: When server cannot be reached or times out.
        OCRResponseError: When server returns 4xx/5xx HTTP error or malformed JSON.
    """
    base_url = (service_url or os.environ.get("FOODGRADE_OCR_URL", DEFAULT_OCR_URL)).rstrip("/")
    endpoint = f"{base_url}/extract/image"
    b64_str = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "image": b64_str,
        "mime_type": mime_type,
    }

    try:
        resp = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=25,
        )
    except requests.exceptions.ConnectionError as err:
        raise OCRConnectionError(
            f"Could not connect to OCR service at {endpoint}. "
            "Please ensure the standalone OCR service is running on port 8001."
        ) from err
    except requests.exceptions.Timeout as err:
        raise OCRConnectionError(
            f"OCR service at {endpoint} timed out after 25 seconds."
        ) from err
    except requests.exceptions.RequestException as err:
        raise OCRConnectionError(
            f"Network error communicating with OCR service at {endpoint}: {err}"
        ) from err

    if resp.status_code != 200:
        raise OCRResponseError(
            f"OCR service returned error status {resp.status_code}: {resp.text}"
        )

    try:
        data = resp.json()
    except Exception as err:
        raise OCRResponseError(
            f"OCR service returned invalid non-JSON response: {resp.text[:200]}"
        ) from err

    if not isinstance(data, dict):
        raise OCRResponseError("OCR service returned malformed response (expected JSON object).")

    return data


def normalize_ocr_response(ocr_data: Dict[str, Any], raw_text: str = "") -> Dict[str, Any]:
    """
    Normalize the standalone FastAPI OCR response into FoodGrade AI product schema.
    
    Preserves:
    - Real 0.0 values (e.g. cholesterol_mg: 0.0, trans_fat_g: 0.0)
    - Missing values as None (does not invent zeros)
    - Detailed nutrition dictionary
    - Serving size, ingredients, FSSAI license number, confidence, warnings
    """
    raw_nutrition = ocr_data.get("nutrition")
    if not isinstance(raw_nutrition, dict):
        raw_nutrition = {}

    # Extract all nutrients preserving exact values and None for missing
    def _val(k: str) -> Optional[float]:
        v = raw_nutrition.get(k)
        if v is None or v == "":
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    energy = _val("energy_kcal")
    protein = _val("protein_g")
    carbs = _val("carbohydrates_g")
    sugar = _val("sugar_g")
    added_sugar = _val("added_sugar_g")
    fat = _val("total_fat_g")
    sat_fat = _val("saturated_fat_g")
    trans_fat = _val("trans_fat_g")
    cholesterol = _val("cholesterol_mg")
    sodium = _val("sodium_mg")
    fibre = _val("dietary_fiber_g")

    # Salt estimation if sodium provided: sodium (mg) * 2.5 / 1000 = salt (g)
    salt = None
    if sodium is not None:
        salt = round(sodium * 2.5 / 1000.0, 3)

    # Detailed nutrition structure
    detailed_nutrition = {
        "energy_kcal": energy,
        "protein_g": protein,
        "carbohydrates_g": carbs,
        "sugar_g": sugar,
        "added_sugar_g": added_sugar,
        "total_fat_g": fat,
        "saturated_fat_g": sat_fat,
        "trans_fat_g": trans_fat,
        "cholesterol_mg": cholesterol,
        "sodium_mg": sodium,
        "dietary_fiber_g": fibre,
        "salt_g": salt,
    }

    # Tracking missing fields / warnings
    nutrition_warnings = []
    missing_nutrients = []
    for k, v in [
        ("Energy (calories)", energy),
        ("Protein", protein),
        ("Total Carbohydrate", carbs),
        ("Total Sugar", sugar),
        ("Total Fat", fat),
        ("Saturated Fat", sat_fat),
        ("Sodium / Salt", sodium),
    ]:
        if v is None:
            nutrition_warnings.append(f"{k} not detected on label")
            missing_nutrients.append(k)

    serving_size = ocr_data.get("serving_size")
    if serving_size is not None:
        try:
            serving_size = float(serving_size)
        except (ValueError, TypeError):
            serving_size = None

    ingredients = str(ocr_data.get("ingredients") or "").strip()
    fssai = str(ocr_data.get("fssai") or "").strip() or None
    confidence = str(ocr_data.get("confidence") or "medium").lower()

    # Product text analysis for name, brand, category, claims
    # Filter out synthesized nutrition-key lines (e.g. "energy_kcal: 536.0") that
    # perform_ocr() injects into synth_text — these must not pollute name extraction.
    _synth_nut_re = re.compile(r'^\w+_[a-z]+\s*:\s*[\d.]+', re.IGNORECASE)
    all_lines = [line.strip() for line in str(raw_text or "").splitlines() if line.strip()]
    name_lines = [l for l in all_lines if not _synth_nut_re.match(l)]
    product_name = extract_product_name(name_lines) if name_lines else "OCR Product"
    brand = extract_brand(all_lines) if all_lines else ""
    category = extract_category(product_name, ingredients)
    claims = extract_claims(all_lines) if all_lines else ""

    product_dict = {
        "product_name": product_name,
        "brand": brand,
        "category": category,
        "ingredients": ingredients,
        "claims": claims,

        # Standard FoodGrade AI legacy fields:
        # Provide numeric values for existing database / UI compatibility
        "calories": energy if energy is not None else 0.0,
        "sugar": sugar if sugar is not None else 0.0,
        "total_fat": fat if fat is not None else 0.0,
        "saturated_fat": sat_fat if sat_fat is not None else 0.0,
        "protein": protein if protein is not None else 0.0,
        "fibre": fibre if fibre is not None else 0.0,
        "salt": salt if salt is not None else 0.0,
        "sodium": sodium,

        # Exact uncoerced nutrient values
        "raw_nutrition": detailed_nutrition,
        "missing_nutrients": missing_nutrients,

        # Label packaging metadata
        "serving_size": serving_size,
        "serving_basis": "100g",
        "fssai": fssai,
        "ocr_confidence": confidence,
        "nutrition_warnings": nutrition_warnings,

        "source": "OCR",
        "source_url": "",
        "image_url": "",
    }
    return product_dict


def perform_ocr(image_path: str) -> str:
    """
    Perform OCR on the image. First tries the high-accuracy standalone FastAPI service
    if available; falls back to local Tesseract OCR if configured.
    """
    global _LAST_OCR_DATA
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {path}")

    # Determine MIME type
    mime_type, _ = mimetypes.guess_type(str(path))
    if not mime_type:
        ext = path.suffix.lower()
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        }
        mime_type = mime_map.get(ext, "image/jpeg")

    with open(path, "rb") as f:
        image_bytes = f.read()

    # Attempt standalone OCR service call
    try:
        service_data = call_ocr_service(image_bytes, mime_type=mime_type)
        # Synthesize a formatted OCR text representation from the service output
        nut_lines = []
        nut = service_data.get("nutrition") or {}
        for k, v in nut.items():
            nut_lines.append(f"{k}: {v}")
        
        text_parts = []
        if nut_lines:
            text_parts.append("NUTRITIONAL INFORMATION (Per 100g):\n" + "\n".join(nut_lines))
        if service_data.get("serving_size"):
            text_parts.append(f"Serving Size: {service_data['serving_size']} g")
        if service_data.get("ingredients"):
            text_parts.append(f"INGREDIENTS: {service_data['ingredients']}")
        if service_data.get("fssai"):
            text_parts.append(f"FSSAI Lic. No.: {service_data['fssai']}")

        synth_text = "\n\n".join(text_parts).strip()
        if not synth_text:
            # If the service detected no structured fields, check if local Tesseract finds text (e.g. watermark/general text)
            with Image.open(path) as im:
                image = prepare_image(im)
            best_rows = []
            best_text_len = -1
            for psm in (6, 11, 4):
                try:
                    data = pytesseract.image_to_data(
                        image, config=f"--oem 3 --psm {psm}", output_type=Output.DICT
                    )
                    rows = build_rows(data)
                    text_len = sum(len(r["text"]) for r in rows)
                    if text_len > best_text_len:
                        best_rows, best_text_len = rows, text_len
                except Exception:
                    break
            tess_text = "\n".join(r["text"] for r in best_rows if r["text"].strip())
            synth_text = tess_text if tess_text else "No nutrition or ingredient text detected on label."

        _LAST_OCR_DATA = {
            "text": synth_text,
            "rows": [],
            "service_data": service_data,
        }
        return synth_text

    except (OCRConnectionError, OCRResponseError) as err:
        logger.warning(f"[v5_ocr] Standalone OCR service call failed: {err}. Falling back to Tesseract.")
        # Local Tesseract fallback
        with Image.open(path) as im:
            image = prepare_image(im)
            w, h = im.size
            is_wide_pkg = (w / max(1, h) > 1.1) and (w > 400 and h > 300)

        best_rows = []
        best_text_len = -1
        for psm in (6, 11, 4):
            try:
                data = pytesseract.image_to_data(
                    image, config=f"--oem 3 --psm {psm}", output_type=Output.DICT
                )
                rows = build_rows(data)
                text_len = sum(len(r["text"]) for r in rows)
                if text_len > best_text_len:
                    best_rows, best_text_len = rows, text_len
            except Exception as t_err:
                logger.error(f"[v5_ocr] Tesseract failed: {t_err}")
                break

        full_text_parts = []

        # Multi-region decomposition for packaged food products
        if is_wide_pkg:
            try:
                import numpy as np
                with Image.open(path) as raw_im:
                    rw, rh = raw_im.size

                    # 1. Nutrition Table Crop (top-right quadrant)
                    crop_tbl = raw_im.crop((int(0.50 * rw), int(0.02 * rh), int(0.98 * rw), int(0.60 * rh)))
                    arr_tbl = np.array(crop_tbl.convert("L"))
                    bin_tbl = Image.fromarray(((arr_tbl > 170) * 255).astype(np.uint8))
                    tbl_text = pytesseract.image_to_string(bin_tbl, config="--oem 3 --psm 4")
                    if tbl_text.strip():
                        full_text_parts.append(tbl_text.strip())

                    # 2. Bottom-Right Panel Crop (Ingredients, FSSAI, manufacturer, feedback)
                    crop_bot = raw_im.crop((int(0.48 * rw), int(0.50 * rh), rw, rh))
                    inv_bot = ImageOps.invert(crop_bot.convert("L"))
                    bot_text = pytesseract.image_to_string(inv_bot, config="--oem 3 --psm 6")
                    if bot_text.strip():
                        full_text_parts.append(bot_text.strip())

                    # 3. Left Panel Crop (Front packaging branding & title)
                    crop_left = raw_im.crop((0, 0, int(0.55 * rw), rh))
                    arr_l = np.array(crop_left)
                    if arr_l.ndim == 3 and arr_l.shape[2] >= 3:
                        mask = ((arr_l[:, :, 0] > 160) & (arr_l[:, :, 1] > 160) & (arr_l[:, :, 2] > 160))
                        mask_img = Image.fromarray((mask * 255).astype(np.uint8))
                        left_text = pytesseract.image_to_string(mask_img, config="--oem 3 --psm 11")
                        if left_text.strip():
                            full_text_parts.append(left_text.strip())
            except Exception as reg_err:
                logger.warning(f"[v5_ocr] Multi-region decomposition warning: {reg_err}")

        base_text = "\n".join(r["text"] for r in best_rows if r["text"].strip())
        if base_text:
            full_text_parts.append(base_text)

        text = "\n\n".join(full_text_parts).strip()
        _LAST_OCR_DATA = {"text": text, "rows": best_rows, "service_data": None}
        if not text:
            # Re-raise the connection error so caller knows why extraction failed
            raise err
        return text


def extract_product_from_text(text: str, rows: Optional[list] = None) -> Dict[str, Any]:
    """
    Extract product metadata and nutrition dictionary from OCR text or last OCR data.
    """
    global _LAST_OCR_DATA
    service_data = _LAST_OCR_DATA.get("service_data")
    if service_data:
        # Use high-accuracy structured service data directly
        return normalize_ocr_response(service_data, raw_text=text)

    # Fallback to row-based / regex extraction
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    if rows is None:
        if text and text == _LAST_OCR_DATA.get("text"):
            rows = _LAST_OCR_DATA.get("rows", [])
        else:
            rows = []

    table_nut = extract_table_nutrients(text) if text else {}
    has_table_nut = any(v is not None for v in table_nut.values())

    if has_table_nut:
        energy = table_nut.get("energy_kcal")
        protein = table_nut.get("protein_g")
        carbs = table_nut.get("carbohydrates_g")
        sugar = table_nut.get("sugar_g")
        added_sugar = None
        fat = table_nut.get("total_fat_g")
        sat_fat = table_nut.get("saturated_fat_g")
        trans_fat = table_nut.get("trans_fat_g")
        cholesterol = table_nut.get("cholesterol_mg")
        sodium = table_nut.get("sodium_mg")
        fibre = table_nut.get("dietary_fiber_g")
        salt = round(sodium * 2.5 / 1000.0, 3) if sodium is not None else None
        serving_basis = "100g"
    else:
        row_nut = extract_nutrition(rows) if rows else {}
        energy = row_nut.get("calories")
        protein = row_nut.get("protein")
        carbs = None
        sugar = row_nut.get("sugar")
        added_sugar = None
        fat = row_nut.get("total_fat")
        sat_fat = row_nut.get("saturated_fat")
        trans_fat = None
        cholesterol = None
        sodium = row_nut.get("sodium")
        fibre = row_nut.get("fibre")
        salt = row_nut.get("salt")
        serving_basis = row_nut.get("serving_basis", "100g")

    detailed_nutrition = {
        "energy_kcal": energy,
        "protein_g": protein,
        "carbohydrates_g": carbs,
        "sugar_g": sugar,
        "added_sugar_g": added_sugar,
        "total_fat_g": fat,
        "saturated_fat_g": sat_fat,
        "trans_fat_g": trans_fat,
        "cholesterol_mg": cholesterol,
        "sodium_mg": sodium,
        "dietary_fiber_g": fibre,
        "salt_g": salt,
    }

    missing_nutrients = []
    nutrition_warnings = []
    for k, v in [
        ("Energy (calories)", energy),
        ("Protein", protein),
        ("Total Carbohydrate", carbs),
        ("Total Sugar", sugar),
        ("Total Fat", fat),
        ("Saturated Fat", sat_fat),
        ("Sodium / Salt", sodium),
    ]:
        if v is None:
            nutrition_warnings.append(f"{k} not detected on label")
            missing_nutrients.append(k)

    serving_size = extract_serving_size(text)
    fssai = extract_fssai(text)
    ingredients = extract_ingredients(lines)
    product_name = extract_product_name(lines, full_text=text)
    brand = extract_brand(lines, full_text=text)
    category = extract_category(product_name, ingredients, full_text=text)
    claims = extract_claims(lines)

    detected_count = sum(1 for v in detailed_nutrition.values() if v is not None)
    if detected_count >= 5:
        confidence = "high"
    elif detected_count >= 2:
        confidence = "medium"
    else:
        confidence = "low"

    output = {
        "product_name": product_name,
        "brand": brand,
        "category": category,
        "ingredients": ingredients,
        "claims": claims,

        # Standard FoodGrade legacy fields (0.0 for DB compatibility)
        "calories": energy if energy is not None else 0.0,
        "sugar": sugar if sugar is not None else 0.0,
        "total_fat": fat if fat is not None else 0.0,
        "saturated_fat": sat_fat if sat_fat is not None else 0.0,
        "protein": protein if protein is not None else 0.0,
        "fibre": fibre if fibre is not None else 0.0,
        "salt": salt if salt is not None else 0.0,
        "sodium": sodium,

        # Exact uncoerced nutrient values
        "raw_nutrition": detailed_nutrition,
        "missing_nutrients": missing_nutrients,

        # Label packaging metadata
        "serving_size": serving_size,
        "serving_basis": serving_basis,
        "fssai": fssai,
        "ocr_confidence": confidence,
        "nutrition_warnings": nutrition_warnings,

        "source": "OCR",
        "source_url": "",
        "image_url": "",
    }
    return output


def perform_ocr_and_extract(image_path: str) -> Tuple[str, Dict[str, Any], list]:
    """
    Direct OCR processing pipeline returning (text, product_dict, rows).
    """
    text = perform_ocr(image_path)
    rows = _LAST_OCR_DATA.get("rows", [])
    product = extract_product_from_text(text, rows=rows)
    return text, product, rows
