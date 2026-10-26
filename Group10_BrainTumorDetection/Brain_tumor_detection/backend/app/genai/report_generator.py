"""
GenAI Report Assistant.

Generates a structured DRAFT report using ONLY verified case data and the
model's own output (predicted class, confidence, class probabilities,
Grad-CAM disclaimer). It never invents findings, never recommends
treatment, and is always labeled as requiring professional review.

Two modes:
  - Template mode (default, no API key required): deterministically fills
    a structured template from the verified fields. This is what runs
    out-of-the-box.
  - LLM-assisted mode (if ANTHROPIC_API_KEY is set in .env): sends the
    SAME verified fields to Claude with a strict system prompt that
    forbids adding any new medical facts, and uses the response to
    phrase the case summary in more natural language. The structured
    facts themselves still come only from `data`, never the LLM.
"""
from datetime import datetime

from app.core.config import settings

AI_LABEL = "AI-generated draft — requires professional review."

TEMPLATE_SYSTEM_PROMPT = """You are a report-drafting assistant for a research/educational \
brain MRI decision-support tool. You will be given verified case data and a CNN model's \
output. Rewrite ONLY the "Case Summary" paragraph in clear, professional clinical-report \
language. Rules you MUST follow:
- Use ONLY the facts given to you. Never add a diagnosis, treatment recommendation, \
  causal explanation, or any medical fact not explicitly present in the input data.
- Do not state or imply certainty beyond the given confidence score.
- Keep it to 2-4 sentences.
- Do not include disclaimers yourself -- those are added separately by the system.
Return only the paragraph text, nothing else."""


def _template_summary(data: dict) -> str:
    return (
        f"MRI case {data['case_code']} (patient reference: {data['patient_ref_id']}) was "
        f"processed by the CNN classification model (version {data['model_version']}). "
        f"The model's top prediction is '{data['predicted_class']}' with a confidence "
        f"score of {data['confidence_score']*100:.1f}%. Class-wise probability distribution: "
        + ", ".join(f"{cls}: {prob*100:.1f}%" for cls, prob in data['all_class_probabilities'].items())
        + "."
    )


def _llm_summary(data: dict) -> str | None:
    """Attempts to call the Anthropic API for a more naturally-phrased
    summary. Returns None on any failure so the caller falls back to the
    template (the app must never break because GenAI phrasing failed)."""
    if not settings.ANTHROPIC_API_KEY:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        user_content = (
            f"Case code: {data['case_code']}\n"
            f"Patient reference: {data['patient_ref_id']}\n"
            f"Model version: {data['model_version']}\n"
            f"Predicted class: {data['predicted_class']}\n"
            f"Confidence: {data['confidence_score']*100:.1f}%\n"
            f"All class probabilities: {data['all_class_probabilities']}\n"
        )
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system=TEMPLATE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        return "".join(b.text for b in response.content if hasattr(b, "text")).strip()
    except Exception as e:
        print(f"[genai] LLM summary failed, falling back to template: {e}")
        return None


def generate_draft_report(data: dict) -> str:
    """
    `data` must contain (all verified, pulled from DB -- never user free text):
      case_code, patient_ref_id, model_version, predicted_class,
      confidence_score, all_class_probabilities, disclaimer
    """
    summary = _llm_summary(data) or _template_summary(data)

    report = f"""{AI_LABEL}
{'=' * len(AI_LABEL)}

CASE SUMMARY
------------
{summary}

AI MODEL RESULT
----------------
Predicted class: {data['predicted_class']}
Confidence score: {data['confidence_score']*100:.1f}%
Model version: {data['model_version']}
{'*** MODEL IS UNTRAINED / DEMO PLACEHOLDER — result is NOT meaningful ***' if data.get('is_placeholder') else ''}

EXPLAINABILITY (GRAD-CAM)
--------------------------
{data['disclaimer']}

LIMITATIONS
------------
- This system is a research/educational decision-support tool, not an autonomous diagnostic device.
- The CNN was trained on a public benchmark dataset and has not been clinically validated.
- Grad-CAM highlights regions that influenced the prediction; it does not delineate a tumor boundary.
- This output must not be used as the sole basis for any clinical decision.

REVIEW SECTION
---------------
Status: PENDING REVIEW
Reviewer notes: [to be completed by reviewing doctor/researcher]

Generated at: {datetime.utcnow().isoformat()}Z
"""
    return report
