import re
from datetime import datetime

from services.web_parser import (
    soup_from_html,
    extract_jsonld,
    find_product_jsonld,
    page_title,
    visible_text,
    clean_text,
)


# ============================================================
# CLAIMS
# ============================================================

CLAIM_TERMS = [
    "high protein",
    "high fibre",
    "high fiber",
    "source of protein",
    "source of fibre",
    "source of fiber",
    "low sugar",
    "no added sugar",
    "sugar free",
    "sugar-free",
    "low fat",
    "fat free",
    "fat-free",
    "low calorie",
    "reduced sugar",
    "reduced fat",
    "whole grain",
    "whole wheat",
    "organic",
    "natural",
]


# ============================================================
# NUTRITION PATTERNS
# ============================================================

NUTRIENT_PATTERNS = {

    "calories": [
        r"(?:energy|calories|calorie)\s*(?:per\s*(?:100\s*g|serving|scoop))?\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(?:kcal|cal|calories)?",
        r"(\d+(?:\.\d+)?)\s*(?:kcal|calories)\b",
        r"(?:energy|calories)\s*[:\-]?\s*(\d+(?:\.\d+)?)",
    ],

    "sugar": [
        r"(?:total\s+)?sugars?\s*(?:per\s*(?:100\s*g|serving|scoop))?\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*g",
        r"(\d+(?:\.\d+)?)\s*g(?:\s+of)?\s+(?:total\s+)?sugars?\b",
        r"(?:total\s+)?sugars?.{0,20}?(\d+(?:\.\d+)?)\s*g",
    ],

    "total_fat": [
        r"(?:total\s+)?fat\s*(?:per\s*(?:100\s*g|serving|scoop))?\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*g",
        r"(\d+(?:\.\d+)?)\s*g(?:\s+of)?\s+(?:total\s+)?fat\b",
        r"total\s+fat.{0,20}?(\d+(?:\.\d+)?)\s*g",
    ],

    "saturated_fat": [
        r"satur(?:ated|ates)\s+fat\s*(?:per\s*(?:100\s*g|serving|scoop))?\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*g",
        r"(\d+(?:\.\d+)?)\s*g(?:\s+of)?\s+satur(?:ated|ates)\s+fat\b",
        r"satur(?:ated|ates)\s+fat.{0,20}?(\d+(?:\.\d+)?)\s*g",
    ],

    "protein": [
        r"(?:total\s+)?protein\s*(?:per\s*(?:100\s*g|serving|scoop))?\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*g",
        r"(\d+(?:\.\d+)?)\s*g(?:\s+of)?\s+protein\b",
        r"protein.{0,20}?(\d+(?:\.\d+)?)\s*g",
    ],

    "fibre": [
        r"(?:dietary\s+)?fib(?:re|er)\s*(?:per\s*(?:100\s*g|serving|scoop))?\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*g",
        r"(\d+(?:\.\d+)?)\s*g(?:\s+of)?\s+(?:dietary\s+)?fib(?:re|er)\b",
        r"(?:dietary\s+)?fib(?:re|er).{0,20}?(\d+(?:\.\d+)?)\s*g",
    ],

    "salt": [
        r"salt\s*(?:per\s*(?:100\s*g|serving|scoop))?\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*g",
        r"(\d+(?:\.\d+)?)\s*g(?:\s+of)?\s+salt\b",
        r"salt.{0,20}?(\d+(?:\.\d+)?)\s*g",
    ],
}


# ============================================================
# GENERAL HELPERS
# ============================================================

def _first_number(text, patterns):
    """
    Return the first numeric value matching any pattern.
    """
    text = text or ""

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.I | re.S
        )

        if match:
            try:
                return float(match.group(1))
            except (ValueError, TypeError):
                pass

    return 0.0


