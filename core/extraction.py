"""
core/extraction.py - Rule-based clinical concept extractor
Extracts clinical terms from discharge summaries using keyword dictionaries.
No external NLP dependencies required (spaCy optional).
"""
import re
from typing import List, Dict

# ── Clinical concept dictionary ──────────────────────────────────────────────
# Maps readable concept labels to their trigger phrases.
# Grouped by clinical category for maintainability.

CLINICAL_CONCEPTS: Dict[str, List[str]] = {
    # Cardiovascular
    "Heart Failure": ["heart failure", "chf", "congestive heart failure", "cardiac failure"],
    "Acute MI": ["myocardial infarction", "heart attack", "stemi", "nstemi", "ami"],
    "Atrial Fibrillation": ["atrial fibrillation", "afib", "a-fib", "af "],
    "Hypertension": ["hypertension", "high blood pressure", "htn"],
    "Coronary Artery Disease": ["coronary artery disease", "cad", "ischemic heart"],

    # Respiratory
    "Pneumonia": ["pneumonia", "pneumonitis", "lung infection"],
    "COPD": ["copd", "chronic obstructive pulmonary", "emphysema", "chronic bronchitis"],
    "Respiratory Failure": ["respiratory failure", "respiratory distress", "ards"],
    "Pulmonary Embolism": ["pulmonary embolism", "pe ", "blood clot in lung"],

    # Metabolic / Endocrine
    "Diabetes Type 2": ["type 2 diabetes", "t2dm", "diabetes mellitus type 2", "non-insulin"],
    "Diabetes Type 1": ["type 1 diabetes", "t1dm", "insulin-dependent diabetes"],
    "Hyperglycemia": ["hyperglycemia", "elevated blood glucose", "high blood sugar"],
    "Hypoglycemia": ["hypoglycemia", "low blood sugar", "low glucose"],
    "Sepsis": ["sepsis", "septicemia", "bloodstream infection", "systemic infection"],
    "Acute Kidney Injury": ["acute kidney injury", "aki", "acute renal failure", "renal insufficiency"],
    "Chronic Kidney Disease": ["chronic kidney disease", "ckd", "chronic renal disease"],

    # Neurological
    "Stroke": ["stroke", "cva", "cerebrovascular accident", "ischemic stroke", "hemorrhagic stroke"],
    "Altered Mental Status": ["altered mental status", "confusion", "encephalopathy", "delirium"],
    "Seizure": ["seizure", "epilepsy", "convulsion", "status epilepticus"],

    # Surgical / Procedural
    "Post-Operative Complication": ["post-op complication", "surgical complication", "wound dehiscence", "anastomotic leak"],
    "DVT": ["deep vein thrombosis", "dvt", "venous thrombosis"],
    "Anemia": ["anemia", "low hemoglobin", "low hgb", "iron deficiency"],
    "Malnutrition": ["malnutrition", "nutritional deficiency", "undernutrition", "cachexia"],
    "Pressure Ulcer": ["pressure ulcer", "pressure injury", "decubitus", "bedsore"],

    # Complexity / Acuity
    "Major Complication": ["major complication", "life-threatening", "critical condition"],
    "Multi-organ Dysfunction": ["multi-organ", "multiorgan", "mods", "multiple organ failure"],
    "Morbid Obesity": ["morbid obesity", "bmi > 40", "bmi>40", "class iii obesity"],
}

# Negation window – if these words appear within N tokens before a concept, skip it
NEGATION_PHRASES = [
    "no ", "not ", "without ", "denies ", "negative for ", "ruled out",
    "no evidence of", "absent", "unremarkable for", "no signs of"
]
NEGATION_WINDOW = 60  # characters


def _is_negated(text: str, match_start: int) -> bool:
    """Check if a concept match is preceded by negation language."""
    window_start = max(0, match_start - NEGATION_WINDOW)
    preceding = text[window_start:match_start].lower()
    return any(neg in preceding for neg in NEGATION_PHRASES)


def extract_concepts(text: str) -> List[str]:
    """
    Extract affirmed clinical concepts from a discharge summary.
    Returns a deduplicated list of concept labels.
    """
    if not text or not isinstance(text, str):
        return []

    text_lower = text.lower()
    found = []

    for concept, phrases in CLINICAL_CONCEPTS.items():
        for phrase in phrases:
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            for match in pattern.finditer(text_lower):
                if not _is_negated(text_lower, match.start()):
                    found.append(concept)
                    break  # one match per concept is enough

    return list(dict.fromkeys(found))  # preserve order, deduplicate
