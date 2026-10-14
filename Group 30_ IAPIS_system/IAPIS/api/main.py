"""
FastAPI Application — IAPIS Backend

Endpoints:
- GET  /health       → Health check
- POST /search       → Hybrid search + rerank
- POST /analyze      → Full pipeline (search + risk flags + recommendation)
- POST /detect-ppe   → PPE detection from uploaded image (optional)

Also serves the static HTML/CSS/JS frontend.
"""

import json
import os
import logging
import tempfile
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from api.models import (
    QueryRequest,
    SearchResponse,
    AnalyzeResponse,
    PPEResponse,
    PPEDetection,
    HealthResponse,
    ReportResult,
    EquipmentFlag,
    RiskSummary,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App Setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="IAPIS — Industrial Accident Prevention Intelligence System",
    description="RAG-based safety intelligence system with hybrid retrieval, risk detection, and LLM recommendations.",
    version="1.0.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Module-level state (lazy-loaded)
# ---------------------------------------------------------------------------
_reports = None
_recurrence_scores = None
_initialized = False


def _ensure_initialized():
    """Lazy-load all modules and data on first request."""
    global _reports, _recurrence_scores, _initialized
    if _initialized:
        return
    
    base_dir = os.path.join(os.path.dirname(__file__), "..")
    reports_path = os.path.join(base_dir, "data", "reports", "reports.json")
    
    if os.path.exists(reports_path):
        with open(reports_path, "r", encoding="utf-8") as f:
            _reports = json.load(f)
        logger.info(f"Loaded {len(_reports)} reports")
    else:
        _reports = []
        logger.warning(f"Reports not found at {reports_path}")
    
    # Pre-compute recurrence scores
    try:
        from risk_models.recurrence_rank import compute_recurrence_scores
        _recurrence_scores = compute_recurrence_scores(_reports)
    except Exception as e:
        logger.warning(f"Could not compute recurrence scores: {e}")
        _recurrence_scores = {}
    
    _initialized = True


def _build_report_result(result: dict, recurrence_scores: dict = None) -> ReportResult:
    """Convert a retrieval result dict into a ReportResult."""
    metadata = result.get("metadata", {})
    text = result.get("document", result.get("text", ""))
    snippet = text[:200] + "..." if len(text) > 200 else text
    
    return ReportResult(
        id=result.get("id", ""),
        title=metadata.get("title", result.get("title", "")),
        snippet=snippet,
        dense_score=result.get("dense_score", 0.0),
        bm25_score=result.get("bm25_score", 0.0),
        rerank_score=result.get("rerank_score", 0.0),
        recurrence_score=(recurrence_scores or {}).get(result.get("id", ""), 0.0),
        equipment=metadata.get("equipment", result.get("equipment", "")),
        hazard_type=metadata.get("hazard_type", result.get("hazard_type", "")),
        severity=metadata.get("severity", result.get("severity", "")),
        location=metadata.get("location", result.get("location", "")),
        date=metadata.get("date", result.get("date", "")),
        source=metadata.get("source", result.get("source", "")),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="ok")


@app.post("/search", response_model=SearchResponse)
async def search(request: QueryRequest):
    """
    Hybrid search + rerank.
    
    Runs BM25 + dense retrieval, fuses with Reciprocal Rank Fusion,
    then reranks top results with a cross-encoder.
    """
    _ensure_initialized()
    
    try:
        from retrieval.hybrid_search import hybrid_search
        from retrieval.reranker import rerank
        
        # Hybrid search
        candidates = hybrid_search(
            query=request.query,
            k=request.top_k * 2,  # Fetch more candidates for reranking
            alpha=request.alpha,
        )
        
        # Rerank
        reranked = rerank(
            query=request.query,
            candidates=candidates,
            top_n=request.top_k,
        )
        
        # Build response
        results = [_build_report_result(r, _recurrence_scores) for r in reranked]
        
        return SearchResponse(results=results)
    
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: QueryRequest):
    """
    Full analysis pipeline.
    
    Runs /search + LSTM/autoencoder risk flags for equipment mentioned
    in top results + generates a grounded recommendation.
    """
    _ensure_initialized()
    
    try:
        from retrieval.hybrid_search import hybrid_search
        from retrieval.reranker import rerank
        from risk_models.recurrence_rank import get_recurrence_pattern_summary
        from recommend.llm_client import generate_recommendation
        
        # Step 1: Hybrid search + rerank
        candidates = hybrid_search(
            query=request.query,
            k=request.top_k * 2,
            alpha=request.alpha,
        )
        reranked = rerank(
            query=request.query,
            candidates=candidates,
            top_n=request.top_k,
        )
        
        results = [_build_report_result(r, _recurrence_scores) for r in reranked]
        
        # Step 2: Get equipment IDs mentioned in results
        equipment_mentioned = set()
        for r in results:
            if r.equipment:
                equipment_mentioned.add(r.equipment)
        
        # Step 3: Risk flags
        equipment_flags = {}
        
        # LSTM drift predictions
        try:
            from risk_models.lstm_drift import predict_all_equipment
            lstm_results = predict_all_equipment()
            for eq_id, pred in lstm_results.items():
                equipment_flags[eq_id] = EquipmentFlag(
                    lstm_drift_risk=pred["risk_score"],
                    flag=pred["flag"],
                )
        except Exception as e:
            logger.warning(f"LSTM prediction failed: {e}")
        
        # Autoencoder anomaly flags
        try:
            from risk_models.autoencoder_anomaly import score_all_logs
            import pandas as pd
            
            ae_results = score_all_logs()
            # Group by equipment_id if available in maintenance logs
            maint_path = os.path.join(os.path.dirname(__file__), "..", "data", "maintenance_logs.csv")
            if os.path.exists(maint_path):
                maint_df = pd.read_csv(maint_path)
                for idx, ae_result in enumerate(ae_results):
                    if idx < len(maint_df):
                        eq_id = maint_df.iloc[idx].get("equipment_id", "")
                        if eq_id and ae_result["is_anomalous"]:
                            if eq_id in equipment_flags:
                                equipment_flags[eq_id].autoencoder_anomaly = True
                            else:
                                equipment_flags[eq_id] = EquipmentFlag(autoencoder_anomaly=True)
        except Exception as e:
            logger.warning(f"Autoencoder scoring failed: {e}")
        
        # Step 4: Recurrence pattern
        recurrence_pattern = ""
        try:
            # Build a list of report dicts for the reranked results
            result_reports = []
            for r in results:
                result_reports.append({
                    "id": r.id,
                    "equipment": r.equipment,
                    "hazard_type": r.hazard_type,
                })
            recurrence_pattern = get_recurrence_pattern_summary(result_reports)
        except Exception as e:
            logger.warning(f"Recurrence pattern failed: {e}")
        
        risk_summary = RiskSummary(
            equipment_flags=equipment_flags,
            recurrence_pattern=recurrence_pattern,
        )
        
        # Step 5: Generate recommendation
        risk_flags_dict = {
            "equipment_flags": {
                k: {"lstm_drift_risk": v.lstm_drift_risk, "flag": v.flag, "autoencoder_anomaly": v.autoencoder_anomaly}
                for k, v in equipment_flags.items()
            },
            "recurrence_pattern": recurrence_pattern,
        }
        
        rec_result = generate_recommendation(
            query=request.query,
            evidence=reranked,
            risk_flags=risk_flags_dict,
        )
        
        return AnalyzeResponse(
            results=results,
            risk_summary=risk_summary,
            recommendation=rec_result["recommendation"],
            llm_provider=rec_result["provider"],
        )
    
    except Exception as e:
        logger.error(f"Analyze failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/detect-ppe", response_model=PPEResponse)
async def detect_ppe(image: UploadFile = File(...)):
    """
    PPE detection from uploaded image using YOLOv8.
    Only active if ultralytics is importable.
    """
    try:
        from cv_branch.ppe_detect import detect_ppe as run_detection
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="PPE detection is not available (ultralytics not installed).",
        )
    
    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        content = await image.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        detections = run_detection(tmp_path)
        
        ppe_detections = [
            PPEDetection(
                class_name=d["class_name"],
                confidence=d["confidence"],
                bbox=d.get("bbox", []),
            )
            for d in detections
        ]
        
        return PPEResponse(
            detections=ppe_detections,
            message=f"Detected {len(ppe_detections)} objects in the image.",
        )
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# Static file serving for frontend
# ---------------------------------------------------------------------------
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    async def serve_frontend():
        """Serve the main HTML page."""
        index_path = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        raise HTTPException(status_code=404, detail="Frontend not found")
