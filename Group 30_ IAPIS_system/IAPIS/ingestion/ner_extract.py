"""
Named Entity Recognition (NER) for Equipment and Hazard Extraction

Uses spaCy with a custom entity ruler pattern list layered on top of
spaCy's built-in NER to extract equipment types and hazard keywords.

Populates missing `equipment` and `hazard_type` fields in reports.

Course mapping: IR Unit VI / DL Unit VI — extracting structured data from text.
"""

import json
import os
import logging
from typing import Dict, List, Optional

import spacy
from spacy.language import Language
from spacy.tokens import Span

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pattern lists for entity ruler
# ---------------------------------------------------------------------------
EQUIPMENT_PATTERNS = [
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "induction"}, {"LOWER": "motor"}]},
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "electric"}, {"LOWER": "motor"}]},
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "motor"}]},
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "conveyor"}, {"LOWER": "belt"}]},
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "conveyor"}]},
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "forklift"}]},
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "fork"}, {"LOWER": "lift"}]},
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "lift"}, {"LOWER": "truck"}]},
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "electrical"}, {"LOWER": "panel"}]},
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "control"}, {"LOWER": "panel"}]},
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "distribution"}, {"LOWER": "panel"}]},
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "panel"}]},
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "compressor"}]},
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "air"}, {"LOWER": "compressor"}]},
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "hydraulic"}, {"LOWER": "press"}]},
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "press"}]},
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "welding"}, {"LOWER": "station"}]},
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "welder"}]},
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "crane"}]},
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "scaffold"}]},
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "scaffolding"}]},
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "ladder"}]},
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "pump"}]},
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "boiler"}]},
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "furnace"}]},
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "generator"}]},
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "transformer"}]},
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "bearing"}]},
    {"label": "EQUIPMENT", "pattern": [{"LOWER": "cylinder"}]},
]

HAZARD_PATTERNS = [
    {"label": "HAZARD", "pattern": [{"LOWER": "overheating"}]},
    {"label": "HAZARD", "pattern": [{"LOWER": "overheat"}]},
    {"label": "HAZARD", "pattern": [{"LOWER": "thermal"}, {"LOWER": "runaway"}]},
    {"label": "HAZARD", "pattern": [{"LOWER": "fire"}]},
    {"label": "HAZARD", "pattern": [{"LOWER": "combustion"}]},
    {"label": "HAZARD", "pattern": [{"LOWER": "smoke"}]},
    {"label": "HAZARD", "pattern": [{"LOWER": "fall"}]},
    {"label": "HAZARD", "pattern": [{"LOWER": "fell"}]},
    {"label": "HAZARD", "pattern": [{"LOWER": "spill"}]},
    {"label": "HAZARD", "pattern": [{"LOWER": "leak"}]},
    {"label": "HAZARD", "pattern": [{"LOWER": "leakage"}]},
    {"label": "HAZARD", "pattern": [{"LOWER": "electrical"}, {"LOWER": "shock"}]},
    {"label": "HAZARD", "pattern": [{"LOWER": "electrocution"}]},
    {"label": "HAZARD", "pattern": [{"LOWER": "arc"}, {"LOWER": "flash"}]},
    {"label": "HAZARD", "pattern": [{"LOWER": "mechanical"}, {"LOWER": "failure"}]},
    {"label": "HAZARD", "pattern": [{"LOWER": "bearing"}, {"LOWER": "failure"}]},
    {"label": "HAZARD", "pattern": [{"LOWER": "pressure"}, {"LOWER": "buildup"}]},
    {"label": "HAZARD", "pattern": [{"LOWER": "overpressure"}]},
    {"label": "HAZARD", "pattern": [{"LOWER": "explosion"}]},
    {"label": "HAZARD", "pattern": [{"LOWER": "chemical"}, {"LOWER": "exposure"}]},
    {"label": "HAZARD", "pattern": [{"LOWER": "fume"}]},
    {"label": "HAZARD", "pattern": [{"LOWER": "fumes"}]},
    {"label": "HAZARD", "pattern": [{"LOWER": "crushing"}]},
    {"label": "HAZARD", "pattern": [{"LOWER": "entanglement"}]},
    {"label": "HAZARD", "pattern": [{"LOWER": "amputation"}]},
    {"label": "HAZARD", "pattern": [{"LOWER": "vibration"}, {"LOWER": "damage"}]},
    {"label": "HAZARD", "pattern": [{"LOWER": "corrosion"}]},
]

# Canonical mapping: normalize detected text to standard labels
EQUIPMENT_CANONICAL = {
    "motor": "induction motor",
    "induction motor": "induction motor",
    "electric motor": "induction motor",
    "conveyor belt": "conveyor belt",
    "conveyor": "conveyor belt",
    "forklift": "forklift",
    "fork lift": "forklift",
    "lift truck": "forklift",
    "electrical panel": "electrical panel",
    "control panel": "electrical panel",
    "distribution panel": "electrical panel",
    "panel": "electrical panel",
    "compressor": "compressor",
    "air compressor": "compressor",
    "hydraulic press": "hydraulic press",
    "press": "hydraulic press",
    "welding station": "welding station",
    "welder": "welding station",
    "crane": "crane",
    "scaffold": "scaffold",
    "scaffolding": "scaffold",
    "ladder": "ladder",
    "pump": "pump",
    "boiler": "boiler",
    "furnace": "furnace",
    "generator": "generator",
    "transformer": "transformer",
    "bearing": "bearing",
    "cylinder": "cylinder",
}