def _clean_value(value):
    """
    Convert arbitrary values to clean text.
    """
    if value is None:
        return ""

    if isinstance(value, list):
        value = ", ".join(
            str(item)
            for item in value
            if item is not None
        )

    if isinstance(value, dict):
        value = value.get("name", "")

    return clean_text(value)


# ============================================================
# JSON-LD HELPERS
# ============================================================

def _find_nested_product(records):
    """
    Search JSON-LD records recursively for a Product object.

    Handles:
    - Product
    - @graph
    - nested dictionaries
    - nested lists
    """

    def search(obj):

        if isinstance(obj, dict):

            obj_type = obj.get("@type", "")

            if isinstance(obj_type, list):
                types = [
                    str(x).lower()
                    for x in obj_type
                ]
            else:
                types = [
                    str(obj_type).lower()
                ]

            if "product" in types:
                return obj

            for value in obj.values():

                result = search(value)

                if result:
                    return result

        elif isinstance(obj, list):

            for item in obj:

                result = search(item)

                if result:
                    return result

        return None

    return search(records)


# ============================================================
# BRAND EXTRACTION
# ============================================================

def _extract_brand(soup, product, title):
    """
    Try multiple sources to identify the brand.
    """

    # 1. JSON-LD
    brand = product.get("brand", "")

    if isinstance(brand, dict):
        brand = brand.get("name", "")

    brand = _clean_value(brand)

    if brand:
        return brand

    # 2. Meta tags
    meta_selectors = [
        ("meta", {"property": "product:brand"}),
        ("meta", {"name": "brand"}),
        ("meta", {"property": "og:brand"}),
    ]

    for tag_name, attrs in meta_selectors:

        tag = soup.find(
            tag_name,
            attrs=attrs
        )

        if tag and tag.get("content"):
            value = clean_text(
                tag.get("content")
            )

            if value:
                return value

    # 3. HTML elements whose class/id contains brand
    elements = soup.find_all(
        attrs={
            "class": re.compile(
                r"brand",
                re.I
            )
        }
    )

    for element in elements[:10]:

        value = clean_text(
            element.get_text(" ")
        )

        if value and not re.match(r"^\d+(?:\.\d+)?\s*(?:g|kg|ml|l|oz|gm|mg)\b", value, re.I) and len(value) < 100:
            return value

    # 4. Title fallback (e.g. "Wheelos Masala Flavour – Balaji Wafers – 22 g" or "KURKURE | Pepsnacks" or "Original Oreo – Cadbury – 41.75 g")
    if title:
        parts = [clean_text(x) for x in re.split(r"\s*[\-–—|]\s*", title) if clean_text(x)]
        if len(parts) >= 2:
            candidate = parts[-1]
            if re.match(r"^\d+(?:\.\d+)?\s*(?:g|kg|ml|l|oz|gm|mg)\b", candidate, re.I) and len(parts) >= 3:
                candidate = parts[-2]
            if candidate and not re.match(r"^\d+(?:\.\d+)?\s*(?:g|kg|ml|l|oz|gm|mg)\b", candidate, re.I) and len(candidate) <= 80:
                return candidate

    # 5. Known brand scan on product name / title
    known_brands = [
        "Amul", "Cadbury", "Britannia", "Nestle", "Parle", "Haldiram",
        "Lay's", "Lays", "PepsiCo", "Doritos", "Kurkure", "Uncle Chipps",
        "Too Yumm", "Saffola", "Kellogg's", "Kellogg", "ITC", "Sunfeast",
        "Patanjali", "Mother Dairy", "Aashirvaad", "Tata", "Fortune", "MTR",
        "Balaji", "Bikaji", "Real", "Tropicana", "Frooti", "Maaza"
    ]
    scan_text = f"{title or ''} {product.get('name', '')}"
    for kb in known_brands:
        if re.search(rf"\b{re.escape(kb)}\b", scan_text, re.I):
            return kb

    return ""


# ============================================================
# CATEGORY EXTRACTION
# ============================================================

