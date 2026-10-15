"""
FoodGrade AI — Core Grading & Verification Engine
Version: FoodGrade V2.5 Methodology Implementation (Enhanced)

Produces two independent, unmerged evaluations aligned with FSSAI standards:
1. Health Grade (A–E) & Health Score (0–100):
   A transparent nutrition-profile score based on six dimensions:
   - Total sugar: 20% (Lower is better; beverage vs solid thresholds)
   - Saturated fat: 20% (Lower is better)
   - Sodium/salt: 20% (Lower is better)
   - Energy: 10% (Lower is preferable; beverage vs solid scaling)
   - Dietary fibre: 15% (Higher is better)
   - Protein: 15% (Higher is better)
   Reference bands:
     85–100: A
     70–84.99: B
     55–69.99: C
     40–54.99: D
     0–39.99: E

2. Claim Verification & FSSAI Verification Status:
   Evaluated against FSSAI Food Safety and Standards (Advertising and Claims) Regulations, 2018.
   Claim statuses:
   - VERIFIED: product data satisfies applicable FSSAI criterion (Label: "Verified Claim")
   - NOT_VERIFIED: product data does not satisfy criterion (Label: "Not Verified")
   - INSUFFICIENT_EVIDENCE: required nutrition/ingredient information is missing (Label: "Insufficient Evidence")
   - CLAIM_DETECTED_UNVERIFIED: claim detected in source text, unverified / non-statutory (Label: "Claim Detected — Unverified")
   - NO_CLAIMS_DETECTED: packaging assessed and no claims found (Label: "No Claim Detected")
   - NOT_ASSESSED: product has not undergone claim assessment (Label: "Not Assessed")

3. Dynamic Data Completeness & Confidence Scoring:
   - Missing information is NOT silently converted into zero.
   - Genuine zero values are preserved.
   - Distinguishes per-serving from per-100g/per-100ml.
   - Energy kJ/kcal and sodium/salt normalization.
   - Explicit "INSUFFICIENT_DATA" status when essential nutrition data is missing.
"""

from __future__ import annotations

import math
import re
from typing import Any

from services.v3_extractor import extract_claims as v3_extract_claims
from services.v3_nlp import normalize_claim as v3_normalize_claim


# ============================================================
# HELPER FUNCTIONS & THRESHOLDS
# ============================================================

def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    """Clamp value between low and high bounds."""
    return max(low, min(high, float(value)))


def grade_from_score(score: float | None, is_claim: bool = False) -> str:
    """
    Convert a 0–100 score into an A–E grade band according to
    FoodGrade V2.5 methodology.
    """
    if score is None:
        return "Insufficient Data"
    score = float(score)
    if is_claim:
        # Section 5: Claim Grade Bands
        if score >= 90.0:
            return "A"
        if score >= 75.0:
            return "B"
        if score >= 50.0:
            return "C"
        if score >= 25.0:
            return "D"
        return "E"
    else:
        # Section 6: Health Grade Bands
        if score >= 85.0:
            return "A"
        if score >= 70.0:
            return "B"
        if score >= 55.0:
            return "C"
        if score >= 40.0:
            return "D"
        return "E"


def _safe_float(val: Any) -> float | None:
    """
    Return float value or None if missing, unparseable, negative, or non-finite.
    Preserves genuine zero (0.0). Does NOT silently turn negatives into zero.
    """
    if val is None or val == "":
        return None
    try:
        f = float(val)
    except (ValueError, TypeError):
        if isinstance(val, str):
            # Clean common unit suffixes (g, ml, mg, kcal, kj)
            cleaned = re.sub(r"[^\d.\-+]", "", val).strip()
            try:
                f = float(cleaned)
            except (ValueError, TypeError):
                return None
        else:
            return None
    if not math.isfinite(f) or f < 0:
        return None
    return f


def _to_dict(product: Any) -> dict[str, Any]:
    """Ensure product mapping is accessible as a standard Python dictionary."""
    if isinstance(product, dict):
        return product
    if hasattr(product, "keys"):
        return {k: product[k] for k in product.keys()}
    return dict(product)


def is_beverage_category(category: str | None) -> bool:
    """Check if product category indicates a liquid beverage."""
    if not category:
        return False
    cat = str(category).lower()
    beverage_keywords = [
        "beverage", "drink", "juice", "soda", "water", "tea", "coffee",
        "syrup", "squash", "cola", "nectar", "energy drink"
    ]
    return any(kw in cat for kw in beverage_keywords)


# ============================================================
# NUTRITION NORMALIZATION & UNIT CONVERSION (Step 1.2)
# ============================================================

