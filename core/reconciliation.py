"""
core/reconciliation.py - Per-case integrity reconciliation
"""
import json
from typing import Dict, Any

from core.extraction import extract_concepts
from core.mapping import find_missing_concepts, to_executive_label


def reconcile_case(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single record and return reconciliation results.

    Returns a dict with:
        record_id, service_line, integrity_score, integrity_level,
        extracted_concepts, missing_concepts, documentation_gaps,
        funding_sensitivity_flag, estimated_variance_pct
    """
    discharge_summary = record.get("discharge_summary", "") or ""
    icd_codes_str = record.get("icd_codes", "") or ""

    # 1. Extract clinical concepts
    extracted = extract_concepts(discharge_summary)

    # 2. Find concepts not reflected in ICD codes
    missing = find_missing_concepts(extracted, icd_codes_str)

    # 3. Convert to executive gap labels
    gaps = [to_executive_label(c) for c in missing]

    # 4. Integrity score: % of extracted concepts that ARE coded
    if not extracted:
        integrity_score = 1.0  # No clinical content detected → no gaps by default
    else:
        coded_count = len(extracted) - len(missing)
        integrity_score = coded_count / len(extracted)

    # 5. Integrity level
    if integrity_score >= 0.85:
        level = "Green"
    elif integrity_score >= 0.60:
        level = "Amber"
    else:
        level = "Red"

    # 6. Funding sensitivity
    missing_count = len(missing)
    if missing_count == 0:
        sensitivity_flag = "Minimal"
        variance_pct = 0.0
    elif missing_count <= 2:
        sensitivity_flag = "Moderate"
        variance_pct = 5.0
    elif missing_count <= 4:
        sensitivity_flag = "Elevated"
        variance_pct = 10.0
    else:
        sensitivity_flag = "High"
        variance_pct = 15.0

    return {
        "record_id": record.get("record_id", ""),
        "service_line": record.get("service_line", "Unknown"),
        "integrity_score": round(integrity_score, 4),
        "integrity_level": level,
        "extracted_concepts": json.dumps(extracted),
        "missing_concepts": json.dumps(missing),
        "documentation_gaps": json.dumps(gaps),
        "funding_sensitivity_flag": sensitivity_flag,
        "estimated_variance_pct": variance_pct,
    }
