"""
core/scoring.py - Aggregate scoring and executive summary computation
"""
import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any

from database import get_connection
from core.reconciliation import reconcile_case


def process_dataset(dataset_id: int) -> Dict[str, Any]:
    """
    Run full reconciliation for all records in a dataset.
    Writes results to reconciliation_results and executive_summary tables.
    Returns the executive summary dict.
    """
    conn = get_connection()

    # Load raw records
    records_df = pd.read_sql_query(
        "SELECT * FROM raw_records WHERE dataset_id=?", conn, params=(dataset_id,)
    )

    results = []
    for _, row in records_df.iterrows():
        result = reconcile_case(row.to_dict())
        result["dataset_id"] = dataset_id
        results.append(result)

    # Clear previous results for this dataset
    conn.execute("DELETE FROM reconciliation_results WHERE dataset_id=?", (dataset_id,))

    # Insert new results
    for r in results:
        conn.execute(
            """INSERT INTO reconciliation_results
               (dataset_id, record_id, service_line, integrity_score, integrity_level,
                extracted_concepts, missing_concepts, documentation_gaps,
                funding_sensitivity_flag, estimated_variance_pct)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                r["dataset_id"], r["record_id"], r["service_line"],
                r["integrity_score"], r["integrity_level"],
                r["extracted_concepts"], r["missing_concepts"],
                r["documentation_gaps"], r["funding_sensitivity_flag"],
                r["estimated_variance_pct"]
            )
        )

    conn.commit()

    # ── Compute executive summary ────────────────────────────────────────────
    total = len(results)
    if total == 0:
        conn.close()
        return {}

    df = pd.DataFrame(results)

    integrity_rate = (df["integrity_score"] >= 0.85).mean()
    mismatch_rate = (df["integrity_level"] == "Red").mean()

    # Funding sensitivity: sum estimated_variance_pct as relative exposure
    avg_low = df["estimated_variance_pct"].mean() * 0.5
    avg_high = df["estimated_variance_pct"].mean()

    # Highest risk service line (most Red cases)
    red_df = df[df["integrity_level"] == "Red"]
    if len(red_df) > 0:
        highest_risk = red_df["service_line"].value_counts().idxmax()
    else:
        highest_risk = "None"

    summary = {
        "dataset_id": dataset_id,
        "generated_at": datetime.now().isoformat(),
        "total_records": total,
        "integrity_rate": round(integrity_rate * 100, 1),
        "mismatch_rate": round(mismatch_rate * 100, 1),
        "estimated_low_variance": round(avg_low, 1),
        "estimated_high_variance": round(avg_high, 1),
        "highest_risk_service_line": highest_risk,
    }

    conn.execute(
        """INSERT INTO executive_summary
           (dataset_id, generated_at, total_records, integrity_rate, mismatch_rate,
            estimated_low_variance, estimated_high_variance, highest_risk_service_line)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            summary["dataset_id"], summary["generated_at"], summary["total_records"],
            summary["integrity_rate"], summary["mismatch_rate"],
            summary["estimated_low_variance"], summary["estimated_high_variance"],
            summary["highest_risk_service_line"]
        )
    )

    conn.commit()
    conn.close()
    return summary


def get_reconciliation_df(dataset_id: int) -> pd.DataFrame:
    """Load reconciliation results as a DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM reconciliation_results WHERE dataset_id=?", conn, params=(dataset_id,)
    )
    conn.close()
    return df


def get_service_line_summary(dataset_id: int) -> pd.DataFrame:
    """Aggregate reconciliation results by service line."""
    df = get_reconciliation_df(dataset_id)
    if df.empty:
        return pd.DataFrame()

    df["missing_count"] = df["missing_concepts"].apply(
        lambda x: len(json.loads(x)) if x else 0
    )

    summary = df.groupby("service_line").agg(
        total_cases=("record_id", "count"),
        mismatch_rate=("integrity_level", lambda x: round((x == "Red").mean() * 100, 1)),
        avg_missing_codes=("missing_count", lambda x: round(x.mean(), 2)),
        avg_variance_pct=("estimated_variance_pct", lambda x: round(x.mean(), 1)),
    ).reset_index()

    summary.columns = [
        "Service Line", "Total Cases", "Mismatch Rate (%)",
        "Avg Missing Codes", "Est. Funding Sensitivity (%)"
    ]
    return summary


def get_top_documentation_gaps(dataset_id: int, top_n: int = 5) -> pd.DataFrame:
    """Return the most common documentation gaps across the dataset."""
    df = get_reconciliation_df(dataset_id)
    if df.empty:
        return pd.DataFrame()

    all_gaps = []
    for gaps_json in df["documentation_gaps"]:
        try:
            all_gaps.extend(json.loads(gaps_json))
        except Exception:
            pass

    if not all_gaps:
        return pd.DataFrame(columns=["Documentation Gap", "Frequency"])

    gap_series = pd.Series(all_gaps).value_counts().head(top_n).reset_index()
    gap_series.columns = ["Documentation Gap", "Frequency"]
    return gap_series


def get_executive_summary(dataset_id: int) -> Dict[str, Any]:
    """Load the latest executive summary for a dataset."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM executive_summary WHERE dataset_id=? ORDER BY generated_at DESC LIMIT 1",
        (dataset_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else {}