def normalize_nutrition(product: dict[str, Any]) -> tuple[dict[str, float | None], list[str], list[str]]:
    """
    Standardize nutrition declarations to per-100g / per-100ml basis:
    - Normalizes per-serving to per-100g/ml if serving_basis indicates per-serving.
    - Converts energy kJ to kcal if calories missing.
    - Estimates salt from sodium if salt missing (salt = sodium * 2.5).
    - Validates values against physical bounds and physiological limits.
    - Distinguishes missing values (None) from genuine zeros (0.0).

    Returns:
        (normalized_nutrients, missing_fields, validation_warnings)
    """
    product = _to_dict(product)
    norm: dict[str, float | None] = {}
    missing_fields: list[str] = []
    val_warnings: list[str] = []

    # Serving basis scaling
    serving_basis = str(product.get("serving_basis") or product.get("basis") or "").lower().strip()
    serving_size = _safe_float(product.get("serving_size"))
    is_per_serving = (
        bool(product.get("is_per_serving"))
        or ("serving" in serving_basis or "serve" in serving_basis)
        or (serving_size is not None and "100" not in serving_basis)
    )

    scale = 1.0
    if is_per_serving:
        if serving_size and serving_size > 0:
            scale = 100.0 / serving_size
            val_warnings.append(
                f"Declared values scaled from per-serving ({serving_size}g/ml) to 100g/ml basis (scale factor: {round(scale, 2)}x)."
            )
        else:
            val_warnings.append(
                "Serving basis specified as per-serving, but serving size was missing; raw declared values utilized."
            )

    # Check for raw_nutrition dict to preserve uncoerced None values from OCR
    raw_nut = product.get("raw_nutrition")
    has_raw = isinstance(raw_nut, dict) and bool(raw_nut)

    # 1. Calories / Energy
    if has_raw and "energy_kcal" in raw_nut:
        raw_cal = _safe_float(raw_nut.get("energy_kcal"))
    else:
        raw_cal = _safe_float(product.get("calories"))
    raw_kj = _safe_float(product.get("energy_kj") or product.get("calories_kj") or product.get("energy-kj_100g"))

    if raw_cal is not None:
        cal_val = raw_cal * scale
        if raw_kj is not None:
            expected_kcal = (raw_kj * scale) / 4.184
            if abs(cal_val - expected_kcal) > max(30.0, expected_kcal * 0.20):
                val_warnings.append(
                    f"Declared energy ({round(cal_val, 1)} kcal) and kJ ({round(raw_kj * scale, 1)} kJ) exhibit significant discrepancy."
                )
    elif raw_kj is not None:
        cal_val = round((raw_kj * scale) / 4.184, 1)
        val_warnings.append(f"Calories derived from declared energy kJ ({round(raw_kj, 1)} kJ -> {cal_val} kcal).")
    else:
        cal_val = None

    if cal_val is not None:
        if cal_val > 950.0:
            val_warnings.append(f"Declared energy ({round(cal_val, 1)} kcal/100g) exceeds physical limit (950 kcal/100g); flagged as implausible.")
            cal_val = None
        else:
            norm["calories"] = round(cal_val, 1)
    else:
        norm["calories"] = None
        missing_fields.append("energy / calories")

    # 2. Total Sugar
    if has_raw and "sugar_g" in raw_nut:
        raw_sugar = _safe_float(raw_nut.get("sugar_g"))
    else:
        raw_sugar = _safe_float(product.get("sugar"))
    if raw_sugar is not None:
        sugar_val = raw_sugar * scale
        if sugar_val > 100.0:
            val_warnings.append(f"Declared sugar ({round(sugar_val, 1)}g/100g) exceeds 100g; flagged as implausible.")
            norm["sugar"] = None
            missing_fields.append("total sugar")
        else:
            norm["sugar"] = round(sugar_val, 2)
    else:
        norm["sugar"] = None
        missing_fields.append("total sugar")

    # 3. Total Fat
    if has_raw and "total_fat_g" in raw_nut:
        raw_tfat = _safe_float(raw_nut.get("total_fat_g"))
    else:
        raw_tfat = _safe_float(product.get("total_fat"))
    if raw_tfat is not None:
        tfat_val = raw_tfat * scale
        if tfat_val > 100.0:
            val_warnings.append(f"Declared total fat ({round(tfat_val, 1)}g/100g) exceeds 100g; flagged as implausible.")
            norm["total_fat"] = None
            missing_fields.append("total fat")
        else:
            norm["total_fat"] = round(tfat_val, 2)
    else:
        norm["total_fat"] = None
        missing_fields.append("total fat")

    # 4. Saturated Fat
    if has_raw and "saturated_fat_g" in raw_nut:
        raw_sat = _safe_float(raw_nut.get("saturated_fat_g"))
    else:
        raw_sat = _safe_float(product.get("saturated_fat"))
    if raw_sat is not None:
        sat_val = raw_sat * scale
        if sat_val > 100.0:
            val_warnings.append(f"Declared saturated fat ({round(sat_val, 1)}g/100g) exceeds 100g; flagged as implausible.")
            norm["saturated_fat"] = None
            missing_fields.append("saturated fat")
        elif norm.get("total_fat") is not None and sat_val > (norm["total_fat"] + 0.5):
            val_warnings.append(f"Saturated fat ({round(sat_val, 1)}g) exceeds declared total fat ({round(norm['total_fat'], 1)}g); data inconsistency flagged.")
            norm["saturated_fat"] = round(sat_val, 2)
        else:
            norm["saturated_fat"] = round(sat_val, 2)
    else:
        norm["saturated_fat"] = None
        missing_fields.append("saturated fat")

    # 5. Protein
    if has_raw and "protein_g" in raw_nut:
        raw_prot = _safe_float(raw_nut.get("protein_g"))
    else:
        raw_prot = _safe_float(product.get("protein"))
    if raw_prot is not None:
        prot_val = raw_prot * scale
        if prot_val > 100.0:
            val_warnings.append(f"Declared protein ({round(prot_val, 1)}g/100g) exceeds 100g; flagged as implausible.")
            norm["protein"] = None
            missing_fields.append("protein")
        else:
            norm["protein"] = round(prot_val, 2)
    else:
        norm["protein"] = None
        missing_fields.append("protein")

    # 6. Dietary Fibre
    if has_raw and "dietary_fiber_g" in raw_nut:
        raw_fib = _safe_float(raw_nut.get("dietary_fiber_g"))
    else:
        raw_fib = _safe_float(product.get("fibre"))
    if raw_fib is not None:
        fib_val = raw_fib * scale
        if fib_val > 100.0:
            val_warnings.append(f"Declared fibre ({round(fib_val, 1)}g/100g) exceeds 100g; flagged as implausible.")
            norm["fibre"] = None
            missing_fields.append("dietary fibre")
        else:
            norm["fibre"] = round(fib_val, 2)
    else:
        norm["fibre"] = None
        missing_fields.append("dietary fibre")

    # 7. Salt / Sodium
    if has_raw and "salt_g" in raw_nut:
        raw_salt = _safe_float(raw_nut.get("salt_g"))
    else:
        raw_salt = _safe_float(product.get("salt"))
    if has_raw and "sodium_mg" in raw_nut:
        raw_sod = _safe_float(raw_nut.get("sodium_mg"))
    else:
        raw_sod = _safe_float(product.get("sodium"))

    if raw_salt is not None:
        salt_val = raw_salt * scale
    elif raw_sod is not None:
        sod_val = raw_sod * scale
        # If declared sodium > 10, likely reported in mg rather than g
        if sod_val > 10.0:
            salt_val = round((sod_val / 1000.0) * 2.5, 3)
            val_warnings.append(f"Salt estimated from declared sodium ({round(sod_val, 1)}mg -> {salt_val}g salt).")
        else:
            salt_val = round(sod_val * 2.5, 3)
            val_warnings.append(f"Salt estimated from declared sodium ({round(sod_val, 2)}g -> {salt_val}g salt).")
    else:
        salt_val = None

    if salt_val is not None:
        if salt_val > 100.0:
            val_warnings.append(f"Declared salt ({round(salt_val, 1)}g/100g) exceeds 100g; flagged as implausible.")
            norm["salt"] = None
            missing_fields.append("salt / sodium")
        else:
            norm["salt"] = round(salt_val, 3)
    else:
        norm["salt"] = None
        missing_fields.append("salt / sodium")

    # Trans fat (for claim verification)
    if has_raw and "trans_fat_g" in raw_nut:
        raw_trans = _safe_float(raw_nut.get("trans_fat_g"))
    else:
        raw_trans = _safe_float(product.get("trans_fat"))
    norm["trans_fat"] = round(raw_trans * scale, 3) if raw_trans is not None else None

    return norm, missing_fields, val_warnings


