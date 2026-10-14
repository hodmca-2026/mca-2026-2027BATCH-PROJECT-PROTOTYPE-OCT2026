import json
import logging
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from Backend.database import get_connection, init_db
from Backend.risk_engine import calculate_risk
from Backend.security.dns_checker import check_dns
from Backend.security.ssl_checker import check_ssl
from Backend.security.url_security import check_url_security
from Backend.utils.url_validator import validate_url
from Backend.ir.ir_service import analyze_url_with_ir
from app.ml.ml_service import analyze_url

logger = logging.getLogger("phishguard")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI(
    title="Phishing URL Risk Detector API",
    description="Backend API for detecting suspicious and phishing URLs.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()


class URLRequest(BaseModel):
    url: str


def _normalize_url(raw_url: str) -> str:
    value = (raw_url or "").strip()
    if not value:
        raise ValueError("URL cannot be empty.")
    if "://" not in value:
        value = "https://" + value
    return value


@app.get("/")
def home():
    return {"message": "Phishing URL Risk Detector API is running!"}


@app.post("/api/v1/scan")
def scan_url(request: URLRequest):
    raw_url = request.url
    try:
        url = _normalize_url(raw_url)
        is_valid = validate_url(url)
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid URL")

        parsed = urlparse(url)
        domain = parsed.hostname or ""
        if not domain:
            raise HTTPException(status_code=400, detail="Could not extract domain from URL")

        dns_result = check_dns(url)
        ssl_result = check_ssl(url)
        url_security_result = check_url_security(url)
        ml_result = analyze_url(url)

        risk_result = calculate_risk(
            ml_prediction=ml_result.get("classification", "legitimate"),
            ml_probability=ml_result.get("phishing_probability", 0.0),
            ml_confidence=ml_result.get("confidence", 0.0),
            dns_resolves=bool(dns_result.get("resolves", False)),
            ssl_valid=bool(ssl_result.get("valid", False)),
            url_security=url_security_result,
        )

        final_classification = "phishing" if risk_result["risk_score"] >= 30 else "legitimate"
        verifiable = bool(dns_result.get("resolves", False))
        if not verifiable and final_classification == "legitimate":
            final_classification = "unverifiable"

        reasons = list(risk_result.get("url_security_reasons", []))
        for signal in ml_result.get("signals", []):
            description = signal.get("description") if isinstance(signal, dict) else str(signal)
            if description:
                reasons.append(description)
        if not verifiable:
            reasons.append("Hostname did not resolve; URL cannot be verified as safe.")

        explanation_text = risk_result["explanation"]
        if isinstance(explanation_text, list):
            explanation_text = " ".join(str(part) for part in explanation_text if str(part).strip())
        if not explanation_text:
            explanation_text = (
                "The URL did not trigger major phishing indicators in the available security checks."
                if final_classification == "legitimate"
                else "The URL triggered suspicious security indicators during analysis."
            )
        if not verifiable:
            explanation_text += " The hostname did not resolve, so the URL cannot be verified as safe."

        result = {
            "url": url,
            "valid": True,
            "verifiable": verifiable,
            "classification": final_classification,
            "verdict": final_classification,
            "risk_classification": risk_result["classification"],
            "risk_score": risk_result["risk_score"],
            "confidence": risk_result["confidence"],
            "score_breakdown": risk_result["score_breakdown"],
            "ml": ml_result,
            "signals": ml_result.get("signals", []),
            "dns": dns_result,
            "ssl": ssl_result,
            "url_security": url_security_result,
            "risk_explanation": explanation_text,
            "explanation": explanation_text,
            "reasons": reasons,
            "url_security_reasons": risk_result.get("url_security_reasons", []),
            "message": "URL scanned successfully",
        }

        try:
            result["ir_analysis"] = analyze_url_with_ir(url)
        except Exception:
            logger.exception("IR analysis failed for %s", url)
            result["ir_analysis"] = {
                "status": "unavailable",
                "message": "IR analysis temporarily unavailable",
            }

        connection = None
        try:
            connection = get_connection()
            connection.execute(
                """
                INSERT INTO scan_history (
                    url,
                    classification,
                    risk_score,
                    confidence,
                    result_json
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    url,
                    final_classification,
                    risk_result["risk_score"],
                    risk_result["confidence"],
                    json.dumps(result),
                ),
            )
            connection.commit()
        except Exception as db_err:
            logger.warning("Database save failed for %s: %s", url, db_err)
        finally:
            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass

        return result

    except HTTPException:
        raise
    except ValueError as exc:
        logger.warning("Invalid URL rejected: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid URL") from exc
    except Exception as exc:
        logger.exception("Unhandled scan error for URL: %s", raw_url)
        raise HTTPException(status_code=500, detail="An error occurred while scanning the URL") from exc


@app.get("/api/v1/history")
def get_history():
    try:
        connection = get_connection()
        rows = connection.execute(
            """
            SELECT id,
                   url,
                   classification,
                   risk_score,
                   confidence,
                   scan_time
            FROM scan_history
            ORDER BY id DESC
            """
        ).fetchall()
    except Exception as exc:
        logger.exception("Failed to retrieve scan history")
        raise HTTPException(status_code=500, detail="Could not retrieve scan history") from exc
    else:
        history = []
        for row in rows:
            history.append(
                {
                    "id": row["id"],
                    "url": row["url"],
                    "classification": row["classification"],
                    "risk_score": row["risk_score"],
                    "confidence": row["confidence"],
                    "scan_time": row["scan_time"],
                }
            )
        return history
    finally:
        try:
            connection.close()
        except Exception:
            pass