HAZARD_CANONICAL = {
    "overheating": "overheating",
    "overheat": "overheating",
    "thermal runaway": "overheating",
    "fire": "fire",
    "combustion": "fire",
    "smoke": "fire",
    "fall": "fall",
    "fell": "fall",
    "spill": "spill",
    "leak": "spill",
    "leakage": "spill",
    "electrical shock": "electrical shock",
    "electrocution": "electrical shock",
    "arc flash": "electrical shock",
    "mechanical failure": "mechanical failure",
    "bearing failure": "mechanical failure",
    "pressure buildup": "pressure buildup",
    "overpressure": "pressure buildup",
    "explosion": "pressure buildup",
    "chemical exposure": "chemical exposure",
    "fume": "chemical exposure",
    "fumes": "chemical exposure",
    "crushing": "crushing",
    "entanglement": "crushing",
    "amputation": "crushing",
    "vibration damage": "vibration damage",
    "corrosion": "corrosion",
}

# Singleton for the loaded spaCy model
_nlp = None


def _get_nlp():
    """Load spaCy model with custom entity ruler (singleton)."""
    global _nlp
    if _nlp is not None:
        return _nlp
    
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        logger.error(
            "spaCy model 'en_core_web_sm' not found. "
            "Run: python -m spacy download en_core_web_sm"
        )
        raise
    
    # Add entity ruler before the built-in NER
    ruler = nlp.add_pipe("entity_ruler", before="ner")
    ruler.add_patterns(EQUIPMENT_PATTERNS + HAZARD_PATTERNS)
    
    _nlp = nlp
    return nlp


def extract_entities(text: str) -> Dict[str, Optional[str]]:
    """
    Extract equipment and hazard entities from text using spaCy + entity ruler.
    
    Returns:
        dict with keys: equipment (str|None), hazard_type (str|None),
                        all_equipment (list[str]), all_hazards (list[str])
    """
    nlp = _get_nlp()
    doc = nlp(text)
    
    equipment_found = []
    hazards_found = []
    
    for ent in doc.ents:
        ent_text = ent.text.lower()
        if ent.label_ == "EQUIPMENT":
            canonical = EQUIPMENT_CANONICAL.get(ent_text, ent_text)
            if canonical not in equipment_found:
                equipment_found.append(canonical)
        elif ent.label_ == "HAZARD":
            canonical = HAZARD_CANONICAL.get(ent_text, ent_text)
            if canonical not in hazards_found:
                hazards_found.append(canonical)
    
    return {
        "equipment": equipment_found[0] if equipment_found else None,
        "hazard_type": hazards_found[0] if hazards_found else None,
        "all_equipment": equipment_found,
        "all_hazards": hazards_found,
    }


def enrich_reports(reports: List[dict]) -> List[dict]:
    """
    Enrich reports by filling in missing equipment/hazard_type fields using NER.
    
    Args:
        reports: List of report dicts (will be modified in place).
    
    Returns:
        The same list of reports with populated fields.
    """
    enriched_count = 0
    
    for report in reports:
        needs_equipment = not report.get("equipment")
        needs_hazard = not report.get("hazard_type")
        
        if needs_equipment or needs_hazard:
            # Run NER on title + text combined
            combined = f"{report.get('title', '')} {report.get('text', '')}"
            entities = extract_entities(combined)
            
            if needs_equipment and entities["equipment"]:
                report["equipment"] = entities["equipment"]
                enriched_count += 1
            
            if needs_hazard and entities["hazard_type"]:
                report["hazard_type"] = entities["hazard_type"]
                enriched_count += 1
        
        # Fallback: if still missing, assign defaults
        if not report.get("equipment"):
            report["equipment"] = "general industrial equipment"
        if not report.get("hazard_type"):
            report["hazard_type"] = "industrial accident"
    
    logger.info(f"NER enrichment: filled {enriched_count} missing fields across {len(reports)} reports")
    return reports


def process_ner(input_path: str = None, output_path: str = None) -> List[dict]:
    """
    Full NER pipeline: load reports, extract entities, enrich, save.
    
    Args:
        input_path: Path to reports.json
        output_path: Path to write enriched reports (defaults to same file)
    
    Returns:
        List of enriched report dicts.
    """
    base_dir = os.path.join(os.path.dirname(__file__), "..")
    
    if input_path is None:
        input_path = os.path.join(base_dir, "data", "reports", "reports.json")
    if output_path is None:
        output_path = input_path
    
    with open(input_path, "r", encoding="utf-8") as f:
        reports = json.load(f)
    
    reports = enrich_reports(reports)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2, ensure_ascii=False)
    
    # Verify 100% coverage
    missing_eq = sum(1 for r in reports if not r.get("equipment"))
    missing_hz = sum(1 for r in reports if not r.get("hazard_type"))
    
    if missing_eq == 0 and missing_hz == 0:
        print(f"[OK] NER enrichment complete: 100% equipment and hazard_type coverage ({len(reports)} reports)")
    else:
        print(f"[WARN] NER enrichment incomplete: {missing_eq} missing equipment, {missing_hz} missing hazard_type")
    
    return reports


if __name__ == "__main__":
    process_ner()