def has_sufficient_nutrition_data(norm_nutrients: dict[str, float | None]) -> bool:
    """
    Determine whether sufficient essential nutrition declarations are present
    to compute an authoritative, defensible health grade.
    Requires at least calories or a primary macronutrient, and at least 2 distinct declared dimensions.
    """
    declared = [
        k for k in ["calories", "sugar", "total_fat", "saturated_fat", "protein", "fibre", "salt"]
        if norm_nutrients.get(k) is not None
    ]
    if len(declared) < 2:
        return False
    has_core = any(
        norm_nutrients.get(k) is not None
        for k in ["calories", "sugar", "total_fat", "protein"]
    )
    return has_core


# ============================================================
# DATA QUALITY & COMPLETENESS SCORING (Section 7)
# ============================================================

def calculate_data_quality_score(product: dict[str, Any]) -> tuple[float, list[str]]:
    """
    Calculate dynamic data completeness and confidence score (0–100).
    Missing information must not silently become zero.

    Returns:
        (score, missing_fields)
    """
    product = _to_dict(product)
    points = 0.0
    missing_fields = []

    # 1. Product Identity (25 points)
    if str(product.get("product_name") or "").strip():
        points += 10.0
    else:
        missing_fields.append("product_name")

    if str(product.get("brand") or "").strip():
        points += 5.0

    if str(product.get("category") or "").strip():
        points += 5.0

    if str(product.get("barcode") or "").strip() or str(product.get("source_url") or "").strip():
        points += 5.0

    # 2. Ingredient Transparency (15 points)
    ingredients_text = str(product.get("ingredients") or "").strip()
    if ingredients_text and ingredients_text.lower() not in {"not provided", "none"}:
        points += 15.0
    else:
        missing_fields.append("ingredients")

    # 3. Core Nutrition Declarations (60 points — 10 points per core nutrient)
    nutrition_keys = [
        ("calories", "energy"),
        ("sugar", "total sugar"),
        ("total_fat", "total fat"),
        ("saturated_fat", "saturated fat"),
        ("protein", "protein"),
        ("salt", "salt / sodium"),
    ]

    is_bev = is_beverage_category(product.get("category"))

    for key, label in nutrition_keys:
        raw_val = product.get(key)
        val = _safe_float(raw_val)
        if val is not None:
            # For energy, 0 kcal in solid food is typically an omission; in beverage it may be genuine
            if key == "calories" and val == 0.0 and not is_bev:
                missing_fields.append(label)
            else:
                points += 10.0
        else:
            missing_fields.append(label)

    return round(clamp(points, 0.0, 100.0), 1), missing_fields


# ============================================================
# SIX-DIMENSION HEALTH SCORING ENGINE (Section 6)
# ============================================================

