"""Tests for the ingestion pipeline."""

import json
import os
import tempfile
import pytest


def test_clean_text():
    """Test text cleaning function."""
    from ingestion.preprocess import clean_text
    
    # Basic cleaning
    result = clean_text("  Hello   WORLD  \n\n  test  ")
    assert result == "hello world test"
    
    # Boilerplate removal
    result = clean_text("Page 3 of 10 This is the report text")
    assert "page" not in result or "of" not in result
    
    # Empty input
    assert clean_text("") == ""
    assert clean_text(None) == ""


def test_chunk_text():
    """Test text chunking function."""
    from ingestion.preprocess import chunk_text
    
    # Short text returns single chunk
    short = "This is a short sentence."
    chunks = chunk_text(short, max_tokens=200)
    assert len(chunks) == 1
    assert chunks[0] == short
    
    # Long text gets split
    long_text = " ".join(["word"] * 400)
    chunks = chunk_text(long_text, max_tokens=200)
    assert len(chunks) >= 2
    
    # Empty text
    assert chunk_text("") == []


def test_report_schema():
    """Test pydantic Report model validation."""
    from ingestion.schema import Report
    
    # Valid report
    report = Report(
        id="RPT-0001",
        type="accident",
        title="Test Report",
        text="This is a test incident report.",
    )
    assert report.id == "RPT-0001"
    assert report.source == "synthetic"  # default
    
    # Invalid type should raise
    with pytest.raises(Exception):
        Report(id="RPT-0002", type="invalid_type", title="Bad", text="...")


def test_ner_extraction():
    """Test NER entity extraction."""
    from ingestion.ner_extract import extract_entities
    
    text = "The induction motor overheated and caused a fire at the conveyor belt area."
    entities = extract_entities(text)
    
    assert entities["equipment"] is not None
    assert entities["hazard_type"] is not None
    assert len(entities["all_equipment"]) > 0
    assert len(entities["all_hazards"]) > 0


def test_ner_enrichment():
    """Test that NER enrichment fills missing fields."""
    from ingestion.ner_extract import enrich_reports
    
    reports = [
        {
            "id": "RPT-TEST",
            "type": "accident",
            "title": "Motor Overheating Event",
            "text": "The induction motor in Building 3 overheated causing smoke and triggering fire alarms.",
            "equipment": None,
            "hazard_type": None,
        }
    ]
    
    enriched = enrich_reports(reports)
    
    # Should have filled in equipment and hazard_type
    assert enriched[0]["equipment"] is not None
    assert enriched[0]["hazard_type"] is not None
    assert enriched[0]["equipment"] != ""
    assert enriched[0]["hazard_type"] != ""