def _extract_category(soup, product):

    category = _clean_value(
        product.get("category", "")
    )

    if category:
        return category

    # Meta category
    meta_candidates = [
        soup.find(
            "meta",
            attrs={"name": "category"}
        ),
        soup.find(
            "meta",
            attrs={"property": "product:category"}
        ),
    ]

    for tag in meta_candidates:

        if tag and tag.get("content"):

            value = clean_text(
                tag.get("content")
            )

            if value:
                return value

    # Breadcrumb fallback
    breadcrumb = soup.find(
        attrs={
            "class": re.compile(
                r"breadcrumb",
                re.I
            )
        }
    )

    if breadcrumb:

        links = breadcrumb.find_all(
            ["a", "span", "li"]
        )

        values = [
            clean_text(x.get_text(" "))
            for x in links
        ]

        values = [
            x for x in values
            if x
        ]

        if values:
            return values[-1]

    return ""


# ============================================================
# PRODUCT NAME EXTRACTION
# ============================================================

def _clean_compound_name(name):
    if not name:
        return ""
    delims = ["|", "–", "—", " - "]
    for d in delims:
        if d in name:
            parts = [clean_text(x) for x in name.split(d) if clean_text(x)]
            if parts and len(parts[0]) >= 3:
                return parts[0]
    return clean_text(name)


def _extract_product_name(soup, product, title):

    # 1. JSON-LD
    name = _clean_value(
        product.get("name", "")
    )

    if name:
        return _clean_compound_name(name)

    # 2. OpenGraph title
    og_title = soup.find(
        "meta",
        attrs={
            "property": "og:title"
        }
    )

    if og_title and og_title.get("content"):
        value = clean_text(
            og_title.get("content")
        )
        if value:
            return _clean_compound_name(value)

    # 3. Product heading
    product_heading = soup.find(
        attrs={
            "class": re.compile(
                r"(product[-_ ]?)?title|product[-_ ]?name",
                re.I
            )
        }
    )

    if product_heading:
        value = clean_text(
            product_heading.get_text(" ")
        )
        if value and len(value) < 300:
            return _clean_compound_name(value)

    # 4. H1
    h1 = soup.find("h1")

    if h1:
        value = clean_text(
            h1.get_text(" ")
        )
        if value:
            return _clean_compound_name(value)

    # 5. Page title (strip compound brand/weight suffixes if present)
    if title:
        return _clean_compound_name(title)

    return "Web Product"


# ============================================================
# INGREDIENT EXTRACTION
# ============================================================

def _extract_ingredients_from_elements(soup):

    # Look for elements where class/id contains
    # ingredient / ingredients.
    elements = soup.find_all(
        attrs={
            "class": re.compile(
                r"ingredient",
                re.I
            )
        }
    )

    elements += soup.find_all(
        attrs={
            "id": re.compile(
                r"ingredient",
                re.I
            )
        }
    )

    for element in elements[:30]:

        value = clean_text(
            element.get_text(" ")
        )

        if not value:
            continue

        # Remove heading-only values.
        if value.lower() in {
            "ingredient",
            "ingredients"
        }:
            continue

        # Avoid returning tiny unrelated strings.
        if len(value) >= 15:

            # If text begins with "Ingredients:",
            # remove the label.
            value = re.sub(
                r"^ingredients?\s*[:\-]\s*",
                "",
                value,
                flags=re.I
            )

            return value[:3000]

    return ""


def _ingredients_from_text(text):

    if not text:
        return ""

    patterns = [

        r"ingredients?\s*[:\-]\s*(.+?)"
        r"(?=\s+(?:nutrition|nutritional information|"
        r"allergen|allergens|contains|storage|"
        r"directions|preparation|manufacturer|"
        r"product information)\b|$)",

        r"ingredients?\s+(.+?)"
        r"(?=\s+(?:nutrition|nutritional information|"
        r"allergen|allergens|contains|storage|"
        r"directions|preparation|manufacturer)\b|$)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.I | re.S
        )

        if match:

            value = clean_text(
                match.group(1)
            )

            if len(value) >= 10:
                return value[:3000]

    return ""