def calculate_health_score(product: dict[str, Any]) -> tuple[float | None, str, list[str], dict[str, float | None]]:
    """
    FoodGrade V2.5 Research Scoring Model:
    Six nutrition dimensions:
    - Total sugar: 20% (Lower is better; beverage vs solid scaling)
    - Saturated fat: 20% (Lower is better)
    - Sodium/salt: 20% (Lower is better)
    - Energy: 10% (Lower is generally preferable)
    - Dietary fibre: 15% (Higher is better)
    - Protein: 15% (Higher is better)

    Missing-data rule:
    - If essential nutrition data is missing, returns None for score,
      "Insufficient Data" for grade, and an explicit explanation.
    - If only individual secondary nutrients are undeclared, applies neutral
      reference score (50.0) with an explanation notice rather than unearned points.

    Returns:
        (health_score, health_grade, health_reasons, dimension_scores)
    """
    product = _to_dict(product)
    norm_nutrients, missing_fields, val_warnings = normalize_nutrition(product)

    # Check for sufficient essential data
    if not has_sufficient_nutrition_data(norm_nutrients):
        health_reasons = [
            "Essential nutrition declarations (energy and macronutrients) are missing. "
            "A reliable health assessment cannot be computed."
        ]
        if val_warnings:
            health_reasons.extend(val_warnings)
        dimension_scores: dict[str, float | None] = {
            "sugar": None,
            "saturated_fat": None,
            "salt": None,
            "energy": None,
            "fibre": None,
            "protein": None,
        }
        return None, "Insufficient Data", health_reasons, dimension_scores

    health_reasons = list(val_warnings)
    dimension_scores_calc: dict[str, float] = {}

    category = product.get("category")
    is_bev = is_beverage_category(category)

    # 1. Total Sugar (20% weight, lower is better)
    sugar_val = norm_nutrients.get("sugar")
    if sugar_val is None:
        sugar_score = 50.0
        health_reasons.append("Total sugar not declared on label (neutral reference applied).")
    else:
        if is_bev:
            # Beverages: Low Sugar <= 2.5g/100ml, High >= 12g/100ml
            sugar_score = clamp(100.0 - (sugar_val / 12.0) * 100.0)
            if sugar_val <= 2.5:
                health_reasons.append(f"Low beverage sugar ({sugar_val}g/100ml) positively contributed to score.")
            elif sugar_val >= 8.0:
                health_reasons.append(f"High beverage sugar ({sugar_val}g/100ml) significantly reduced health score.")
            else:
                health_reasons.append(f"Moderate beverage sugar ({sugar_val}g/100ml) reduced health score.")
        else:
            # Solids: Low Sugar <= 5g/100g, High >= 45g/100g
            sugar_score = clamp(100.0 - (sugar_val / 45.0) * 100.0)
            if sugar_val <= 5.0:
                health_reasons.append(f"Low sugar ({sugar_val}g/100g) positively contributed to health score.")
            elif sugar_val > 22.5:
                health_reasons.append(f"High sugar content ({sugar_val}g/100g) significantly reduced health score.")
            elif sugar_val > 10.0:
                health_reasons.append(f"Moderate sugar ({sugar_val}g/100g) reduced health score.")
    dimension_scores_calc["sugar"] = round(sugar_score, 1)

    # 2. Saturated Fat (20% weight, lower is better)
    sat_val = norm_nutrients.get("saturated_fat")
    if sat_val is None:
        sat_score = 50.0
        health_reasons.append("Saturated fat not declared on label (neutral reference applied).")
    else:
        sat_score = clamp(100.0 - (sat_val / 18.0) * 100.0)
        if sat_val <= 1.5:
            health_reasons.append(f"Low saturated fat ({sat_val}g/100g) positively contributed to score.")
        elif sat_val > 8.0:
            health_reasons.append(f"High saturated fat ({sat_val}g/100g) reduced health score.")
    dimension_scores_calc["saturated_fat"] = round(sat_score, 1)

    # 3. Sodium / Salt (20% weight, lower is better)
    salt_val = norm_nutrients.get("salt")
    if salt_val is None:
        salt_score = 50.0
        health_reasons.append("Salt/sodium not declared on label (neutral reference applied).")
    else:
        salt_score = clamp(100.0 - (salt_val / 2.5) * 100.0)
        if salt_val <= 0.3:
            health_reasons.append(f"Low salt/sodium ({salt_val}g/100g) positively contributed to score.")
        elif salt_val > 1.25:
            health_reasons.append(f"Elevated salt/sodium ({salt_val}g/100g) reduced health score.")
    dimension_scores_calc["salt"] = round(salt_score, 1)

    # 4. Energy (10% weight, lower is generally preferable)
    cal_val = norm_nutrients.get("calories")
    if cal_val is None or (cal_val == 0.0 and not is_bev):
        energy_score = 50.0
        health_reasons.append("Energy not declared on label (neutral reference applied).")
    else:
        if is_bev:
            energy_score = clamp(100.0 - (cal_val / 80.0) * 100.0)
            if cal_val <= 20.0:
                health_reasons.append(f"Low caloric density for beverage ({cal_val} kcal/100ml).")
            elif cal_val > 50.0:
                health_reasons.append(f"Elevated caloric density for beverage ({cal_val} kcal/100ml) reduced score.")
        else:
            energy_score = clamp(100.0 - ((cal_val - 50.0) / 500.0) * 100.0)
            if cal_val <= 200.0:
                health_reasons.append(f"Moderate caloric density ({cal_val} kcal/100g).")
            elif cal_val > 450.0:
                health_reasons.append(f"High caloric density ({cal_val} kcal/100g) reduced health score.")
    dimension_scores_calc["energy"] = round(energy_score, 1)

    # 5. Dietary Fibre (15% weight, higher is better)
    fibre_val = norm_nutrients.get("fibre")
    if fibre_val is None:
        fibre_score = 0.0
        health_reasons.append("Dietary fibre not declared on label (no positive score added).")
    else:
        fibre_score = clamp((fibre_val / 6.0) * 100.0)
        if fibre_val >= 6.0:
            health_reasons.append(f"High dietary fibre ({fibre_val}g/100g) significantly improved score.")
        elif fibre_val >= 3.0:
            health_reasons.append(f"Contains dietary fibre ({fibre_val}g/100g, source of fibre).")
    dimension_scores_calc["fibre"] = round(fibre_score, 1)

    # 6. Protein (15% weight, higher is better)
    protein_val = norm_nutrients.get("protein")
    if protein_val is None:
        protein_score = 0.0
        health_reasons.append("Protein not declared on label (no positive score added).")
    else:
        protein_score = clamp((protein_val / 10.0) * 100.0)
        if protein_val >= 10.0:
            health_reasons.append(f"High protein ({protein_val}g/100g meets FSSAI high-protein threshold) improved score.")
        elif protein_val >= 5.0:
            health_reasons.append(f"Contains protein ({protein_val}g/100g, source of protein).")
    dimension_scores_calc["protein"] = round(protein_score, 1)

    # Weighted calculation
    health_score = (
        0.20 * sugar_score
        + 0.20 * sat_score
        + 0.20 * salt_score
        + 0.10 * energy_score
        + 0.15 * fibre_score
        + 0.15 * protein_score
    )

    health_score = round(clamp(health_score, 0.0, 100.0), 1)
    health_grade = grade_from_score(health_score, is_claim=False)

    return health_score, health_grade, health_reasons, dimension_scores_calc


