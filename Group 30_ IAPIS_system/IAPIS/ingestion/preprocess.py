"""
NLP Preprocessing for Incident Reports

Provides:
- clean_text(): lowercase, strip boilerplate, collapse whitespace
- chunk_text(): split long texts into embedding-friendly chunks
- process_reports(): full pipeline over the reports corpus
"""

import json
import os
import re
from typing import List


def clean_text(text: str) -> str:
    """
    Clean raw report text for downstream processing.
    
    - Lowercases
    - Strips common boilerplate headers/footers
    - Collapses multiple whitespace/newlines into single space
    - Strips leading/trailing whitespace
    """
    if not text:
        return ""
    
    # Lowercase
    text = text.lower()
    
    # Remove common boilerplate patterns
    boilerplate_patterns = [
        r"---+",  # horizontal rules
        r"page \d+ of \d+",  # page numbers
        r"confidential.*?report",  # confidentiality headers
        r"classification:?\s*(restricted|confidential|internal)",
        r"prepared by:?\s*\w+",
        r"approved by:?\s*\w+",
        r"revision:?\s*\d+",
        r"document\s*(?:no|number|id):?\s*[\w-]+",
    ]
    for pattern in boilerplate_patterns:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)
    
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    
    # Strip
    text = text.strip()
    
    return text


def chunk_text(text: str, max_tokens: int = 200) -> List[str]:
    """
    Split text into chunks suitable for the embedding model's context window.
    
    Uses a simple sentence-boundary + word-count approach.
    Each chunk is <= max_tokens words.
    
    Args:
        text: The input text to chunk.
        max_tokens: Maximum number of words per chunk (approximate token proxy).
    
    Returns:
        List of text chunks. If the text is already short enough, returns [text].
    """
    if not text:
        return []
    
    words = text.split()
    
    # If short enough, return as single chunk
    if len(words) <= max_tokens:
        return [text]
    
    # Split on sentence boundaries first
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = []
    current_word_count = 0
    
    for sentence in sentences:
        sentence_words = sentence.split()
        sentence_word_count = len(sentence_words)
        
        # If a single sentence exceeds max_tokens, split it by word count
        if sentence_word_count > max_tokens:
            # Flush current chunk first
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_word_count = 0
            
            # Split the long sentence into word-level chunks
            for i in range(0, sentence_word_count, max_tokens):
                chunk_words = sentence_words[i : i + max_tokens]
                chunks.append(" ".join(chunk_words))
            continue
        
        if current_word_count + sentence_word_count > max_tokens and current_chunk:
            # Flush current chunk
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_word_count = 0
        
        current_chunk.extend(sentence_words)
        current_word_count += sentence_word_count
    
    # Don't forget the last chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks


def process_reports(input_path: str = None, output_path: str = None) -> List[dict]:
    """
    Load reports, clean text, and write back the cleaned corpus.
    
    Args:
        input_path: Path to raw reports.json
        output_path: Path to write cleaned reports (defaults to same file)
    
    Returns:
        List of cleaned report dicts.
    """
    base_dir = os.path.join(os.path.dirname(__file__), "..")
    
    if input_path is None:
        input_path = os.path.join(base_dir, "data", "reports", "reports.json")
    if output_path is None:
        output_path = input_path
    
    # Load
    with open(input_path, "r", encoding="utf-8") as f:
        reports = json.load(f)
    
    # Clean
    for report in reports:
        report["text"] = clean_text(report.get("text", ""))
        report["title"] = clean_text(report.get("title", ""))
    
    # Write
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2, ensure_ascii=False)
    
    print(f"Preprocessed {len(reports)} reports -> {output_path}")
    return reports


if __name__ == "__main__":
    process_reports()
