"""
Recurrence Ranking

Computes a "recurrence score" for each report based on how many other reports
share the same (equipment, hazard_type) pair.

Course mapping: IR Unit V — a simplified, non-graph analogue of link-based/
PageRank-style importance. Co-occurrence count stands in for "inbound links":
reports that describe frequently-recurring equipment+hazard combinations
receive higher scores, analogous to highly-linked pages being more "authoritative."
"""

import json
import os
import logging
from typing import Dict, List
from collections import Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def compute_recurrence_scores(reports: List[dict]) -> Dict[str, float]:
    """
    Compute recurrence scores for all reports.
    
    For each report, the recurrence score is based on how many other reports
    share the same (equipment, hazard_type) pair. Scores are normalized to [0, 1].
    
    Singleton reports (unique equipment+hazard combo) get a score of 0.
    Reports with the most common combo get a score of 1.
    
    Args:
        reports: List of report dicts with 'id', 'equipment', 'hazard_type'.
    
    Returns:
        Dict mapping report_id -> recurrence_score (float, 0-1).
    """
    # Count (equipment, hazard_type) pair frequencies
    pair_counts = Counter()
    report_pairs = {}
    
    for report in reports:
        equipment = report.get("equipment", "unknown")
        hazard = report.get("hazard_type", "unknown")
        pair = (equipment, hazard)
        pair_counts[pair] += 1
        report_pairs[report["id"]] = pair
    
    # Find max count for normalization (exclude 1 since we subtract self)
    max_count = max(pair_counts.values()) if pair_counts else 1
    
    # Compute scores: (count_of_pair - 1) / (max_count - 1)
    # -1 because we don't count the report itself
    scores = {}
    for report in reports:
        pair = report_pairs[report["id"]]
        count = pair_counts[pair]
        
        if max_count <= 1:
            score = 0.0
        else:
            # Number of OTHER reports with same pair
            other_count = count - 1
            max_other = max_count - 1
            score = other_count / max_other if max_other > 0 else 0.0
        
        scores[report["id"]] = round(score, 4)
    
    # Log summary
    top_pairs = pair_counts.most_common(5)
    logger.info(
        f"Computed recurrence scores for {len(reports)} reports. "
        f"Top recurring pairs: {top_pairs}"
    )
    
    return scores


def get_recurrence_pattern_summary(
    reports: List[dict],
    scores: Dict[str, float] = None,
) -> str:
    """
    Generate a human-readable summary of recurrence patterns in the given reports.
    
    Args:
        reports: List of report dicts (typically the top-k retrieved reports).
        scores: Optional pre-computed recurrence scores.
    
    Returns:
        A summary string describing the recurrence patterns.
    """
    if not reports:
        return "No reports provided for pattern analysis."
    
    # Count pairs in the provided subset
    pair_counts = Counter()
    for report in reports:
        equipment = report.get("equipment", "unknown")
        hazard = report.get("hazard_type", "unknown")
        pair_counts[(equipment, hazard)] += 1
    
    # Find repeating patterns (count > 1)
    repeating = [(pair, count) for pair, count in pair_counts.most_common() if count > 1]
    
    if not repeating:
        return f"No recurring patterns found among the {len(reports)} retrieved reports."
    
    parts = []
    for (equipment, hazard), count in repeating:
        parts.append(f"{count} of {len(reports)} retrieved reports involve {equipment} with {hazard}")
    
    return "; ".join(parts) + "."


if __name__ == "__main__":
    reports_path = os.path.join(os.path.dirname(__file__), "..", "data", "reports", "reports.json")
    
    if not os.path.exists(reports_path):
        print("Reports file not found. Run scripts/generate_synthetic_reports.py first.")
    else:
        with open(reports_path, "r", encoding="utf-8") as f:
            reports = json.load(f)
        
        scores = compute_recurrence_scores(reports)
        
        # Show distribution
        print(f"\nRecurrence scores for {len(scores)} reports:")
        score_values = list(scores.values())
        print(f"  Min: {min(score_values):.4f}")
        print(f"  Max: {max(score_values):.4f}")
        print(f"  Mean: {sum(score_values)/len(score_values):.4f}")
        
        # Show top recurring
        top_reports = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"\nTop 5 recurring reports:")
        for rid, score in top_reports:
            report = next(r for r in reports if r["id"] == rid)
            print(f"  {rid}: score={score:.4f} — {report['equipment']} / {report['hazard_type']}")