# ============================================================
# FSSAI CLAIM VERIFICATION ENGINE (Objective 2)
# ============================================================

CLAIM_STATUS_LABELS: dict[str, str] = {
    "VERIFIED": "Verified Claim",
    "NOT_VERIFIED": "Not Verified",
    "INSUFFICIENT_EVIDENCE": "Insufficient Evidence",
    "CLAIM_DETECTED_UNVERIFIED": "Claim Detected — Unverified",
    "NO_CLAIMS_DETECTED": "No Claim Detected",
    "NOT_ASSESSED": "Not Assessed",
}


def get_claim_status_label(status: str) -> str:
    """Return beginner-friendly readable label for a claim status code."""
    return CLAIM_STATUS_LABELS.get(status, status.replace("_", " ").title())


def verify_claims(
    product: dict[str, Any],
    pipeline_result: dict[str, Any] | None = None
) -> tuple[float | None, str, str, list[str], list[dict[str, Any]]]:
    """
    Connect V3 NLP extraction & normalization to FSSAI Claim Verification.

    Produces distinct statuses:
    - VERIFIED: product data satisfies applicable FSSAI criterion
    - NOT_VERIFIED: product data fails criterion
    - INSUFFICIENT_EVIDENCE: claim made, but required nutrition/ingredient data missing
    - CLAIM_DETECTED_UNVERIFIED: claim detected in text, but non-statutory / unverified
    - NO_CLAIMS_DETECTED: product assessed, no claims found
    - NOT_ASSESSED: product has not undergone claim assessment (e.g. NULL claim field)

    Returns:
        (claim_score, claim_grade, overall_status, claim_reasons, claim_details)
    """
    product = _to_dict(product)
    raw_claims_field = product.get("claims")

    # Distinguish NOT_ASSESSED from NO_CLAIMS_DETECTED
    if raw_claims_field is None:
        return (
            None,
            "Not Assessed",
            "NOT_ASSESSED",
            ["Product has not undergone claim assessment (packaging claims not declared)."],
            [],
        )

    raw_claims = str(raw_claims_field).strip()
    if not raw_claims or raw_claims.lower() in {"none", "not provided", "no claims", "no claim"}:
        return (
            0.0,
            "No Claim",
            "NO_CLAIMS_DETECTED",
            ["No marketing or nutrition claims detected on product label."],
            [],
        )

    ingredients_text = str(product.get("ingredients") or "").lower().strip()
    norm_nutrients, _, _ = normalize_nutrition(product)

    # Extract claims using V3 extraction/NLP if not already provided in pipeline_result
    extracted_claims: list[dict[str, Any]] = []
    if pipeline_result and "ranking" in pipeline_result and "ranked_claims" in pipeline_result["ranking"]:
        extracted_claims = pipeline_result["ranking"]["ranked_claims"]
    elif pipeline_result and "nlp" in pipeline_result and "normalized_claims" in pipeline_result["nlp"]:
        extracted_claims = pipeline_result["nlp"]["normalized_claims"]
    else:
        raw_items = v3_extract_claims(raw_claims)
        for item in raw_items:
            norm = v3_normalize_claim(item.get("text", ""))
            extracted_claims.append(norm)

    # If no structured claims were extracted from raw text, try splitting by comma, semicolon, newline, pipe
    if not extracted_claims and raw_claims:
        for chunk in re.split(r"[,;\n|]", raw_claims):
            chunk = chunk.strip()
            if chunk:
                norm = v3_normalize_claim(chunk)
                extracted_claims.append(norm)

    if not extracted_claims:
        return (
            0.0,
            "No Claim",
            "NO_CLAIMS_DETECTED",
            ["No recognizable claims detected on product label."],
            [],
        )

    claim_details: list[dict[str, Any]] = []
    claim_reasons: list[str] = []
    evaluable_scores: list[float] = []

    sugar_val = norm_nutrients.get("sugar")
    sat_val = norm_nutrients.get("saturated_fat")
    fat_val = norm_nutrients.get("total_fat")
    protein_val = norm_nutrients.get("protein")
    fibre_val = norm_nutrients.get("fibre")
    salt_val = norm_nutrients.get("salt")
    trans_val = norm_nutrients.get("trans_fat")

    added_sugars_list = [
        "sugar", "glucose syrup", "fructose", "sucrose", "maltose",
        "dextrose", "corn syrup", "invert sugar", "honey", "jaggery"
    ]

    for item in extracted_claims:
        concept = item.get("normalized") or "unknown"
        original = item.get("original") or item.get("text") or concept
        status = "INSUFFICIENT_EVIDENCE"
        evidence = ""
        rule = ""
        score_val = 0.0

        if concept == "high_protein":
            rule = "FSSAI Claim Regs 2018: High Protein requires >= 20% RDA (approx >= 10g/100g for solids)."
            if protein_val is None:
                status = "INSUFFICIENT_EVIDENCE"
                evidence = "Protein value not declared on label to verify High Protein claim."
            elif protein_val >= 10.0:
                status = "VERIFIED"
                evidence = f"Protein content ({protein_val}g/100g) satisfies FSSAI High Protein threshold (>= 10g/100g)."
                score_val = 100.0
            else:
                status = "NOT_VERIFIED"
                evidence = f"Protein content ({protein_val}g/100g) is below FSSAI High Protein threshold (>= 10g/100g)."

        elif concept == "source_of_protein":
            rule = "FSSAI Claim Regs 2018: Source of Protein requires >= 10% RDA (approx >= 5g/100g for solids)."
            if protein_val is None:
                status = "INSUFFICIENT_EVIDENCE"
                evidence = "Protein value not declared on label to verify Source of Protein claim."
            elif protein_val >= 5.0:
                status = "VERIFIED"
                evidence = f"Protein content ({protein_val}g/100g) satisfies FSSAI Source of Protein threshold (>= 5g/100g)."
                score_val = 100.0
            else:
                status = "NOT_VERIFIED"
                evidence = f"Protein content ({protein_val}g/100g) is below FSSAI Source of Protein threshold (>= 5g/100g)."

        elif concept == "high_fibre":
            rule = "FSSAI Claim Regs 2018: High Fibre requires >= 6g/100g."
            if fibre_val is None:
                status = "INSUFFICIENT_EVIDENCE"
                evidence = "Dietary fibre not declared on label to verify High Fibre claim."
            elif fibre_val >= 6.0:
                status = "VERIFIED"
                evidence = f"Dietary fibre ({fibre_val}g/100g) satisfies FSSAI High Fibre threshold (>= 6g/100g)."
                score_val = 100.0
            elif fibre_val >= 3.0:
                status = "NOT_VERIFIED"
                evidence = f"Dietary fibre ({fibre_val}g/100g) meets 'Source of Fibre' (>= 3g) but not 'High Fibre' (>= 6g)."
            else:
                status = "NOT_VERIFIED"
                evidence = f"Dietary fibre ({fibre_val}g/100g) is below FSSAI High Fibre threshold (>= 6g/100g)."

        elif concept == "source_of_fibre":
            rule = "FSSAI Claim Regs 2018: Source of Fibre requires >= 3g/100g."
            if fibre_val is None:
                status = "INSUFFICIENT_EVIDENCE"
                evidence = "Dietary fibre not declared on label to verify Source of Fibre claim."
            elif fibre_val >= 3.0:
                status = "VERIFIED"
                evidence = f"Dietary fibre ({fibre_val}g/100g) satisfies FSSAI Source of Fibre threshold (>= 3g/100g)."
                score_val = 100.0
            else:
                status = "NOT_VERIFIED"
                evidence = f"Dietary fibre ({fibre_val}g/100g) is below FSSAI Source of Fibre threshold (>= 3g/100g)."

        elif concept == "low_sugar":
            rule = "FSSAI Claim Regs 2018: Low Sugar requires <= 5g/100g for solids (<= 2.5g/100ml for liquids)."
            if sugar_val is None:
                status = "INSUFFICIENT_EVIDENCE"
                evidence = "Total sugar not declared on label to verify Low Sugar claim."
            elif sugar_val <= 5.0:
                status = "VERIFIED"
                evidence = f"Total sugar ({sugar_val}g/100g) satisfies FSSAI Low Sugar limit (<= 5g/100g)."
                score_val = 100.0
            else:
                status = "NOT_VERIFIED"
                evidence = f"Total sugar ({sugar_val}g/100g) exceeds FSSAI Low Sugar limit (<= 5g/100g)."

        elif concept == "sugar_free":
            rule = "FSSAI Claim Regs 2018: Sugar-Free requires <= 0.5g/100g."
            if sugar_val is None:
                status = "INSUFFICIENT_EVIDENCE"
                evidence = "Total sugar not declared on label to verify Sugar-Free claim."
            elif sugar_val <= 0.5:
                status = "VERIFIED"
                evidence = f"Total sugar ({sugar_val}g/100g) satisfies FSSAI Sugar-Free limit (<= 0.5g/100g)."
                score_val = 100.0
            else:
                status = "NOT_VERIFIED"
                evidence = f"Total sugar ({sugar_val}g/100g) exceeds FSSAI Sugar-Free limit (<= 0.5g/100g)."

        elif concept == "no_added_sugar":
            rule = "FSSAI Claim Regs 2018: No Added Sugar requires absence of added sugars in processing."
            if not ingredients_text or ingredients_text in {"not provided", "none"}:
                status = "INSUFFICIENT_EVIDENCE"
                evidence = "Ingredient list missing on label to verify No Added Sugar claim."
            else:
                found_sugars = [s for s in added_sugars_list if s in ingredients_text]
                if found_sugars:
                    status = "NOT_VERIFIED"
                    evidence = f"Added sugar ingredients detected: {', '.join(found_sugars)}."
                else:
                    status = "VERIFIED"
                    evidence = "No added sugar ingredients identified in ingredient text."
                    score_val = 100.0

        elif concept == "low_fat":
            rule = "FSSAI Claim Regs 2018: Low Fat requires <= 3g/100g for solids (<= 1.5g/100ml for liquids)."
            if fat_val is None:
                status = "INSUFFICIENT_EVIDENCE"
                evidence = "Total fat not declared on label to verify Low Fat claim."
            elif fat_val <= 3.0:
                status = "VERIFIED"
                evidence = f"Total fat ({fat_val}g/100g) satisfies FSSAI Low Fat limit (<= 3g/100g)."
                score_val = 100.0
            else:
                status = "NOT_VERIFIED"
                evidence = f"Total fat ({fat_val}g/100g) exceeds FSSAI Low Fat limit (<= 3g/100g)."

        elif concept == "fat_free":
            rule = "FSSAI Claim Regs 2018: Fat-Free requires <= 0.5g/100g."
            if fat_val is None:
                status = "INSUFFICIENT_EVIDENCE"
                evidence = "Total fat not declared on label to verify Fat-Free claim."
            elif fat_val <= 0.5:
                status = "VERIFIED"
                evidence = f"Total fat ({fat_val}g/100g) satisfies FSSAI Fat-Free limit (<= 0.5g/100g)."
                score_val = 100.0
            else:
                status = "NOT_VERIFIED"
                evidence = f"Total fat ({fat_val}g/100g) exceeds FSSAI Fat-Free limit (<= 0.5g/100g)."

        elif concept == "low_saturated_fat":
            rule = "FSSAI Claim Regs 2018: Low Saturated Fat requires <= 1.5g/100g (<= 0.75g/100ml for liquids)."
            if sat_val is None:
                status = "INSUFFICIENT_EVIDENCE"
                evidence = "Saturated fat not declared on label to verify Low Saturated Fat claim."
            elif sat_val <= 1.5:
                status = "VERIFIED"
                evidence = f"Saturated fat ({sat_val}g/100g) satisfies FSSAI Low Saturated Fat limit (<= 1.5g/100g)."
                score_val = 100.0
            else:
                status = "NOT_VERIFIED"
                evidence = f"Saturated fat ({sat_val}g/100g) exceeds FSSAI Low Saturated Fat limit (<= 1.5g/100g)."

        elif concept in {"low_sodium", "low_salt"}:
            rule = "FSSAI Claim Regs 2018: Low Sodium requires <= 0.12g sodium/100g (approx <= 0.3g salt)."
            if salt_val is None:
                status = "INSUFFICIENT_EVIDENCE"
                evidence = "Salt/sodium not declared on label to verify Low Sodium claim."
            elif salt_val <= 0.3:
                status = "VERIFIED"
                evidence = f"Salt level ({salt_val}g/100g) satisfies FSSAI Low Sodium limit."
                score_val = 100.0
            else:
                status = "NOT_VERIFIED"
                evidence = f"Salt level ({salt_val}g/100g) exceeds FSSAI Low Sodium limit (<= 0.3g salt/100g)."

        elif concept in {"sodium_free", "salt_free"}:
            rule = "FSSAI Claim Regs 2018: Sodium-Free requires <= 0.005g sodium/100g (approx <= 0.013g salt)."
            if salt_val is None:
                status = "INSUFFICIENT_EVIDENCE"
                evidence = "Salt/sodium not declared on label to verify Sodium-Free claim."
            elif salt_val <= 0.013:
                status = "VERIFIED"
                evidence = f"Salt level ({salt_val}g/100g) satisfies FSSAI Sodium-Free limit."
                score_val = 100.0
            else:
                status = "NOT_VERIFIED"
                evidence = f"Salt level ({salt_val}g/100g) exceeds FSSAI Sodium-Free limit."

        elif concept == "trans_fat_free":
            rule = "FSSAI Advertising & Claims 2018: Trans Fat Free requires < 0.2g trans fat/100g and <= 1.5g sat fat/100g."
            if trans_val is None:
                status = "INSUFFICIENT_EVIDENCE"
                evidence = "Trans fat value not declared on label to verify Trans Fat Free claim."
            elif trans_val < 0.2 and (sat_val is None or sat_val <= 1.5):
                status = "VERIFIED"
                evidence = f"Trans fat ({trans_val}g/100g) satisfies FSSAI Trans Fat Free threshold (< 0.2g/100g)."
                score_val = 100.0
            else:
                status = "NOT_VERIFIED"
                evidence = f"Trans fat ({trans_val}g/100g) or saturated fat exceeds FSSAI Trans Fat Free threshold."

        elif concept in {"organic", "natural"}:
            rule = "FSSAI Organic Food Regulations: Requires third-party accreditation (Jaivik Bharat)."
            status = "CLAIM_DETECTED_UNVERIFIED"
            evidence = f"{concept.title()} claim detected on package; requires independent statutory certification."
            score_val = 50.0

        elif concept == "marketing_claim":
            rule = "FSSAI General Claim Regulations: Marketing claims must not mislead consumers."
            status = "CLAIM_DETECTED_UNVERIFIED"
            evidence = f"Marketing statement '{original}' detected; qualitative claim without numerical statutory threshold."
            score_val = 50.0

        else:
            status = "CLAIM_DETECTED_UNVERIFIED"
            evidence = f"Claim '{original}' detected on packaging; requires domain verification."
            rule = "FSSAI General Claim Regulations: Requires supporting documentation."
            score_val = 50.0

        # Record evaluable scores for statutory claims
        if status == "VERIFIED":
            evaluable_scores.append(100.0)
            claim_reasons.append(f"[VERIFIED] {original}: {evidence}")
        elif status == "NOT_VERIFIED":
            evaluable_scores.append(0.0)
            claim_reasons.append(f"[NOT VERIFIED] {original}: {evidence}")
        elif status == "INSUFFICIENT_EVIDENCE":
            claim_reasons.append(f"[INSUFFICIENT EVIDENCE] {original}: {evidence}")
        else:
            claim_reasons.append(f"[CLAIM DETECTED — UNVERIFIED] {original}: {evidence}")

        claim_details.append({
            "claim": original,
            "original": original,
            "concept": concept,
            "status": status,
            "evidence": evidence,
            "rule": rule,
            "score": score_val,
        })

    # Overall Claim Status & Grade Determination (Hierarchy)
    if any(c["status"] == "NOT_VERIFIED" for c in claim_details):
        overall_status = "NOT_VERIFIED"
        claim_score = 0.0
        claim_grade = "E"
    elif any(c["status"] == "VERIFIED" for c in claim_details):
        overall_status = "VERIFIED"
        if evaluable_scores:
            claim_score = round(sum(evaluable_scores) / len(evaluable_scores), 1)
        else:
            claim_score = 100.0
        claim_grade = grade_from_score(claim_score, is_claim=True)
    elif any(c["status"] == "INSUFFICIENT_EVIDENCE" for c in claim_details):
        overall_status = "INSUFFICIENT_EVIDENCE"
        claim_score = 0.0
        claim_grade = "E"
    elif any(c["status"] == "CLAIM_DETECTED_UNVERIFIED" for c in claim_details):
        overall_status = "CLAIM_DETECTED_UNVERIFIED"
        claim_score = 50.0
        claim_grade = "C"
    else:
        overall_status = "NO_CLAIMS_DETECTED"
        claim_score = 0.0
        claim_grade = "No Claim"

    return claim_score, claim_grade, overall_status, claim_reasons, claim_details