def _extract_ingredients(soup, product, text):

    # 1. JSON-LD
    ingredients = _clean_value(
        product.get("ingredients", "")
        or product.get("ingredient", "")
    )

    if ingredients:
        return ingredients[:3000]

    # 2. HTML elements
    ingredients = _extract_ingredients_from_elements(
        soup
    )

    if ingredients:
        return ingredients

    # 3. Visible text
    ingredients = _ingredients_from_text(
        text
    )

    return ingredients


# ============================================================
# CLAIM EXTRACTION
# ============================================================

def _claims_from_text(text):

    lower = (text or "").lower()

    found = []

    for term in CLAIM_TERMS:

        if term in lower:

            # Keep one normalized spelling.
            normalized = term.replace(
                "sugar-free",
                "sugar free"
            ).replace(
                "fat-free",
                "fat free"
            )

            found.append(
                normalized.title()
            )

    # Remove duplicates while preserving order.
    return ", ".join(
        dict.fromkeys(found)
    )


def _extract_claims(soup, product, text):

    description = _clean_value(
        product.get("description", "")
    )

    # Meta description can contain product claims.
    meta_description = soup.find(
        "meta",
        attrs={
            "name": "description"
        }
    )

    meta_text = ""

    if meta_description:
        meta_text = clean_text(
            meta_description.get("content", "")
        )

    combined = " ".join([
        description,
        meta_text,
        text or ""
    ])

    return _claims_from_text(
        combined
    )


# ============================================================
# NUTRITION FROM HTML TABLES
# ============================================================

def _parse_nutrient_pair(label, value, nutrition):
    label = clean_text(label).lower()
    value = clean_text(value)
    if not label or not value:
        return

    # Normalize numbers with thousand-separators (e.g., '2,240' -> '2240')
    cleaned_val = re.sub(r"(\d),(\d)", r"\1\2", value)
    number_match = re.search(r"(\d+(?:\.\d+)?)", cleaned_val)
    if not number_match:
        return
    number = float(number_match.group(1))

    if "energy" in label or "calorie" in label:
        if "calories" not in nutrition or nutrition["calories"] == 0:
            kcal_match = re.search(r"(\d+(?:\.\d+)?)\s*k?cal", cleaned_val, re.I)
            if kcal_match:
                nutrition["calories"] = float(kcal_match.group(1))
            else:
                kj_match = re.search(r"(\d+(?:\.\d+)?)\s*kj", cleaned_val, re.I)
                if kj_match:
                    nutrition["calories"] = round(float(kj_match.group(1)) / 4.184, 1)
                else:
                    nutrition["calories"] = number

    elif "sugar" in label and "added" not in label:
        if "sugar" not in nutrition or nutrition["sugar"] == 0:
            nutrition["sugar"] = number

    elif "saturated" in label and "fat" in label:
        if "saturated_fat" not in nutrition or nutrition["saturated_fat"] == 0:
            nutrition["saturated_fat"] = number

    elif (
        ("total fat" in label or label == "fat" or label.endswith(" fat"))
        and "saturated" not in label
        and "trans" not in label
        and "unsaturated" not in label
    ):
        if "total_fat" not in nutrition or nutrition["total_fat"] == 0:
            nutrition["total_fat"] = number

    elif "protein" in label:
        if "protein" not in nutrition or nutrition["protein"] == 0:
            nutrition["protein"] = number

    elif "fibre" in label or "fiber" in label:
        if "fibre" not in nutrition or nutrition["fibre"] == 0:
            nutrition["fibre"] = number

    elif "salt" in label:
        if "salt" not in nutrition or nutrition["salt"] == 0:
            nutrition["salt"] = number

    elif "sodium" in label and ("salt" not in nutrition or nutrition["salt"] == 0):
        if "mg" in value.lower():
            nutrition["salt"] = round((number * 2.5) / 1000.0, 3)
        else:
            nutrition["salt"] = round(number * 2.5, 3)


