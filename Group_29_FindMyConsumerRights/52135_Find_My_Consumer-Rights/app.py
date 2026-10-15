import streamlit as st
import os
import re
import json
from collections import Counter

from src.index import InvertedIndex
from src.preprocess import preprocess
from src.rankers.tfidf import TFIDFRanker
from src.rankers.bm25 import BM25Ranker
from src.rankers.language_model import LanguageModelRanker
from src.forum_guidance import parse_monetary_amount, get_forum_guidance, determine_forum
from src.query_expansion import expand_query

st.set_page_config(
    page_title="Consumer Rights Helper",
    page_icon="⚖️",
    layout="wide"
)

# Custom Styling (Centered, max 1000px width, clean cards, readable typography)
st.markdown("""
<style>
    /* Google Font Import */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Enforce clean light background across entire application */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #FFFFFF !important;
        color: #1F2937 !important;
    }

    /* Content centering and max 1000px width */
    .block-container {
        max-width: 1000px !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        padding-top: 2rem !important;
        padding-bottom: 3.5rem !important;
        margin: 0 auto !important;
    }

    /* Typography base */
    body, p, div, span, label {
        font-size: 15px;
        color: #1F2937;
    }

    /* Headings and primary accents */
    h1 {
        color: #1E3A8A !important;
        font-size: 2.3rem !important;
        font-weight: 700 !important;
        margin-bottom: 0.2rem !important;
    }

    h3 {
        color: #1E3A8A !important;
        font-size: 1.35rem !important;
        font-weight: 700 !important;
        margin-top: 1.8rem !important;
        margin-bottom: 0.8rem !important;
    }

    /* Input area */
    .stTextArea textarea {
        background-color: #FFFFFF !important;
        color: #1F2937 !important;
        font-size: 15.5px !important;
        border-radius: 10px !important;
        border: 1px solid #CBD5E1 !important;
        padding: 12px 14px !important;
    }
    .stTextArea textarea:focus {
        border-color: #2563EB !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2) !important;
    }

    /* Tabs Styling (Clean Light Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #F8FAFC !important;
        border-radius: 10px !important;
        padding: 4px !important;
        border: 1px solid #E2E8F0 !important;
        gap: 6px !important;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        color: #475569 !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        border: none !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #2563EB !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
    }

    /* Expanders Styling (Consistent Light theme for legal passages) */
    [data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        color: #1F2937 !important;
        margin-bottom: 10px !important;
    }
    [data-testid="stExpander"] details summary {
        color: #1E3A8A !important;
        font-weight: 600 !important;
    }
    [data-testid="stExpander"] details summary:hover {
        color: #2563EB !important;
    }
    [data-testid="stExpander"] details[open] {
        background-color: #FFFFFF !important;
    }
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        background-color: #FAFAFA !important;
        border-top: 1px solid #E2E8F0 !important;
        border-radius: 0 0 10px 10px !important;
        padding: 14px 16px !important;
    }

    /* Audio Input Widget Container */
    [data-testid="stAudioInput"] {
        background-color: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        padding: 12px 14px !important;
    }

    /* Code Block Styling for Drafts */
    [data-testid="stCodeBlock"] {
        background-color: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
    }
    [data-testid="stCodeBlock"] pre, [data-testid="stCodeBlock"] code {
        color: #1E293B !important;
        background-color: #F8FAFC !important;
    }

    /* Primary Action Buttons (Blue #2563EB, No Red) */
    div.stButton > button, div.stButton > button[kind="primary"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.65rem 1.4rem !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2) !important;
        transition: all 0.15s ease-in-out !important;
    }
    div.stButton > button:hover {
        background-color: #1d4ed8 !important;
        color: #ffffff !important;
        box-shadow: 0 4px 8px rgba(37, 99, 235, 0.3) !important;
        transform: translateY(-1px) !important;
    }
    div.stButton > button:active {
        background-color: #1e40af !important;
        transform: translateY(0px) !important;
    }

    /* Example Preset Buttons */
    .example-btn div.stButton > button {
        background-color: #f8fafc !important;
        color: #1e293b !important;
        border: 1px solid #e2e8f0 !important;
        font-size: 13.5px !important;
        font-weight: 500 !important;
        padding: 0.45rem 0.6rem !important;
        box-shadow: none !important;
    }
    .example-btn div.stButton > button:hover {
        background-color: #f1f5f9 !important;
        border-color: #94a3b8 !important;
        color: #0f172a !important;
    }

    /* Semantic Dashboard Cards */
    .metric-card {
        border-radius: 12px;
        padding: 16px 18px;
        border-left: 5px solid;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        margin-bottom: 12px;
        background: #ffffff;
    }
    .metric-card-green  { background-color: #ecfdf5; border-left-color: #10b981; }
    .metric-card-blue   { background-color: #eff6ff; border-left-color: #2563eb; }
    .metric-card-orange { background-color: #fffbeb; border-left-color: #f59e0b; }
    .metric-card-purple { background-color: #f5f3ff; border-left-color: #8b5cf6; }

    .metric-label {
        font-size: 12.5px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .metric-card-green .metric-label  { color: #047857; }
    .metric-card-blue .metric-label   { color: #1d4ed8; }
    .metric-card-orange .metric-label { color: #b45309; }
    .metric-card-purple .metric-label { color: #6d28d9; }

    .metric-val {
        font-size: 17px;
        font-weight: 700;
        color: #0f172a;
    }
    .metric-sub {
        font-size: 13.5px;
        color: #475569;
        margin-top: 3px;
    }

    /* Food Safety Alert Card */
    .food-safety-card {
        background-color: #fff1f2;
        border: 1px solid #fecdd3;
        border-left: 6px solid #e11d48;
        border-radius: 12px;
        padding: 18px 20px;
        margin-top: 14px;
        margin-bottom: 18px;
        box-shadow: 0 4px 6px -1px rgba(225, 29, 72, 0.06);
    }

    /* Law Card */
    .law-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px 18px;
        margin-bottom: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
        border-left: 5px solid #2563eb;
    }
    .law-card-title {
        font-size: 16.5px;
        font-weight: 700;
        color: #1e3a8a;
    }
    .law-card-desc {
        font-size: 14.5px;
        color: #334155;
        margin-top: 6px;
        line-height: 1.5;
    }
    .law-card-badge {
        font-size: 11px;
        font-weight: 700;
        color: #2563eb;
        background: #eff6ff;
        padding: 2px 8px;
        border-radius: 10px;
        border: 1px solid #bfdbfe;
    }

    /* Rights Card */
    .rights-card {
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 12px;
        padding: 16px 18px;
        height: 100%;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.03);
    }
    .rights-card-title {
        font-size: 16px;
        font-weight: 700;
        color: #15803d;
        margin-bottom: 6px;
    }
    .rights-card-body {
        font-size: 13.5px;
        color: #1e293b;
        line-height: 1.45;
    }
    .rights-card-cite {
        font-size: 11.5px;
        color: #166534;
        margin-top: 8px;
        font-weight: 600;
    }

    /* Remedy Tiles */
    .remedy-tile {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px 14px;
        text-align: center;
        height: 100%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .remedy-badge-active {
        background: #f5f3ff;
        color: #7c3aed;
        font-size: 11.5px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 10px;
        display: inline-block;
        margin-top: 8px;
        border: 1px solid #ddd6fe;
    }
    .remedy-badge-inactive {
        background: #f8fafc;
        color: #94a3b8;
        font-size: 11px;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 10px;
        display: inline-block;
        margin-top: 8px;
        border: 1px solid #e2e8f0;
    }

    /* Forum Card */
    .forum-card {
        background: #ffffff;
        border: 1px solid #bfdbfe;
        border-left: 6px solid #2563eb;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.05);
        margin-bottom: 12px;
    }

    /* Action Plan Container */
    .action-plan-container {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.04);
        margin-bottom: 16px;
    }
    .action-plan-item {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        margin-bottom: 14px;
    }
    .action-plan-item:last-child {
        margin-bottom: 0px;
    }
    .action-plan-num {
        background: #2563eb;
        color: #ffffff;
        font-weight: 700;
        font-size: 13px;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        margin-top: 1px;
    }
    .action-plan-text {
        font-size: 14.5px;
        color: #334155;
        line-height: 1.5;
    }

    /* Highlight badge in soft yellow */
    mark.highlight {
        background-color: #fef08a;
        color: #713f12;
        padding: 1px 4px;
        border-radius: 3px;
        font-weight: 500;
    }

    /* Expandable passage styling */
    .passage-text {
        font-size: 14.5px;
        line-height: 1.65;
        color: #1e293b;
        white-space: pre-wrap;
        margin-top: 4px;
    }
    .passage-caption {
        font-size: 12px;
        color: #64748b;
        margin-top: 10px;
        padding-top: 6px;
        border-top: 1px dashed #e2e8f0;
    }

    /* Footer */
    .footer-container {
        margin-top: 45px;
        padding-top: 16px;
        border-top: 1px solid #e2e8f0;
        text-align: center;
        font-size: 13px;
        color: #64748b;
    }
    .footer-sources {
        font-size: 11.5px;
        color: #94a3b8;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'processed')
PASSAGES_FILE = os.path.join(DATA_DIR, 'passages.jsonl')
INDEX_FILE = os.path.join(DATA_DIR, 'index.pkl')
METRICS_FILE = os.path.join(BASE_DIR, 'results', 'metrics.json')

@st.cache_resource
def load_corpus_and_index():
    if not os.path.exists(PASSAGES_FILE) or not os.path.exists(INDEX_FILE):
        return None, None, None, "Legal corpus not ready (index or passages missing)"

    try:
        index_obj = InvertedIndex.load(INDEX_FILE)
        passages = {}
        with open(PASSAGES_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                p = json.loads(line)
                passages[p['passage_id']] = p

        if len(passages) < 200:
            return None, None, None, f"Legal corpus not ready (insufficient passages: {len(passages)} < 200)"

        models = {
            'BM25': BM25Ranker(index_obj, k1=1.5, b=0.75),
            'TF-IDF': TFIDFRanker(index_obj),
            'QL-Dirichlet': LanguageModelRanker(index_obj, smoothing='dirichlet', mu=1000),
            'QL-Jelinek-Mercer': LanguageModelRanker(index_obj, smoothing='jm', lambda_jm=0.5)
        }
        return index_obj, passages, models, "OK"
    except Exception as e:
        return None, None, None, f"Legal corpus not ready ({str(e)})"

index_obj, passages_dict, models_dict, health_status = load_corpus_and_index()

# 1. Header (Updated as requested)
st.title("⚖️ Consumer Rights Helper")
st.markdown("<p style='font-size: 16.5px; color: #475569; margin-top: -6px; margin-bottom: 22px;'>Understand your rights and get guidance based on Indian consumer law.</p>", unsafe_allow_html=True)

if health_status != "OK":
    st.error(f"⚠️ {health_status}")
    st.stop()

def highlight_terms(text, query):
    tokens = preprocess(query)
    if not tokens:
        return text
    escaped_tokens = [re.escape(t) for t in set(tokens) if len(t) >= 2]
    if not escaped_tokens:
        return text
    pattern = re.compile(rf'\b({"|".join(escaped_tokens)}[a-z]*)\b', re.IGNORECASE)
    return pattern.sub(r'<mark class="highlight">\1</mark>', text)

def format_passage_lines(text):
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    pattern = re.compile(r'(?<!\n)(?<=\S)[\t ]+(\((?:[a-z]|\d+|[ivx]+)\)\s+)', re.IGNORECASE)
    formatted = pattern.sub(r'\n\1', text)
    lines = [line.strip() for line in formatted.split('\n') if line.strip()]
    return lines

# Food context keywords
FOOD_CONTEXT_KEYWORDS = [
    'food', 'juice', 'milk', 'snack', 'snacks', 'biscuit', 'biscuits', 'cookie', 'cookies',
    'bread', 'grocery', 'groceries', 'meal', 'beverage', 'drink', 'drinks', 'edible',
    'bakery', 'sweet', 'sweets', 'meat', 'chicken', 'fish', 'vegetable', 'vegetables',
    'fruit', 'fruits', 'packaged food', 'packaged drink', 'packaged water', 'mineral water',
    'flour', 'atta', 'rice', 'dal', 'oil', 'butter', 'cheese', 'paneer', 'ice cream', 'chocolate',
    'restaurant', 'cafe', 'hotel food', 'canteen', 'dhaba'
]

# Food safety violation keywords (contamination, spoilage, illness, hygiene hazards)
FOOD_SAFETY_KEYWORDS = [
    'expired', 'expiry', 'spoil', 'spoiled', 'rotten', 'fungus', 'mold',
    'contaminated', 'contamination', 'food poisoning', 'poisoning',
    'stale', 'insect', 'insects', 'worm', 'worms', 'maggot', 'maggots',
    'stone', 'glass', 'foreign matter', 'foreign object', 'foreign body',
    'unhygienic', 'adulterated', 'adulteration', 'vomit', 'vomiting', 'sick',
    'illness', 'hospital', 'hospitalized', 'stomach ache', 'stomach pain',
    'fssai', 'substandard food', 'harmful', 'unsafe food', 'unsafe',
    'foul smell', 'foul taste', 'dead insect', 'cockroach', 'dead fly', 'lizard'
]

def is_food_safety_issue(text):
    """
    Checks if a complaint involves genuine food safety violations (contamination,
    expiry, spoilage, or hygiene hazards requiring FSSAI intervention).
    Excludes regular restaurant billing, delivery fee, or refund disputes.
    """
    text_lower = text.lower()
    if 'fssai' in text_lower or 'food safety' in text_lower or 'food poisoning' in text_lower:
        return True
    has_food = any(re.search(r'\b' + re.escape(kw) + r'\b', text_lower) for kw in FOOD_CONTEXT_KEYWORDS)
    has_hazard = any(re.search(r'\b' + re.escape(kw) + r'\b', text_lower) for kw in FOOD_SAFETY_KEYWORDS)
    return has_food and has_hazard

def is_food_related(text):
    return is_food_safety_issue(text)

UNRELATED_PATTERNS = [
    r'\b(?:binary\s+search|linear\s+search|bubble\s+sort|quick\s+sort|merge\s+sort)\b',
    r'\b(?:java|python|c\+\+|javascript|typescript|golang|rust|html|css|sql|react|angular)\b',
    r'\b(?:algorithm|programming|leetcode|data\s+structure|recursion|compiler|syntax)\b',
    r'\b(?:write\s+(?:a\s+)?code|write\s+(?:a\s+)?program|debug\s+my\s+code)\b',
    r'\b(?:what\s+is\s+the\s+weather|weather\s+today|temperature\s+in)\b',
    r'\b(?:solve\s+(?:the\s+)?equation|quadratic\s+equation|calculus|derivative|integral)\b',
    r'\b(?:who\s+is\s+the\s+president|capital\s+of|tell\s+me\s+a\s+joke)\b',
    r'^(?:hi|hello|hey|howdy|good\s+(?:morning|afternoon|evening)|how\s+are\s+you)\b'
]

HEALTH_SYMPTOM_PATTERNS = [
    r'\b(?:i\s+have\s+(?:a\s+)?(?:headache|fever|cough|cold|stomach\s*ache|body\s*pain|chest\s*pain|migraine))\b',
    r'\b(?:my\s+(?:head|stomach|chest|throat|back|leg|eye)\s+(?:hurts|aches))\b',
    r'\b(?:symptoms\s+of|how\s+to\s+cure|how\s+to\s+treat|treatment\s+for|remedy\s+for\s+(?:cold|fever|headache))\b'
]

def is_personal_health_query(text):
    """
    Identifies pure personal health symptoms without commercial merchant context.
    """
    text_lower = text.strip().lower()
    has_commercial = any(cue in text_lower for cue in [
        'bought', 'purchased', 'ordered', 'medicine', 'drug', 'tablet', 'pill',
        'doctor', 'hospital', 'clinic', 'food', 'juice', 'milk', 'expired', 'seller', 'chemist', 'pharmacy'
    ])
    if has_commercial:
        return False
    return any(re.search(pat, text_lower) for pat in HEALTH_SYMPTOM_PATTERNS)

CIVIC_GRIEVANCE_PATTERNS = [
    r'\b(?:municipal\s+corporation|municipality|nagar\s+nigam|nagar\s+palika|panchayat|pwd|public\s+works\s+department)\b',
    r'\b(?:pothole|potholes|street\s*light|street\s*lights|drainage|sewage|sewer|garbage\s+collection|public\s+road|broken\s+road)\b'
]

def is_civic_grievance(text):
    """
    Identifies statutory civic governance issues (roads, potholes, municipal duties)
    outside Consumer Protection Act commercial jurisdiction.
    """
    text_lower = text.strip().lower()
    has_civic_authority = any(re.search(pat, text_lower) for pat in CIVIC_GRIEVANCE_PATTERNS[:1])
    has_civic_infrastructure = any(re.search(pat, text_lower) for pat in CIVIC_GRIEVANCE_PATTERNS[1:])
    return has_civic_authority or (has_civic_infrastructure and not any(k in text_lower for k in ['bought', 'paid', 'ordered', 'builder', 'developer', 'society']))

def is_tenancy_query(text):
    """
    Identifies tenancy / residential rent disputes requiring jurisdiction qualification.
    """
    text_lower = text.strip().lower()
    tenancy_terms = ['landlord', 'tenant', 'tenancy', 'rent agreement', 'security deposit', 'rental deposit', 'flat rent', 'house rent', 'pg deposit']
    return any(re.search(r'\b' + re.escape(t) + r'\b', text_lower) for t in tenancy_terms)

def is_unrelated_query(text):
    """
    Politely identifies queries outside Indian consumer law (programming, math, general trivia, greetings).
    """
    text_clean = text.strip().lower()
    for pat in UNRELATED_PATTERNS:
        if re.search(pat, text_clean):
            if re.search(r'\b(?:promo|discount|coupon)\s+code\b', text_clean):
                continue
            return True
    if text_clean in ['hi', 'hello', 'hey', 'help', 'test']:
        return True
    return False

def is_ambiguous_complaint(text):
    """
    Identifies vague grievances lacking key facts (e.g., 'They took my money') to prompt for clarification.
    """
    if is_unrelated_query(text) or is_personal_health_query(text) or is_civic_grievance(text):
        return False
    text_clean = text.strip()
    words = re.findall(r'\b\w+\b', text_clean.lower())

    specific_cues = [
        'phone', 'mobile', 'laptop', 'tv', 'fridge', 'refrigerator', 'car', 'bike',
        'machine', 'shoes', 'dress', 'clothes', 'flight', 'airline', 'ticket', 'train',
        'hotel', 'bank', 'account', 'card', 'loan', 'insurance', 'policy', 'hospital',
        'doctor', 'courier', 'parcel', 'amazon', 'flipkart', 'zomato', 'swiggy',
        'supermarket', 'store', 'shop', 'dealer', 'builder', 'flat', 'apartment',
        'broadband', 'sim', 'recharge', 'food', 'milk', 'juice', 'meal', 'medicine',
        'warranty', 'delivery', 'repair', 'screen', 'mrp', 'ad', 'advertisement',
        'deposit', 'landlord', 'tenant'
    ]
    has_specific = any(cue in words for cue in specific_cues)

    if len(words) <= 5 and not has_specific:
        return True

    vague_phrases = [
        r'^(?:they|someone|he|she)\s+(?:took|stole|deducted)\s+my\s+money\??$',
        r'^(?:i\s+(?:was|got)\s+cheated\??)$',
        r'^(?:money\s+deducted\??)$',
        r'^(?:cheated\s+me\??)$',
        r'^(?:they\s+cheated\s+me\??)$',
        r'^(?:fraud\s+happened\??)$',
        r'^(?:i\s+have\s+an?\s+issue\??)$',
        r'^(?:my\s+money\s+(?:was\s+)?stolen\??)$'
    ]
    for vp in vague_phrases:
        if re.match(vp, text_clean.lower().strip()):
            return True

    return False

def detect_complaint_category(text):
    text_lower = text.lower()
    if is_food_safety_issue(text):
        return 'food'
    if 'washing machine' in text_lower:
        return 'goods'
    if 'builder' in text_lower or 'delayed possession' in text_lower or 'possession' in text_lower or 'flat' in text_lower or is_tenancy_query(text):
        return 'service'
    goods_kw = ['product', 'goods', 'machine', 'device', 'phone', 'smartphone', 'mobile', 'screen', 'fridge', 'laptop', 'item', 'defect', 'defective', 'spinning', 'clothes', 'shoe', 'shoes', 'appliance', 'vehicle', 'car', 'bike', 'hardware']
    serv_kw = ['service', 'airline', 'flight', 'ticket', 'hotel', 'travel', 'broadband', 'internet', 'telecom', 'bank', 'banking', 'insurance', 'hospital', 'doctor', 'courier', 'subscription', 'delay', 'landlord', 'tenant', 'deposit']
    g_score = sum(1 for k in goods_kw if k in text_lower)
    s_score = sum(1 for k in serv_kw if k in text_lower)
    if g_score > s_score:
        return 'goods'
    elif s_score > g_score:
        return 'service'
    return 'unclear'

def get_simple_law_explanation(doc_id, breadcrumb, text):
    did = doc_id.lower()
    b_lower = breadcrumb.lower()
    t_lower = text.lower()

    if "cpa_s35" in did or "s35" in b_lower:
        return "Explains how to file a formal consumer complaint, who can file, and allows filing electronically through e-Daakhil or within your local district."
    elif "cpa_s39" in did or "s39" in b_lower:
        return "Lists the statutory remedies the Consumer Commission can order, including full refund with interest, replacement of goods, removal of defects, and compensation for loss or hardship."
    elif "cpa_s34" in did or "s34" in b_lower or "jr_r" in did or "jurisdiction" in b_lower:
        return "Determines pecuniary and territorial jurisdiction—ensuring you file in the appropriate Commission (District, State, or National) based on the amount paid."
    elif "cpa_s69" in did or "s69" in b_lower:
        return "Defines the 2-year statutory limitation period to file your consumer complaint from the date the dispute arose."
    elif "cpa_s2_" in did or "cpa_s2" in did or "definition" in b_lower:
        if "defect" in t_lower:
            return "Defines legal 'defect'—any fault, imperfection, or shortcoming in the quality, quantity, potency, or standard of goods."
        elif "deficiency" in t_lower:
            return "Defines legal 'deficiency'—any fault, imperfection, or inadequacy in the quality, nature, and manner of service performance."
        elif "unfair" in t_lower:
            return "Defines 'unfair trade practice'—protects consumers against deceptive statements, fake bargains, and misleading representations."
        elif "misleading" in t_lower:
            return "Defines 'misleading advertisement'—prohibits false descriptions, deceptive guarantees, and unverified claims."
        return "Defines key consumer protections, terms, and obligations under the Consumer Protection Act, 2019."
    elif "ecr_" in did or "e-commerce" in b_lower or "commerce" in b_lower:
        return "Establishes mandatory obligations for online platforms and sellers, prohibiting unfair cancellation fees, fake reviews, and requiring prompt refunds and grievance handling."
    elif "dp_" in did or "dark pattern" in b_lower:
        return "Prohibits deceptive digital UI tricks (dark patterns) such as hidden fees, pre-ticked add-ons, drip pricing, and false urgency countdowns."
    elif "mag_" in did or "misleading ad" in b_lower:
        return "Regulates advertisements and endorsements—holding brands and endorsers liable for unsubstantiated claims or bait pricing."
    elif "cpa_s89" in did or "cpa_s90" in did:
        return "Imposes strict penalties, fines, and criminal liability for false advertising or manufacturing adulterated and spurious goods."
    else:
        return "Provides statutory safeguards and legal duties governing this specific consumer dispute."

def generate_complaint_draft(query_text, guidance):
    has_amount = bool(guidance.get('raw_match') and guidance.get('amount') is not None)

    if has_amount:
        amount_val = guidance['raw_match']
        forum_tier = guidance.get('forum_tier')
        if forum_tier == 'State Commission':
            forum_heading = "STATE CONSUMER DISPUTES REDRESSAL COMMISSION"
            forum_location = "[district / city name, state]"
            pecuniary_text = f"The total value of goods or services paid as consideration is {amount_val}. This Hon'ble Commission has pecuniary jurisdiction under Section 34 of the Consumer Protection Act, 2019 and Rule 4 of the Consumer Protection (Jurisdiction of the District Commission, the State Commission and the National Commission) Rules, 2021 (consideration exceeds fifty lakh rupees but does not exceed two crore rupees)."
        elif forum_tier == 'National Commission':
            forum_heading = "NATIONAL CONSUMER DISPUTES REDRESSAL COMMISSION"
            forum_location = "NEW DELHI"
            pecuniary_text = f"The total value of goods or services paid as consideration is {amount_val}. This Hon'ble Commission has pecuniary jurisdiction under Section 34 of the Consumer Protection Act, 2019 and Rule 5 of the Consumer Protection (Jurisdiction of the District Commission, the State Commission and the National Commission) Rules, 2021 (consideration exceeds two crore rupees)."
        else:
            forum_heading = "DISTRICT CONSUMER DISPUTES REDRESSAL COMMISSION"
            forum_location = "[district / city name, state]"
            pecuniary_text = f"The total value of goods or services paid as consideration is {amount_val}. This Hon'ble Commission has pecuniary jurisdiction under Section 34 of the Consumer Protection Act, 2019 and Rule 3 of the Consumer Protection (Jurisdiction of the District Commission, the State Commission and the National Commission) Rules, 2021 (consideration does not exceed fifty lakh rupees)."
        refund_line = f"To refund the price paid, with interest [Section 39(1)(c)] ({amount_val});"
    else:
        forum_heading = "DISTRICT CONSUMER DISPUTES REDRESSAL COMMISSION"
        forum_location = "[district / city name, state]"
        pecuniary_text = "The total value of goods or services paid as consideration is [amount paid]. Pecuniary jurisdiction is governed by Section 34 of the Consumer Protection Act, 2019 and Rules 3-5 of the Consumer Protection (Jurisdiction of the District Commission, the State Commission and the National Commission) Rules, 2021 (Rule 3 for consideration up to fifty lakh rupees; Rule 4 for consideration between fifty lakh and two crore rupees; Rule 5 for consideration exceeding two crore rupees)."
        refund_line = "To refund the price paid, with interest [Section 39(1)(c)];"

    defect_cues = ["defect", "defective", "faulty", "broken", "not working", "damaged", "stopped", "poor quality"]
    text_lower = query_text.lower()
    has_defect_cue = any(cue in text_lower for cue in defect_cues)

    category = detect_complaint_category(query_text)
    if category == 'goods' or category == 'food':
        prayer_a = "To remove the defect from the goods [Section 39(1)(a)];"
    elif category == 'service':
        prayer_a = "To remove the deficiency in the service [Section 39(1)(a)];"
    else:
        prayer_a = "To remove the defect from the goods / deficiency in the service [Section 39(1)(a)];"

    if has_defect_cue or category == 'food':
        reliefs_block = f"""(a) {prayer_a}
(b) To replace the goods with new goods free from defects [Section 39(1)(b)];
(c) {refund_line}
(d) To pay compensation for loss, injury, or hardship suffered [Section 39(1)(d)]."""
    else:
        reliefs_block = f"""(a) {refund_line}
(b) To pay compensation for loss, injury, or hardship suffered [Section 39(1)(d)]."""

    return f"""Template draft, not legal advice.

BEFORE THE HON'BLE {forum_heading}
AT {forum_location}

CONSUMER COMPLAINT NO. ______ OF 2026
(Filed under Section 35 of the Consumer Protection Act, 2019)

IN THE MATTER OF:

[complainant name]
Address: [complainant address]
Phone: [contact number] | Email: [email]
                                                    ... COMPLAINANT

VERSUS

[seller name]
Address: [seller address]
                                                    ... OPPOSITE PARTY

MEMORANDUM OF COMPLAINT UNDER SECTION 35 OF THE CONSUMER PROTECTION ACT, 2019

The Complainant respectfully states:

1. PARTIES:
The Complainant is filing this complaint against the Opposite Party [seller name] under Section 35 of the Consumer Protection Act, 2019 in relation to goods sold/delivered or services provided/agreed to be provided.

2. STATEMENT OF FACTS & GRIEVANCE:
{query_text.strip()}

3. PECUNIARY JURISDICTION:
{pecuniary_text}

4. TERRITORIAL JURISDICTION:
This Hon'ble Commission has territorial jurisdiction under Section 34 of the Consumer Protection Act, 2019 as the Complainant resides or personally works for gain, or the cause of action wholly or in part arose, within the local limits of this Hon'ble Commission.

5. LIMITATION PERIOD:
The cause of action arose on [date]. This complaint is being filed within two years of that date, as required by Section 69 of the Consumer Protection Act, 2019. [Confirm before filing]

6. RELIEFS SOUGHT:
Under Section 39 of the Consumer Protection Act, 2019, the Complainant respectfully prays for the following reliefs:
{reliefs_block}

PLACE: [district / city name, state]
DATE: [date]

                                                    ___________________________
                                                    (SIGNATURE OF COMPLAINANT)
                                                    [complainant name]

VERIFICATION:
I, [complainant name], verify that the contents of this complaint are true to my knowledge and belief.
Verified at [district / city name, state] on [date].

                                                    ___________________________
                                                    (SIGNATURE OF COMPLAINANT)
"""

def generate_plain_summary(query_text, guidance):
    amt = guidance.get('raw_match') or "Amount unspecified"
    forum = guidance.get('forum_name') or "District Consumer Commission"
    clean_q = query_text.strip()
    return f"""📌 CONSUMER COMPLAINT SUMMARY
--------------------------------------------------
• Grievance Description : {clean_q}
• Transaction / Loss     : {amt}
• Appropriate Court     : {forum}
• Key Statutory Right   : Right to Redressal (Section 2(9), Consumer Protection Act 2019)
• Limitation Period     : 2 Years from incident date (Section 69, CPA 2019)
• Recommended Next Step : Send formal written escalation to seller; file on edaakhil.nic.in if unresolved.
"""

def generate_seller_email(query_text, guidance):
    amt = guidance.get('raw_match') or "[Amount Paid]"
    clean_q = query_text.strip()
    return f"""Subject: URGENT: Grievance Redressal Notice regarding Purchase / Service - {amt}

Dear Customer Support / Grievance Officer,

I am writing regarding a transaction of {amt} where I experienced the following grievance:
"{clean_q}"

Under the Consumer Protection Act, 2019 and E-Commerce Rules, 2020, this constitutes a deficiency of service / defect in goods.

I request you to immediately resolve this matter by issuing a full refund / replacement within 7 working days. Failing this, I will be compelled to lodge a formal complaint on the National Consumer Helpline (1915) and before the Consumer Commission via e-Daakhil.

Sincerely,
[Your Name]
[Your Phone Number]
"""

# Check for dev mode in query parameters: ?dev=1
is_dev_mode = False
try:
    if hasattr(st, "query_params"):
        is_dev_mode = (st.query_params.get("dev") == "1")
except Exception:
    is_dev_mode = False

if is_dev_mode:
    with st.expander("⚙️ Advanced", expanded=False):
        selected_model = st.selectbox(
            "Retrieval Model:",
            options=["BM25", "TF-IDF", "QL-Dirichlet", "QL-Jelinek-Mercer"],
            index=0
        )
        st.caption("Default model works best for most complaints.")
else:
    selected_model = "BM25"

# 2. Input Section
if "complaint_input" not in st.session_state:
    st.session_state["complaint_input"] = ""
if "has_searched" not in st.session_state:
    st.session_state["has_searched"] = False
if "last_audio" not in st.session_state:
    st.session_state["last_audio"] = None

def set_example_complaint(text):
    st.session_state["complaint_input"] = text
    st.session_state["has_searched"] = False

input_tab1, input_tab2 = st.tabs(["✍️ Type Complaint", "🗣️ Voice Input (Microphone)"])

with input_tab2:
    audio_val = st.audio_input("Click the microphone to record your complaint:")
    if audio_val is not None and audio_val != st.session_state.get("last_audio"):
        st.session_state["last_audio"] = audio_val
        transcribed = None
        error_msg = None
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            with sr.AudioFile(audio_val) as source:
                audio_data = recognizer.record(source)
                transcribed = recognizer.recognize_google(audio_data)
        except Exception as e:
            try:
                import speech_recognition as sr
                if isinstance(e, sr.UnknownValueError):
                    error_msg = "Could not understand audio. Please speak clearly into the microphone and try again, or type your complaint in the 'Type Complaint' tab."
                elif isinstance(e, sr.RequestError):
                    error_msg = "Speech recognition service could not be reached. Please check your internet connection, or type your complaint in the 'Type Complaint' tab."
                else:
                    error_msg = "Voice transcription was unsuccessful. You can retry recording or type your complaint in the 'Type Complaint' tab."
            except Exception:
                error_msg = "Voice transcription was unsuccessful. You can retry recording or type your complaint in the 'Type Complaint' tab."

        if transcribed and transcribed.strip():
            st.session_state["complaint_input"] = transcribed.strip()
            st.session_state["has_searched"] = False
            st.success(f"🎙️ Transcribed: \"{transcribed.strip()}\"")
            st.info("👉 You can review or edit the transcribed text in the '✍️ Type Complaint' tab, then click '🔍 Analyze Complaint'.")
        else:
            msg = error_msg or "Could not transcribe audio. Please retry recording or type your complaint directly in the 'Type Complaint' tab."
            st.warning(f"⚠️ {msg}")

with input_tab1:
    query_text = st.text_area(
        "Describe your consumer complaint:",
        key="complaint_input",
        placeholder="Describe your problem in simple language (e.g. what you bought, what went wrong, and amount paid).",
        height=120,
        label_visibility="collapsed"
    )

# Primary Action Button (Blue #2563EB)
search_clicked = st.button("🔍 Analyze Complaint", type="primary", use_container_width=True)

# 6 Clickable Example Complaints below the box
st.markdown("<div style='margin-top: 14px; margin-bottom: 8px; font-size: 14px; font-weight: 600; color: #475569;'>Try an example:</div>", unsafe_allow_html=True)

EX_DEFECTIVE = "I bought a smartphone for Rs 22,000, but the screen stopped working within 10 days. The service center refused to repair or replace it under warranty."
EX_SHOPPING = "I ordered shoes for Rs 3,500 from an online e-commerce website, but received counterfeit fake items and the seller refused to process my refund."
EX_FOOD = "I bought packaged juice and milk for Rs 350 from a supermarket, but both items were expired and spoiled, causing severe stomach ache."
EX_OVERCHARGING = "The local store charged Rs 150 for a cold drink bottle whose printed Maximum Retail Price (MRP) was only Rs 95."
EX_MISLEADING_AD = "A fairness cream advertised 100% permanent results in 7 days, but after paying Rs 1,200 and using it for 2 months, there was zero effect and fake claims."
EX_SERVICE = "I booked an airline flight ticket for Rs 12,500, which was canceled without any notice or alternative, and the airline refused to refund my ticket price."

row1_col1, row1_col2, row1_col3 = st.columns(3)
with row1_col1:
    st.markdown('<div class="example-btn">', unsafe_allow_html=True)
    st.button("📱 Defective Product", on_click=set_example_complaint, args=(EX_DEFECTIVE,), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
with row1_col2:
    st.markdown('<div class="example-btn">', unsafe_allow_html=True)
    st.button("🛒 Online Shopping Fraud", on_click=set_example_complaint, args=(EX_SHOPPING,), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
with row1_col3:
    st.markdown('<div class="example-btn">', unsafe_allow_html=True)
    st.button("🍔 Expired Food Product", on_click=set_example_complaint, args=(EX_FOOD,), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

row2_col1, row2_col2, row2_col3 = st.columns(3)
with row2_col1:
    st.markdown('<div class="example-btn">', unsafe_allow_html=True)
    st.button("💸 Overcharging", on_click=set_example_complaint, args=(EX_OVERCHARGING,), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
with row2_col2:
    st.markdown('<div class="example-btn">', unsafe_allow_html=True)
    st.button("📢 Misleading Advertisement", on_click=set_example_complaint, args=(EX_MISLEADING_AD,), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
with row2_col3:
    st.markdown('<div class="example-btn">', unsafe_allow_html=True)
    st.button("🏦 Service Deficiency", on_click=set_example_complaint, args=(EX_SERVICE,), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Process search state
if search_clicked:
    if query_text.strip():
        st.session_state["has_searched"] = True
    else:
        st.session_state["has_searched"] = False

if not query_text.strip():
    st.session_state["has_searched"] = False

if search_clicked and not query_text.strip():
    st.info("👋 Please describe your problem above or click one of the examples to see your rights.")
elif st.session_state["has_searched"] and query_text.strip():
    # 1. Unrelated Queries Check (Politely reject questions outside consumer rights)
    if is_unrelated_query(query_text):
        st.info("""
        ℹ️ **This question appears to be outside consumer rights law.**

        Consumer Rights Helper assists Indian consumers with disputes regarding:
        • Defective goods and refused warranty repairs
        • Deficient commercial services (airlines, banking, broadband, hotels)
        • E-commerce fraud, delivery delays, and refund disputes
        • MRP overcharging, hidden charges, and misleading advertisements
        • Food safety, adulteration, expired products, and contamination

        If you have a grievance with a seller, merchant, or service provider, please describe your consumer issue.
        """)
    # 2. Personal Health Symptoms Check
    elif is_personal_health_query(query_text):
        st.info("""
        ℹ️ **This appears to be a personal health or medical symptom question, not a commercial consumer dispute.**

        Consumer Rights Helper assists with consumer disputes against sellers, manufacturers, or commercial service providers (such as adulterated food, expired medicines sold by a chemist, or billing malpractice by a hospital).

        • For personal medical symptoms or healthcare advice, please consult a qualified doctor or healthcare professional.
        """)
    # 3. Civic / Municipal Grievance Check
    elif is_civic_grievance(query_text):
        st.info("""
        ℹ️ **This appears to be a civic or municipal governance issue, rather than a commercial consumer transaction.**

        Under the Consumer Protection Act, 2019, statutory civic functions performed by municipal corporations (such as maintaining public roads, repairing potholes, street lighting, or public sanitation) are not commercial services rendered for consideration.

        • **Where to report civic issues:**
        • File a grievance with your local **Municipal Corporation / Nagar Nigam** or ward office.
        • Lodge a grievance on the Central Government Public Grievance Portal: [CPGRAMS (pgportal.gov.in)](https://pgportal.gov.in/).
        """)
    # 4. Ambiguous Complaints Check (Ask one short clarification question when unclear)
    elif is_ambiguous_complaint(query_text):
        st.warning("""
        ⚠️ **Your complaint is unclear or missing key facts.**

        **Clarification Question:** Could you tell us what specific product or service you paid for, who the seller or company was, and what went wrong?

        *Examples of complete complaints:*
        • *"I bought a smartphone for Rs 22,000, but the screen stopped working and the service center refused repair under warranty."*
        • *"I ordered shoes for Rs 3,500 online, but received fake items and the seller refused my refund."*
        """)
    else:
        with st.spinner("Finding relevant consumer rights and legal provisions..."):
            # 1. Retrieval
            model = models_dict[selected_model]
            user_tokens = preprocess(query_text)
            query_tokens = expand_query(query_text, user_tokens=user_tokens)

            if not query_tokens:
                scored_results = []
            else:
                scored = model.score(query_tokens)
                # Calibrated relevance threshold:
                # Based on 28 benchmark consumer complaints (minimum score 7.05, median 15.33),
                # queries with top BM25 score below 5.5 represent weak or incidental token matches.
                if selected_model == 'BM25':
                    min_threshold = 5.5
                elif selected_model == 'TF-IDF':
                    min_threshold = 0.04
                else:
                    min_threshold = -150.0  # Log-prob threshold for LM

                scored_results = [s for s in scored if s[1] >= min_threshold]

            top_5 = scored_results[:5]

            if not top_5:
                st.info("ℹ️ We could not find sufficiently relevant legal provisions in our corpus matching this specific complaint. Please describe what you bought or the service you used, what went wrong, and how much you paid, or contact the National Consumer Helpline at 1915.")
            else:
                # 2. Guidance Resolution
                guidance = get_forum_guidance(query_text)
                category = detect_complaint_category(query_text)
                food_flag = is_food_safety_issue(query_text)
                is_tenancy = is_tenancy_query(query_text)

                raw_amt = guidance.get('raw_match')
                if raw_amt:
                    raw_clean = raw_amt.strip()
                    if not re.match(r'^(?:rs\.?|inr|₹)', raw_clean, re.I):
                        amt_display = f"Rs {raw_clean}"
                    else:
                        amt_display = re.sub(r'^(?:₹|inr\s*|rs\.?\s*)', 'Rs ', raw_clean, flags=re.I)
                elif guidance.get('amount'):
                    amt_display = f"Rs {guidance['amount']:,.0f}"
                else:
                    amt_display = None

                forum_name_full = guidance.get('forum_name') or 'District Consumer Commission'
                if "State" in forum_name_full:
                    short_forum = "State Consumer Commission"
                elif "National" in forum_name_full:
                    short_forum = "National Consumer Commission"
                else:
                    short_forum = "District Consumer Commission"

                amt_str = amt_display or "your claim amount"
                if guidance.get('raw_match'):
                    simple_forum_reason = f"Based on your claim of {amt_str}, your case falls under the {short_forum} (file where you live, where the transaction happened, or online)."
                else:
                    simple_forum_reason = f"For claims up to ₹50 Lakh, file with the {short_forum} (file where you live, where the transaction happened, or online)."

                if food_flag:
                    issue_title = "Expired / Unsafe Food Product"
                    type_label = "Food / Consumable"
                elif is_tenancy:
                    issue_title = "Security Deposit / Tenancy Dispute"
                    type_label = "Commercial Accommodation / Service"
                elif category == "goods":
                    issue_title = "Defective Goods"
                    type_label = "Goods / Physical Product"
                elif category == "service":
                    issue_title = "Deficiency in Service"
                    type_label = "Commercial Service"
                else:
                    issue_title = "Consumer Grievance"
                    type_label = "Unspecified / General"

                amt_text = amt_display if amt_display else "Not specified in text"

                # =========================================================================
                # 1. WHAT WE UNDERSTOOD
                # =========================================================================
                st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
                st.markdown("### 1. What We Understood")

                if is_tenancy:
                    st.markdown("""
                    <div style="background-color: #fefce8; border: 1px solid #fef08a; border-radius: 10px; padding: 14px 16px; margin-top: 6px; margin-bottom: 12px;">
                        <div style="font-weight: 700; color: #854d0e; font-size: 15px;">🏠 Tenancy & Security Deposit Jurisdiction Notice</div>
                        <div style="font-size: 13.5px; color: #713f12; margin-top: 5px; line-height: 1.5;">
                            <b>Jurisdiction depends on the nature of the tenancy:</b>
                            <ul style="margin: 4px 0 6px 18px; padding: 0;">
                                <li><b>Private Residential Leases:</b> Disputes between individual landlords and tenants (e.g. residential flat rental) are governed by state Rent Control Acts and the Transfer of Property Act, 1882. Consumer Commissions generally do not entertain individual residential landlord-tenant disputes.</li>
                                <li><b>Commercial / Serviced Accommodations:</b> If you paid for a commercial paying guest (PG) facility, student hostel, serviced co-living platform, or property management agency providing hospitality and maintenance services for a fee, it may be entertained as a commercial deficiency of service under Section 2(11) of the Consumer Protection Act, 2019.</li>
                            </ul>
                            <i>The guidance below applies if your complaint involves a commercial serviced accommodation. For private residential leases, consider sending a formal legal notice or approaching the local civil court / Rent Authority.</i>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                col_u1, col_u2 = st.columns([1.25, 1])
                with col_u1:
                    st.markdown(f"""
                    <div class="metric-card metric-card-blue" style="margin-bottom: 8px;">
                        <div class="metric-label">Grievance & Transaction Summary</div>
                        <div class="metric-val" style="font-size: 18px;">✅ {issue_title}</div>
                        <div style="font-size: 14.5px; color: #334155; margin-top: 6px;">
                            <b>Category:</b> {type_label} &nbsp;|&nbsp; <b>Amount:</b> {amt_text}
                        </div>
                        <div style="font-size: 13px; color: #64748b; margin-top: 4px;">
                            Protected statutory consumer dispute under Section 2(9) of the Consumer Protection Act, 2019.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with col_u2:
                    st.markdown(f"""
                    <div class="metric-card metric-card-green" style="margin-bottom: 8px;">
                        <div class="metric-label" style="color: #047857;">Appropriate Redressal Commission</div>
                        <div class="metric-val" style="font-size: 18px;">🏛️ {short_forum}</div>
                        <div style="font-size: 14px; color: #334155; margin-top: 6px;">{simple_forum_reason}</div>
                        <div style="font-size: 13px; color: #b45309; font-weight: 600; margin-top: 4px;">
                            ⏳ Statutory Limitation: File within 2 years of incident (Sec 69).
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                if food_flag:
                    st.markdown("""
                    <div class="food-safety-card" style="margin-top: 6px; margin-bottom: 14px; padding: 14px 16px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 17px; font-weight: 700; color: #991b1b;">🍔 Food Safety Alert (FSSAI Regulatory Issue)</span>
                            <span style="background: #fee2e2; color: #b91c1c; font-weight: 700; padding: 2px 8px; border-radius: 12px; font-size: 12px;">High Priority</span>
                        </div>
                        <div style="font-size: 14px; color: #374151; margin-top: 6px; line-height: 1.5;">
                            This complaint involves an unsafe, contaminated, or expired consumable. While financial refund/compensation is pursued through consumer courts, food safety and hygiene violations must also be reported to <b>FSSAI (Food Safety and Standards Authority of India)</b>.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                # =========================================================================
                # 2. WHAT YOU CAN DO
                # =========================================================================
                st.markdown("### 2. What You Can Do")

                defect_cues = ["defect", "defective", "faulty", "broken", "not working", "damaged", "stopped", "poor quality", "leaking", "crack"]
                has_defect = any(cue in query_text.lower() for cue in defect_cues)

                rem1, rem2, rem3, rem4 = st.columns(4)
                with rem1:
                    st.markdown("""
                    <div class="remedy-tile" style="padding: 12px 10px;">
                        <div>
                            <div style="font-size: 26px;">💰</div>
                            <div style="font-weight: 700; font-size: 14.5px; margin-top: 2px;">Refund</div>
                            <div style="font-size: 12px; color: #64748b;">Full price + interest [Sec 39(1)(c)]</div>
                        </div>
                        <div class="remedy-badge-active">✅ Recommended</div>
                    </div>
                    """, unsafe_allow_html=True)
                with rem2:
                    replace_app = (category == "goods" or food_flag or has_defect)
                    b_cls = "remedy-badge-active" if replace_app else "remedy-badge-inactive"
                    b_txt = "✅ Applicable" if replace_app else "⚪ Alternative"
                    st.markdown(f"""
                    <div class="remedy-tile" style="padding: 12px 10px;">
                        <div>
                            <div style="font-size: 26px;">🔄</div>
                            <div style="font-weight: 700; font-size: 14.5px; margin-top: 2px;">Replacement</div>
                            <div style="font-size: 12px; color: #64748b;">Defect-free new unit [Sec 39(1)(b)]</div>
                        </div>
                        <div class="{b_cls}">{b_txt}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with rem3:
                    repair_app = (category == "goods" and has_defect and not food_flag)
                    b_cls = "remedy-badge-active" if repair_app else "remedy-badge-inactive"
                    b_txt = "✅ Applicable" if repair_app else "⚪ Not Applicable"
                    st.markdown(f"""
                    <div class="remedy-tile" style="padding: 12px 10px;">
                        <div>
                            <div style="font-size: 26px;">🛠️</div>
                            <div style="font-weight: 700; font-size: 14.5px; margin-top: 2px;">Repair</div>
                            <div style="font-size: 12px; color: #64748b;">Free defect removal [Sec 39(1)(a)]</div>
                        </div>
                        <div class="{b_cls}">{b_txt}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with rem4:
                    st.markdown("""
                    <div class="remedy-tile" style="padding: 12px 10px;">
                        <div>
                            <div style="font-size: 26px;">⚖️</div>
                            <div style="font-weight: 700; font-size: 14.5px; margin-top: 2px;">Compensation</div>
                            <div style="font-size: 12px; color: #64748b;">For hardship or loss [Sec 39(1)(d)]</div>
                        </div>
                        <div class="remedy-badge-active">✅ Applicable</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("""
                <div class="action-plan-container" style="margin-top: 14px; margin-bottom: 12px;">
                    <div class="action-plan-item">
                        <div class="action-plan-num">1</div>
                        <div class="action-plan-text">
                            <b>Preserve Bill & Proof:</b> Keep your purchase bill/receipt, photos/videos of defects or expired packaging, warranty card, and order communication.
                        </div>
                    </div>
                    <div class="action-plan-item">
                        <div class="action-plan-num">2</div>
                        <div class="action-plan-text">
                            <b>Send Written Notice to Seller:</b> Contact the company in writing (using our ready email draft below) demanding resolution within 7 working days.
                        </div>
                    </div>
                    <div class="action-plan-item">
                        <div class="action-plan-num">3</div>
                        <div class="action-plan-text">
                            <b>National Consumer Helpline (Toll-Free 1915):</b> If the seller ignores your request, register a pre-litigation grievance on consumerhelpline.gov.in for informal dispute mediation.
                        </div>
                    </div>
                    <div class="action-plan-item">
                        <div class="action-plan-num">4</div>
                        <div class="action-plan-text">
                            <b>File Online on e-Daakhil if Unresolved:</b> Submit a formal legal complaint before the Consumer Commission at edaakhil.nic.in.
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if food_flag:
                    col_next1, col_next2, col_next3 = st.columns(3)
                    with col_next1:
                        st.link_button("🥗 FSSAI Food Safety Connect", "https://foscos.fssai.gov.in/consumergrievance/", use_container_width=True)
                    with col_next2:
                        st.link_button("📞 National Consumer Helpline (1915)", "https://consumerhelpline.gov.in", use_container_width=True)
                    with col_next3:
                        st.link_button("🌐 e-Daakhil Online Filing", "https://edaakhil.nic.in", use_container_width=True)
                else:
                    col_next1, col_next2 = st.columns(2)
                    with col_next1:
                        st.link_button("📞 National Consumer Helpline (Call 1915)", "https://consumerhelpline.gov.in", use_container_width=True)
                    with col_next2:
                        st.link_button("🌐 File Online on e-Daakhil (edaakhil.nic.in)", "https://edaakhil.nic.in", use_container_width=True)

                # =========================================================================
                # 3. RELEVANT LAW & SOURCES
                # =========================================================================
                st.markdown("### 3. Relevant Law & Sources")

                col_r1, col_r2, col_r3 = st.columns(3)
                with col_r1:
                    st.markdown("""
                    <div class="rights-card">
                        <div class="rights-card-title">✅ Right to Safety</div>
                        <div class="rights-card-body">Protection against goods and services hazardous to life, health, or property.</div>
                        <div class="rights-card-cite">Section 2(9)(i), CPA 2019</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_r2:
                    st.markdown("""
                    <div class="rights-card">
                        <div class="rights-card-title">✅ Right to Information</div>
                        <div class="rights-card-body">Right to be informed about quality, quantity, potency, purity, and standard of goods.</div>
                        <div class="rights-card-cite">Section 2(9)(ii), CPA 2019</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_r3:
                    st.markdown("""
                    <div class="rights-card">
                        <div class="rights-card-title">✅ Right to Redressal</div>
                        <div class="rights-card-body">Right to seek remedies, replacement, full refund, and compensation for hardship.</div>
                        <div class="rights-card-cite">Section 2(9)(v), CPA 2019</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<div style='margin-top: 14px; margin-bottom: 6px; font-weight: 600; color: #1e3a8a;'>Applicable Statutory Provisions (Retrieved from Legal Corpus):</div>", unsafe_allow_html=True)

                for rank, (doc_id, _) in enumerate(top_5, 1):
                    passage_data = passages_dict.get(doc_id, {})
                    raw_text = passage_data.get('text', '')
                    breadcrumb = passage_data.get('metadata', {}).get('breadcrumb', doc_id)
                    doc_tag = passage_data.get('metadata', {}).get('doc', '')
                    simple_expl = get_simple_law_explanation(doc_id, breadcrumb, raw_text)
                    lines = format_passage_lines(raw_text)

                    st.markdown(f"""
                    <div class="law-card" style="margin-bottom: 6px; padding: 12px 14px;">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div class="law-card-title">⚖️ {breadcrumb}</div>
                            <span class="law-card-badge">Law {rank} of 5</span>
                        </div>
                        <div class="law-card-desc" style="font-size: 13.5px; margin-top: 4px;"><b>Why this applies:</b> {simple_expl}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    with st.expander(f"📖 View Legal Text — {breadcrumb}", expanded=False):
                        full_text = "\n".join(lines)
                        highlighted_body = highlight_terms(full_text, query_text)
                        st.markdown(f'<div class="passage-text">{highlighted_body}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="passage-caption">Passage ID: {doc_id} &nbsp;|&nbsp; Document: {doc_tag}</div>', unsafe_allow_html=True)

                # =========================================================================
                # 4. COMPLAINT DRAFT
                # =========================================================================
                st.markdown("### 4. Complaint Draft")
                st.caption("Pre-drafted, customized documents ready to copy or download:")

                with st.expander("⚖️ Formal Consumer Complaint Draft (Section 35, CPA 2019)", expanded=True):
                    st.caption("A structured formal complaint draft based on Section 35 of the Consumer Protection Act, 2019. Fill in any [bracketed blanks] before filing.")
                    complaint_draft = generate_complaint_draft(query_text, guidance)
                    st.code(complaint_draft, language="text")
                    st.download_button(
                        "📥 Download Consumer Complaint Draft (.txt)",
                        complaint_draft,
                        file_name="section_35_complaint_draft.txt",
                        mime="text/plain",
                        use_container_width=True
                    )

                with st.expander("✉️ Escalation Email to Seller", expanded=False):
                    st.caption("Send this pre-litigation resolution email directly to the seller or company grievance officer.")
                    email_draft = generate_seller_email(query_text, guidance)
                    st.code(email_draft, language="text")
                    st.download_button(
                        "📥 Download Escalation Email (.txt)",
                        email_draft,
                        file_name="seller_escalation_email.txt",
                        mime="text/plain",
                        use_container_width=True
                    )

                with st.expander("📋 Complaint Summary", expanded=False):
                    st.caption("A simple, non-legal summary of your grievance and key facts to organize your case.")
                    summary_text = generate_plain_summary(query_text, guidance)
                    st.code(summary_text, language="text")
                    st.download_button(
                        "📥 Download Complaint Summary (.txt)",
                        summary_text,
                        file_name="consumer_complaint_summary.txt",
                        mime="text/plain",
                        use_container_width=True
                    )

# Footer Line
st.markdown("""
<div class="footer-container">
    <div>Information from the retrieved legal text, not legal advice.</div>
    <div class="footer-sources">Sources: Consumer Protection Act 2019, Consumer Protection (E-Commerce) Rules 2020, Guidelines for Prevention and Regulation of Dark Patterns 2023, Consumer Protection (Jurisdiction Rules) 2021, Guidelines for Prevention of Misleading Advertisements 2022.</div>
</div>
""", unsafe_allow_html=True)