# ============================================================
# COMPATIBILITY WRAPPERS
# ============================================================

def calculate_claim_score(product: dict[str, Any]) -> tuple[float | None, list[str]]:
    """Backward-compatible wrapper for existing calculate_claim_score callers."""
    score, grade, status, reasons, _ = verify_claims(product)
    return score, reasons


# ============================================================
# MAIN FOODGRADE CALCULATION ENTRYPOINT
# ============================================================

def calculate_foodgrade(
    product: dict[str, Any],
    pipeline_result: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Main FoodGrade V2.5 scoring and verification engine.

    Produces two separate, unmerged evaluations:
    - Health Grade (A–E or Insufficient Data) & Score (0–100 or None)
    - Claim Status & Grade (VERIFIED, NOT_VERIFIED, INSUFFICIENT_EVIDENCE,
      CLAIM_DETECTED_UNVERIFIED, NO_CLAIMS_DETECTED, NOT_ASSESSED)
    - Dynamic Data Quality Score (0–100)
    - Positive & Negative Scoring Factors
    """
    product = _to_dict(product)

    # 1. Health Score (6 dimensions)
    health_score, health_grade, health_reasons, dimension_scores = calculate_health_score(product)
    health_status = "GRADED" if health_score is not None else "INSUFFICIENT_DATA"

    # Extract positive and negative factors
    positive_factors = [
        r for r in health_reasons
        if any(w in r for w in ["positively", "improved", "Low sugar", "Low saturated", "Low salt", "High fibre", "High protein", "source of"])
    ]
    negative_factors = [
        r for r in health_reasons
        if any(w in r for w in ["reduced", "penalty", "High sugar", "High saturated", "Elevated", "High caloric", "exceeds"])
    ]
    missing_factors = [
        r for r in health_reasons
        if "neutral reference" in r or "not declared" in r or "missing" in r.lower()
    ]

    # 2. Claim Verification (V3 NLP connected to FSSAI)
    claim_score, claim_grade, claim_status, claim_reasons, claim_details = verify_claims(
        product,
        pipeline_result=pipeline_result
    )

    # 3. Dynamic Data Completeness & Confidence Score
    data_quality_score, missing_fields = calculate_data_quality_score(product)

    if claim_status == "INSUFFICIENT_EVIDENCE" and data_quality_score > 30:
        data_quality_score = round(data_quality_score * 0.85, 1)

    category = product.get("category") or "Packaged Food"
    is_bev = is_beverage_category(category)

    return {
        "health_score": health_score,
        "health_grade": health_grade,
        "health_status": health_status,
        "claim_score": claim_score,
        "claim_grade": claim_grade,
        "claim_status": claim_status,
        "claim_status_label": get_claim_status_label(claim_status),
        "health_reasons": health_reasons,
        "positive_factors": positive_factors,
        "negative_factors": negative_factors,
        "missing_factors": missing_factors,
        "claim_reasons": claim_reasons,
        "data_quality_score": data_quality_score,
        "claim_status_label": get_claim_status_label(claim_status),
        "claim_details": claim_details,
        "dimension_scores": dimension_scores,
        "missing_fields": missing_fields,
        "category": category,
        "is_beverage": is_bev,
        "methodology_status": "FoodGrade V2.5 research methodology",
    }
