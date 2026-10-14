"""
Prompt Templates for Safety Recommendation Generation

Contains the grounded prompt template that instructs the LLM to:
1. Summarize the risk pattern
2. Cite report IDs used
3. Give 2-4 concrete safety actions
4. Refuse to invent facts not in the provided reports
"""


SAFETY_RECOMMENDATION_PROMPT = """You are a senior industrial safety analyst. Based ONLY on the retrieved incident reports and risk data below, provide a safety recommendation.

## User Query
{query}

## Retrieved Incident Reports (Evidence)
{evidence_text}

## Risk Flags
{risk_flags_text}

## Instructions
1. **Pattern Summary**: Summarize the recurring risk pattern you see across the reports. What equipment, hazard types, and root causes appear repeatedly?
2. **Cited Reports**: Explicitly cite the report IDs (e.g., RPT-0001, OSHA-0003) you are referencing.
3. **Safety Actions**: Provide 2-4 concrete, actionable safety recommendations based on the evidence.
4. **CRITICAL**: Do NOT invent or assume any facts not present in the provided reports. If the evidence is insufficient, say so.

Respond in a clear, professional format suitable for a safety officer briefing.
"""


FALLBACK_TEMPLATE = """## Safety Recommendation

**Query:** {query}

**Pattern Summary:**
Based on {num_reports} similar past reports involving **{top_equipment}**, the most common hazard types were: {top_hazards}. These incidents occurred across locations including {locations}.

**Cited Reports:** {cited_ids}

**Risk Flags:**
{risk_flags_summary}

**Recommended Actions:**
1. Conduct an immediate inspection of all {top_equipment} units, focusing on signs of {primary_hazard}.
2. Review and update the maintenance schedule for {top_equipment} to prevent recurrence of {primary_hazard} events.
3. Ensure all operators and maintenance personnel are trained on the warning signs of {primary_hazard} and the correct emergency response procedures.
4. Install or verify the function of monitoring systems (temperature sensors, vibration monitors) on all {top_equipment} units flagged by the risk assessment.

**Note:** This recommendation was generated using a template-based fallback (no LLM API available). For more detailed, context-aware recommendations, configure a Groq or Gemini API key.
"""


def format_evidence(reports: list, max_chars: int = 3000) -> str:
    """Format retrieved reports into evidence text for the prompt."""
    parts = []
    total_chars = 0
    
    for i, report in enumerate(reports):
        # Get report details
        report_id = report.get("id", f"Report-{i+1}")
        title = report.get("title", report.get("metadata", {}).get("title", "Untitled"))
        text = report.get("text", report.get("document", ""))
        equipment = report.get("equipment", report.get("metadata", {}).get("equipment", "unknown"))
        hazard = report.get("hazard_type", report.get("metadata", {}).get("hazard_type", "unknown"))
        severity = report.get("severity", report.get("metadata", {}).get("severity", "unknown"))
        
        # Truncate individual report text if needed
        if len(text) > 500:
            text = text[:500] + "..."
        
        entry = (
            f"### {report_id}: {title}\n"
            f"- Equipment: {equipment}\n"
            f"- Hazard: {hazard}\n"
            f"- Severity: {severity}\n"
            f"- Details: {text}\n"
        )
        
        if total_chars + len(entry) > max_chars:
            break
        
        parts.append(entry)
        total_chars += len(entry)
    
    return "\n".join(parts) if parts else "No reports available."


def format_risk_flags(risk_flags: dict) -> str:
    """Format risk flags into readable text."""
    if not risk_flags:
        return "No risk flags available."
    
    parts = []
    
    equipment_flags = risk_flags.get("equipment_flags", {})
    for eq_id, flags in equipment_flags.items():
        lstm_risk = flags.get("lstm_drift_risk", 0)
        lstm_flag = flags.get("flag", False)
        ae_anomaly = flags.get("autoencoder_anomaly", False)
        
        status = []
        if lstm_flag:
            status.append(f"LSTM drift risk: {lstm_risk:.2f}")
        if ae_anomaly:
            status.append("Autoencoder anomaly detected")
        
        if status:
            parts.append(f"- **{eq_id}**: {', '.join(status)}")
    
    recurrence = risk_flags.get("recurrence_pattern", "")
    if recurrence:
        parts.append(f"- **Recurrence pattern**: {recurrence}")
    
    return "\n".join(parts) if parts else "No risk flags detected."


def build_llm_prompt(query: str, evidence: list, risk_flags: dict) -> str:
    """Build the full prompt for the LLM API call."""
    evidence_text = format_evidence(evidence)
    risk_flags_text = format_risk_flags(risk_flags)
    
    return SAFETY_RECOMMENDATION_PROMPT.format(
        query=query,
        evidence_text=evidence_text,
        risk_flags_text=risk_flags_text,
    )


def build_fallback_recommendation(query: str, evidence: list, risk_flags: dict) -> str:
    """Build a template-based recommendation without an LLM."""
    from collections import Counter
    
    # Extract statistics from evidence
    equipment_counts = Counter()
    hazard_counts = Counter()
    locations = set()
    cited_ids = []
    
    for report in evidence:
        metadata = report.get("metadata", {})
        eq = report.get("equipment", metadata.get("equipment", ""))
        hz = report.get("hazard_type", metadata.get("hazard_type", ""))
        loc = report.get("location", metadata.get("location", ""))
        rid = report.get("id", "")
        
        if eq:
            equipment_counts[eq] += 1
        if hz:
            hazard_counts[hz] += 1
        if loc:
            locations.add(loc)
        if rid:
            cited_ids.append(rid)
    
    top_equipment = equipment_counts.most_common(1)[0][0] if equipment_counts else "industrial equipment"
    top_hazards = ", ".join(h for h, _ in hazard_counts.most_common(3)) or "general hazards"
    primary_hazard = hazard_counts.most_common(1)[0][0] if hazard_counts else "equipment failure"
    locations_str = ", ".join(list(locations)[:3]) or "various locations"
    cited_str = ", ".join(cited_ids) or "None"
    risk_flags_summary = format_risk_flags(risk_flags)
    
    return FALLBACK_TEMPLATE.format(
        query=query,
        num_reports=len(evidence),
        top_equipment=top_equipment,
        top_hazards=top_hazards,
        primary_hazard=primary_hazard,
        locations=locations_str,
        cited_ids=cited_str,
        risk_flags_summary=risk_flags_summary,
    )
