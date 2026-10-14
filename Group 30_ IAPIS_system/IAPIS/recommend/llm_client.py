"""
LLM Client for Safety Recommendation Generation

Calls Groq first; on failure/missing key, calls Gemini; on failure/missing key,
falls back to a deterministic template. The pipeline never crashes for missing keys.

Never sends full report text beyond what's needed — caps total evidence to ~1500 tokens.
"""

import os
import logging
from typing import Dict, List, Optional

from dotenv import load_dotenv

from recommend.prompt_templates import build_llm_prompt, build_fallback_recommendation

# Explicitly load .env from project root (parent of recommend/)
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(_env_path, override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _call_groq(prompt: str) -> Optional[str]:
    """Call Groq API using OpenAI-compatible SDK (avoids groq package proxy issues)."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_key_here":
        logger.info("Groq API key not configured, skipping.")
        return None
    
    try:
        import httpx
        
        # Use raw HTTP request to Groq's OpenAI-compatible endpoint
        # This avoids all SDK version/proxy issues
        response = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a senior industrial safety analyst. Provide clear, evidence-based safety recommendations.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 1024,
            },
            timeout=30.0,
        )
        
        response.raise_for_status()
        data = response.json()
        result = data["choices"][0]["message"]["content"]
        logger.info("Groq API call successful")
        return result
    
    except Exception as e:
        logger.warning(f"Groq API call failed: {e}")
        return None


def _call_gemini(prompt: str) -> Optional[str]:
    """Call Google Gemini API for recommendation generation."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_key_here":
        logger.info("Gemini API key not configured, skipping.")
        return None
    
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=1024,
            ),
        )
        
        result = response.text
        logger.info("Gemini API call successful")
        return result
    
    except Exception as e:
        logger.warning(f"Gemini API call failed: {e}")
        return None


def generate_recommendation(
    query: str,
    evidence: List[dict],
    risk_flags: dict,
) -> Dict:
    """
    Generate a safety recommendation using the best available LLM.
    
    Cascade: Groq -> Gemini -> Deterministic fallback template.
    
    Args:
        query: The user's safety query.
        evidence: List of retrieved/reranked report dicts.
        risk_flags: Dict with equipment risk flags and recurrence patterns.
    
    Returns:
        {
            "recommendation": str,
            "provider": "groq" | "gemini" | "fallback",
            "success": bool,
        }
    """
    # Determine preferred provider
    preferred = os.getenv("LLM_PROVIDER", "groq").lower()
    
    # Build the prompt
    prompt = build_llm_prompt(query, evidence, risk_flags)
    
    # Try preferred provider first
    result = None
    provider = None
    
    if preferred == "groq":
        result = _call_groq(prompt)
        if result:
            provider = "groq"
        else:
            result = _call_gemini(prompt)
            if result:
                provider = "gemini"
    elif preferred == "gemini":
        result = _call_gemini(prompt)
        if result:
            provider = "gemini"
        else:
            result = _call_groq(prompt)
            if result:
                provider = "groq"
    else:
        # Try both in order
        result = _call_groq(prompt)
        if result:
            provider = "groq"
        else:
            result = _call_gemini(prompt)
            if result:
                provider = "gemini"
    
    # Fallback to template
    if result is None:
        logger.info("No LLM API available. Using deterministic fallback template.")
        result = build_fallback_recommendation(query, evidence, risk_flags)
        provider = "fallback"
    
    return {
        "recommendation": result,
        "provider": provider,
        "success": True,
    }


if __name__ == "__main__":
    # Test with dummy data
    test_evidence = [
        {
            "id": "RPT-0001",
            "title": "Motor M-12 overheating",
            "text": "Motor overheated causing smoke...",
            "equipment": "induction motor",
            "hazard_type": "overheating",
            "severity": "high",
            "location": "Building 3, Line 2",
        }
    ]
    
    test_risk_flags = {
        "equipment_flags": {
            "M-12": {"lstm_drift_risk": 0.78, "flag": True, "autoencoder_anomaly": True}
        },
        "recurrence_pattern": "3 of 5 reports involve induction motors with overheating",
    }
    
    result = generate_recommendation("overheating motor incidents", test_evidence, test_risk_flags)
    print(f"\nProvider: {result['provider']}")
    print(f"Recommendation:\n{result['recommendation']}")