def _extract_nutrition_from_tables(soup):

    nutrition = {}

    # 1. Search all tables
    for table in soup.find_all("table"):

        rows = table.find_all("tr")

        for row in rows:

            cells = row.find_all(["th", "td"])

            if len(cells) >= 2:
                label = cells[0].get_text(" ")
                val = cells[1].get_text(" ")
                _parse_nutrient_pair(label, val, nutrition)
                if len(cells) >= 3 and (not val or val.strip().lower() in {"100g", "per 100g", "100 g"}):
                    _parse_nutrient_pair(label, cells[2].get_text(" "), nutrition)

    # 2. Search definition lists <dl>
    for dl in soup.find_all("dl"):
        dts = dl.find_all("dt")
        dds = dl.find_all("dd")
        for dt, dd in zip(dts, dds):
            _parse_nutrient_pair(dt.get_text(" "), dd.get_text(" "), nutrition)

    # 3. Search lists <li> with colon delimiter
    for li in soup.find_all("li"):
        txt = clean_text(li.get_text(" "))
        if ":" in txt and len(txt) < 120:
            parts = txt.split(":", 1)
            _parse_nutrient_pair(parts[0], parts[1], nutrition)

    # 4. Search divs with nutrient/macro/fact classes
    for div in soup.find_all(attrs={"class": re.compile(r"nutrition|nutrient|macro|fact", re.I)}):
        spans = div.find_all(["span", "div", "p", "strong", "b"], recursive=False)
        if len(spans) == 2:
            _parse_nutrient_pair(spans[0].get_text(" "), spans[1].get_text(" "), nutrition)

    return nutrition


# ============================================================
# NUTRITION FROM JSON-LD
# ============================================================

def _extract_jsonld_nutrition(product):

    nutrition = {}

    # Correct Schema.org field:
    # nutritionInformation
    info = product.get(
        "nutritionInformation"
    )

    # Support the old/custom field too.
    if not info:
        info = product.get(
            "nutrition"
        )

    if not isinstance(info, dict):
        return nutrition

    mappings = {

        "calories": [
            "calories",
            "energy"
        ],

        "sugar": [
            "sugarContent",
            "sugars"
        ],

        "total_fat": [
            "fatContent",
            "fat"
        ],

        "saturated_fat": [
            "saturatedFatContent",
            "saturatedFat"
        ],

        "protein": [
            "proteinContent",
            "protein"
        ],

        "fibre": [
            "fiberContent",
            "fibreContent",
            "fibre"
        ],

        "salt": [
            "saltContent",
            "salt"
        ],
    }

    for field, keys in mappings.items():

        for key in keys:

            if key not in info:
                continue

            value = info[key]

            if isinstance(value, dict):
                value = (
                    value.get("value")
                    or value.get("amount")
                )

            match = re.search(
                r"\d+(?:\.\d+)?",
                str(value)
            )

            if match:

                nutrition[field] = float(
                    match.group(0)
                )

                break

    return nutrition


# ============================================================
# IMAGE EXTRACTION
# ============================================================

def _extract_image(soup, product):

    image = product.get(
        "image",
        ""
    )

    if isinstance(image, list):

        image = (
            image[0]
            if image
            else ""
        )

    image = _clean_value(
        image
    )

    if image:
        return image

    og_image = soup.find(
        "meta",
        attrs={
            "property": "og:image"
        }
    )

    if og_image and og_image.get("content"):

        return clean_text(
            og_image.get("content")
        )

    return ""


# ============================================================
# MAIN EXTRACTION FUNCTION
# ============================================================

