"""
core/ingestion.py - CSV ingestion and database loading
"""
import pandas as pd
import sqlite3
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_connection


REQUIRED_COLUMNS = {"record_id", "discharge_summary", "icd_codes", "service_line"}


def load_csv(file_path: str) -> tuple[int, str]:
    """
    Load a CSV file into the database.
    Returns (dataset_id, dataset_name) on success.
    Raises ValueError if CSV is invalid.
    """
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise ValueError(f"Could not read file: {e}")

    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing required columns: {', '.join(missing)}")

    # Fill optional columns
    if "cmg_weight" not in df.columns:
        df["cmg_weight"] = None

    df = df.fillna("")

    dataset_name = os.path.splitext(os.path.basename(file_path))[0]
    loaded_at = datetime.now().isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO datasets (name, file_path, loaded_at, record_count) VALUES (?, ?, ?, ?)",
        (dataset_name, file_path, loaded_at, len(df))
    )
    dataset_id = cursor.lastrowid

    for _, row in df.iterrows():
        cursor.execute(
            """INSERT INTO raw_records
               (dataset_id, record_id, discharge_summary, icd_codes, cmg_weight, service_line)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                dataset_id,
                str(row["record_id"]),
                str(row["discharge_summary"]),
                str(row["icd_codes"]),
                row.get("cmg_weight") or None,
                str(row["service_line"]),
            )
        )

    conn.commit()
    conn.close()
    return dataset_id, dataset_name


def get_raw_records(dataset_id: int) -> pd.DataFrame:
    """Retrieve all raw records for a dataset as a DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM raw_records WHERE dataset_id=?", conn, params=(dataset_id,)
    )
    conn.close()
    return df
