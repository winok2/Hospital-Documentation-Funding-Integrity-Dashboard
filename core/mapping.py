"""
core/mapping.py - Maps clinical concepts to expected ICD-10 code prefixes
"""
from typing import Dict, List, Set

# ── Concept → ICD-10 code prefix mapping ─────────────────────────────────────
CONCEPT_TO_ICD_PREFIX: Dict[str, List[str]] = {
    "Heart Failure":                ["I50"],
    "Acute MI":                     ["I21", "I22"],
    "Atrial Fibrillation":          ["I48"],
    "Hypertension":                 ["I10", "I11", "I12", "I13"],
    "Coronary Artery Disease":      ["I25"],
    "Pneumonia":                    ["J18", "J15", "J13", "J12"],
    "COPD":                         ["J44", "J43"],
    "Respiratory Failure":          ["J96"],
    "Pulmonary Embolism":           ["I26"],
    "Diabetes Type 2":              ["E11"],
    "Diabetes Type 1":              ["E10"],
    "Hyperglycemia":                ["R73", "E11.65", "E10.65"],
    "Hypoglycemia":                 ["E16", "E11.64", "E10.64"],
    "Sepsis":                       ["A41", "A40"],
    "Acute Kidney Injury":          ["N17"],
    "Chronic Kidney Disease":       ["N18"],
    "Stroke":                       ["I63", "I61", "I64"],
    "Altered Mental Status":        ["R41", "G93.4", "F05"],
    "Seizure":                      ["G40", "R56"],
    "Post-Operative Complication":  ["T81"],
    "DVT":                          ["I82"],
    "Anemia":                       ["D50", "D51", "D52", "D53", "D64"],
    "Malnutrition":                 ["E40", "E41", "E42", "E43", "E44", "E46"],
    "Pressure Ulcer":               ["L89"],
    "Major Complication":           ["T80", "T81", "T82"],
    "Multi-organ Dysfunction":      ["R65"],
    "Morbid Obesity":               ["E66"],
}


def get_expected_prefixes(concepts: List[str]) -> Dict[str, List[str]]:
    """Return a mapping of concept → expected ICD prefixes."""
    return {c: CONCEPT_TO_ICD_PREFIX[c] for c in concepts if c in CONCEPT_TO_ICD_PREFIX}


def find_missing_concepts(concepts: List[str], icd_codes_str: str) -> List[str]:
    """
    Given extracted concepts and documented ICD codes,
    return which concepts are NOT covered by any documented code.
    """
    if not icd_codes_str:
        return concepts[:]

    # Normalize documented codes
    documented = [c.strip().upper() for c in icd_codes_str.split(";") if c.strip()]

    missing = []
    for concept in concepts:
        expected_prefixes = CONCEPT_TO_ICD_PREFIX.get(concept, [])
        if not expected_prefixes:
            continue
        covered = any(
            any(doc.startswith(prefix.upper()) for prefix in expected_prefixes)
            for doc in documented
        )
        if not covered:
            missing.append(concept)

    return missing


# Human-readable gap labels for executive UI
GAP_LABELS = {
    "Heart Failure":               "Potential Under-Documented Cardiac Complexity",
    "Acute MI":                    "Potential Under-Documented Acute Cardiac Event",
    "Atrial Fibrillation":         "Rhythm Disorder Not Reflected in Coding",
    "Hypertension":                "Chronic Condition Specificity Gap",
    "Coronary Artery Disease":     "Chronic Cardiovascular Complexity Gap",
    "Pneumonia":                   "Respiratory Infection Documentation Gap",
    "COPD":                        "Chronic Pulmonary Condition Not Coded",
    "Respiratory Failure":         "Acute Respiratory Complexity Not Captured",
    "Pulmonary Embolism":          "High-Acuity Event Without Corresponding Code",
    "Diabetes Type 2":             "Chronic Metabolic Condition Coding Gap",
    "Diabetes Type 1":             "Insulin-Dependent Complexity Not Reflected",
    "Hyperglycemia":               "Metabolic Instability Specificity Gap",
    "Hypoglycemia":                "Acute Metabolic Event Documentation Gap",
    "Sepsis":                      "Critical Infectious Complexity Under-Documented",
    "Acute Kidney Injury":         "Acute Organ Compromise Not Captured",
    "Chronic Kidney Disease":      "Chronic Comorbidity Specificity Gap",
    "Stroke":                      "Neurological Event Coding Gap",
    "Altered Mental Status":       "Neurological Complexity Under-Represented",
    "Seizure":                     "Neurological Episode Documentation Gap",
    "Post-Operative Complication": "Procedural Complication Not Fully Coded",
    "DVT":                         "Vascular Complication Documentation Gap",
    "Anemia":                      "Hematologic Complication Not Coded",
    "Malnutrition":                "Nutritional Risk Not Reflected in Coding",
    "Pressure Ulcer":              "Wound Complexity Documentation Gap",
    "Major Complication":          "High-Severity Event Specificity Gap",
    "Multi-organ Dysfunction":     "Multi-System Complexity Under-Documented",
    "Morbid Obesity":              "Comorbid Complexity Coding Gap",
}


def to_executive_label(concept: str) -> str:
    """Return an executive-friendly label for a gap concept."""
    return GAP_LABELS.get(concept, f"Documentation Gap: {concept}")