def extract_product_from_html(
    url,
    html,
    headers=None
):
    """
    Extract product information from a webpage.

    Extraction priority:

    1. JSON-LD / Schema.org Product
    2. Meta tags
    3. Product-specific HTML elements
    4. Nutrition tables
    5. Visible page text
    6. Page title

    Output is normalized to the format
    expected by the existing FoodGrade/V3 pipeline.
    """

    soup = soup_from_html(
        html
    )

    # Extract JSON-LD BEFORE visible_text()
    # because visible_text() removes script tags.
    records = extract_jsonld(
        soup
    )

    product = (
        _find_nested_product(records)
        or find_product_jsonld(records)
        or {}
    )

    title = page_title(
        soup
    )

    # Visible page text.
    text = visible_text(
        soup
    )

    # --------------------------------------------------------
    # BASIC PRODUCT INFORMATION
    # --------------------------------------------------------

    product_name = _extract_product_name(
        soup,
        product,
        title
    )

    brand = _extract_brand(
        soup,
        product,
        title
    )

    category = _extract_category(
        soup,
        product
    )

    ingredients = _extract_ingredients(
        soup,
        product,
        text
    )

    claims = _extract_claims(
        soup,
        product,
        text
    )

    # --------------------------------------------------------
    # NUTRITION
    # --------------------------------------------------------

    jsonld_nutrition = (
        _extract_jsonld_nutrition(
            product
        )
    )

    table_nutrition = (
        _extract_nutrition_from_tables(
            soup
        )
    )

    nutrition = {}

    # JSON-LD gets priority.
    nutrition.update(
        table_nutrition
    )

    nutrition.update(
        jsonld_nutrition
    )

    # Text fallback for anything still missing.
    for field, patterns in NUTRIENT_PATTERNS.items():

        if field not in nutrition or nutrition.get(field) == 0:

            value = _first_number(
                text,
                patterns
            )

            if value:
                nutrition[field] = value

    # Sodium to Salt fallback for text
    if "salt" not in nutrition or nutrition.get("salt") == 0:
        sodium_patterns = [
            r"sodium\s*(?:per\s*(?:100\s*g|serving|scoop))?\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*mg",
            r"(\d+(?:\.\d+)?)\s*mg(?:\s+of)?\s+sodium\b",
            r"sodium.{0,20}?(\d+(?:\.\d+)?)\s*mg",
        ]
        sodium_mg = _first_number(text, sodium_patterns)
        if sodium_mg:
            nutrition["salt"] = round((sodium_mg * 2.5) / 1000.0, 3)

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    extraction_sources = []

    if product:
        extraction_sources.append(
            "JSON-LD"
        )

    if ingredients:
        extraction_sources.append(
            "Ingredients HTML/text"
        )

    if nutrition:
        extraction_sources.append(
            "Nutrition HTML/text"
        )

    if claims:
        extraction_sources.append(
            "Claims/page text"
        )

    if not extraction_sources:
        extraction_sources.append(
            "Visible-page fallback"
        )

    result = {

        "product_name": product_name,

        "brand": brand,

        "category": category,

        "ingredients": ingredients,

        "claims": claims,

        "calories": nutrition.get(
            "calories",
            0.0
        ),

        "sugar": nutrition.get(
            "sugar",
            0.0
        ),

        "total_fat": nutrition.get(
            "total_fat",
            0.0
        ),

        "saturated_fat": nutrition.get(
            "saturated_fat",
            0.0
        ),

        "protein": nutrition.get(
            "protein",
            0.0
        ),

        "fibre": nutrition.get(
            "fibre",
            0.0
        ),

        "salt": nutrition.get(
            "salt",
            0.0
        ),

        "source": "Web Retrieval",

        "source_url": url,

        "image_url": _extract_image(
            soup,
            product
        ),

        "retrieved_at":
            datetime.utcnow().isoformat()
            + "Z",

        "page_title": title,

        "extraction_method":
            " + ".join(
                extraction_sources
            ),
    }

    return result