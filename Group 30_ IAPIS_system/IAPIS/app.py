"""
IAPIS — Streamlit User Interface
Phase 8 implementation per project build specification.
Decoupled frontend that interacts with the FastAPI backend over HTTP.
"""

import io
import requests
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
DEFAULT_BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="IAPIS — Accident Prevention Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for styling
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #888;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    .report-card {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    .badge-high { background-color: #ef4444; color: white; }
    .badge-medium { background-color: #f59e0b; color: white; }
    .badge-low { background-color: #10b981; color: white; }
    .badge-info { background-color: #3b82f6; color: white; }
    .risk-box {
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border: 1px solid rgba(239, 68, 68, 0.3);
        background-color: rgba(239, 68, 68, 0.05);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Sidebar Configuration
# -----------------------------------------------------------------------------
st.sidebar.title("🛡️ IAPIS Controls")

backend_url = st.sidebar.text_input(
    "FastAPI Backend URL",
    value=DEFAULT_BACKEND_URL,
    help="URL where api.main:app is running",
)

# Health Check
try:
    health_resp = requests.get(f"{backend_url}/health", timeout=2)
    if health_resp.status_code == 200 and health_resp.json().get("status") == "ok":
        st.sidebar.success("● Backend Connected")
    else:
        st.sidebar.warning(f"Backend returned status {health_resp.status_code}")
except Exception:
    st.sidebar.error("Backend Disconnected. Start with: `uvicorn api.main:app --port 8000`")

st.sidebar.subheader("Retrieval Settings")
top_k = st.sidebar.slider(
    "Top K Results",
    min_value=1,
    max_value=20,
    value=5,
    help="Number of historical accident reports to retrieve",
)

alpha = st.sidebar.slider(
    "Hybrid Alpha (Dense vs BM25)",
    min_value=0.0,
    max_value=1.0,
    value=0.5,
    step=0.05,
    help="0.0 = BM25 keyword search only, 1.0 = Dense semantic search only",
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    **Architecture:**
    - Hybrid Search: Dense + BM25 (RRF)
    - Cross-Encoder Re-ranker
    - LSTM Sequence Drift & AE Anomaly
    - Recurrence Co-occurrence Graph
    - LLM Recommendation (Groq/Gemini/Fallback)
    - YOLOv8 PPE Verification
    """
)

# -----------------------------------------------------------------------------
# Main Header
# -----------------------------------------------------------------------------
st.markdown('<div class="main-title">🛡️ IAPIS Safety Intelligence</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Industrial Accident Prevention Intelligence System — Real-time hazard pattern detection & RAG recommendations</div>',
    unsafe_allow_html=True,
)

tab_search, tab_ppe = st.tabs(["🔍 Hazard Search & Intelligence", "📷 Computer Vision PPE Detection"])

# -----------------------------------------------------------------------------
# Tab 1: Hazard Search & Intelligence
# -----------------------------------------------------------------------------
with tab_search:
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        query = st.text_input(
            "Describe the hazard, equipment issue, or safety scenario:",
            value="overheating motor",
            placeholder="e.g., motor overheating, chemical fume leak, conveyor belt jam...",
            label_visibility="collapsed",
        )
    with col_btn:
        run_btn = st.button("Analyze Hazard", type="primary", use_container_width=True)

    # Preset query buttons
    st.caption("Quick scenarios:")
    sc_col1, sc_col2, sc_col3, sc_col4 = st.columns(4)
    with sc_col1:
        if st.button("🔥 Overheating Motor", use_container_width=True):
            query = "overheating motor"
            run_btn = True
    with sc_col2:
        if st.button("☣️ Chemical Fume Exposure", use_container_width=True):
            query = "chemical fume exposure ventilation"
            run_btn = True
    with sc_col3:
        if st.button("⚡ High Voltage Arc Flash", use_container_width=True):
            query = "electrical arc flash switchgear"
            run_btn = True
    with sc_col4:
        if st.button("⚠️ Conveyor Pinch Hazard", use_container_width=True):
            query = "conveyor belt nip point guard missing"
            run_btn = True

    if run_btn and query:
        with st.spinner("Executing hybrid retrieval, sequence drift checks, and recommendation generation..."):
            try:
                resp = requests.post(
                    f"{backend_url}/analyze",
                    json={"query": query, "top_k": top_k, "alpha": alpha},
                    timeout=30,
                )
                if resp.status_code != 200:
                    st.error(f"Analysis failed with HTTP {resp.status_code}: {resp.text}")
                else:
                    data = resp.json()
                    results = data.get("results", [])
                    risk_summary = data.get("risk_summary", {})
                    recommendation = data.get("recommendation", "")
                    provider = data.get("llm_provider", "Template Engine")

                    # Section 1: LLM Recommendation
                    st.subheader("📋 Preventive Action Recommendations")
                    badge_style = "badge-info" if "groq" in provider.lower() or "gemini" in provider.lower() else "badge-medium"
                    st.markdown(
                        f'<span class="badge {badge_style}">Source: {provider.upper()}</span>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(recommendation)

                    # Section 2: Deep Learning Risk Monitoring
                    st.markdown("---")
                    st.subheader("⚠️ Equipment Risk & Anomaly Assessment")
                    
                    eq_flags = risk_summary.get("equipment_flags", {})
                    rec_pattern = risk_summary.get("recurrence_pattern", "")

                    if rec_pattern:
                        st.info(f"🔁 **Recurrence Pattern:** {rec_pattern}")

                    if eq_flags:
                        eq_cols = st.columns(len(eq_flags) if len(eq_flags) <= 4 else 4)
                        for idx, (eq_name, flags) in enumerate(eq_flags.items()):
                            col_idx = idx % (len(eq_cols))
                            with eq_cols[col_idx]:
                                lstm_risk = flags.get("lstm_drift_risk", 0.0)
                                is_drift = flags.get("flag", False)
                                is_anomaly = flags.get("autoencoder_anomaly", False)

                                status_badge = "🔴 RISK FLAGGED" if (is_drift or is_anomaly) else "🟢 NORMAL"
                                st.metric(
                                    label=f"⚙️ {eq_name.title()}",
                                    value=status_badge,
                                    delta=f"LSTM Risk: {lstm_risk:.2f}" if is_drift else f"Risk: {lstm_risk:.2f}",
                                    delta_color="inverse" if is_drift else "normal",
                                )
                                st.caption(
                                    f"• LSTM Drift Flag: {'Yes' if is_drift else 'No'}\n\n"
                                    f"• AE Anomaly: {'Detected' if is_anomaly else 'Clean'}"
                                )
                    else:
                        st.write("No active equipment sensor alerts associated with matching entities.")

                    # Section 3: Retrieved Precedent Incidents
                    st.markdown("---")
                    st.subheader(f"📑 Historical Precedent Incident Reports ({len(results)} Found)")

                    if not results:
                        st.warning("No matching historical reports found.")
                    else:
                        for r in results:
                            sev = r.get("severity", "medium").lower()
                            sev_class = "badge-high" if "high" in sev else ("badge-low" if "low" in sev else "badge-medium")

                            with st.container():
                                st.markdown(
                                    f"""
                                    <div class="report-card">
                                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 0.5rem;">
                                            <h4 style="margin:0;">{r.get('title', 'Untitled Incident')} <span style="font-size:0.8rem; color:#aaa;">({r.get('id', 'N/A')})</span></h4>
                                            <div>
                                                <span class="badge {sev_class}">Severity: {r.get('severity', 'N/A').upper()}</span>
                                                <span class="badge badge-info">Recurrence: {r.get('recurrence_score', 0.0):.2f}</span>
                                            </div>
                                        </div>
                                        <p style="font-size:0.9rem; color:#ccc; margin-bottom:0.5rem;">{r.get('snippet', '')}</p>
                                        <div style="font-size:0.8rem; color:#888;">
                                            <strong>Equipment:</strong> {r.get('equipment', 'N/A')} &nbsp;|&nbsp; 
                                            <strong>Hazard:</strong> {r.get('hazard_type', 'N/A')} &nbsp;|&nbsp; 
                                            <strong>Location:</strong> {r.get('location', 'N/A')} &nbsp;|&nbsp; 
                                            <strong>Date:</strong> {r.get('date', 'N/A')} &nbsp;|&nbsp; 
                                            <strong>Rerank Score:</strong> {r.get('rerank_score', 0.0):.4f} (BM25: {r.get('bm25_score', 0.0):.2f}, Dense: {r.get('dense_score', 0.0):.2f})
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

            except requests.exceptions.ConnectionError:
                st.error(f"Could not connect to FastAPI server at `{backend_url}`. Please run `uvicorn api.main:app --port 8000`.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

# -----------------------------------------------------------------------------
# Tab 2: Computer Vision PPE Detection
# -----------------------------------------------------------------------------
with tab_ppe:
    st.subheader("📷 PPE Safety Compliance Visual Inspection")
    st.caption("Upload an image to inspect for safety equipment (Hardhats, Vests, Masks, Personnel).")

    uploaded_file = st.file_uploader("Upload inspection photo", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        image_bytes = uploaded_file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        col_img, col_det = st.columns([3, 2])

        with col_img:
            st.image(image, caption="Uploaded Workplace Image", use_container_width=True)

        with col_det:
            if st.button("Scan for PPE Compliance", type="primary", use_container_width=True):
                with st.spinner("Running YOLOv8 PPE detection model..."):
                    try:
                        files = {"file": (uploaded_file.name, image_bytes, uploaded_file.type)}
                        ppe_resp = requests.post(f"{backend_url}/detect-ppe", files=files, timeout=30)

                        if ppe_resp.status_code == 200:
                            ppe_data = ppe_resp.json()
                            detections = ppe_data.get("detections", [])
                            message = ppe_data.get("message", "")

                            st.success(message)

                            if detections:
                                # Overlay boxes on image
                                annotated = image.copy()
                                draw = ImageDraw.Draw(annotated)
                                width, height = annotated.size

                                for d in detections:
                                    bbox = d.get("bbox", [])
                                    cls_name = d.get("class_name", "object")
                                    conf = d.get("confidence", 0.0)

                                    if len(bbox) == 4:
                                        # Box coordinates can be normalized or pixel-based
                                        x1, y1, x2, y2 = bbox
                                        if max(bbox) <= 1.0:
                                            x1 *= width
                                            y1 *= height
                                            x2 *= width
                                            y2 *= height
                                        is_viol = cls_name.lower().startswith("no-") or cls_name.lower().startswith("no_")
                                        is_per = cls_name.lower() in ["person", "human"]
                                        color = "#ef4444" if is_viol else ("#06b6d4" if is_per else "#22c55e")

                                        draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
                                        draw.text((x1 + 4, max(0, y1 - 15)), f"{cls_name} {conf:.2f}", fill=color)

                                st.image(annotated, caption="Annotated Detections", use_container_width=True)

                                st.write("### Detection List")
                                for d in detections:
                                    is_viol = d['class_name'].lower().startswith("no-") or d['class_name'].lower().startswith("no_")
                                    badge = "🔴 VIOLATION: " if is_viol else ("👤 " if d['class_name'].lower() in ['person', 'human'] else "🟢 COMPLIANT: ")
                                    st.write(f"- {badge}**{d['class_name']}** ({d['confidence'] * 100:.1f}% confidence)")
                            else:
                                st.info("No PPE equipment or personnel detected.")
                        else:
                            st.error(f"PPE detection endpoint returned HTTP {ppe_resp.status_code}: {ppe_resp.text}")
                    except Exception as e:
                        st.error(f"Failed to communicate with PPE detection endpoint: {e}")
