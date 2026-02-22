"""
database.py - SQLite database management for Hospital Documentation Dashboard
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "hospital_dashboard.db")


def get_connection():
    """Return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    """Create all required tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            file_path TEXT,
            loaded_at TEXT NOT NULL,
            record_count INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS raw_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id INTEGER NOT NULL,
            record_id TEXT NOT NULL,
            discharge_summary TEXT,
            icd_codes TEXT,
            cmg_weight REAL,
            service_line TEXT,
            FOREIGN KEY (dataset_id) REFERENCES datasets(id)
        );

        CREATE TABLE IF NOT EXISTS reconciliation_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id INTEGER NOT NULL,
            record_id TEXT NOT NULL,
            service_line TEXT,
            integrity_score REAL,
            integrity_level TEXT,
            extracted_concepts TEXT,
            missing_concepts TEXT,
            documentation_gaps TEXT,
            funding_sensitivity_flag TEXT,
            estimated_variance_pct REAL,
            FOREIGN KEY (dataset_id) REFERENCES datasets(id)
        );

        CREATE TABLE IF NOT EXISTS executive_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id INTEGER NOT NULL,
            generated_at TEXT NOT NULL,
            total_records INTEGER,
            integrity_rate REAL,
            mismatch_rate REAL,
            estimated_low_variance REAL,
            estimated_high_variance REAL,
            highest_risk_service_line TEXT,
            FOREIGN KEY (dataset_id) REFERENCES datasets(id)
        );
    """)

    conn.commit()
    conn.close()


def get_latest_dataset_id():
    """Return the most recently loaded dataset ID."""
    conn = get_connection()
    row = conn.execute("SELECT id FROM datasets ORDER BY loaded_at DESC LIMIT 1").fetchone()
    conn.close()
    return row["id"] if row else None


def clear_dataset(dataset_id):
    """Remove all data for a given dataset."""
    conn = get_connection()
    conn.execute("DELETE FROM reconciliation_results WHERE dataset_id=?", (dataset_id,))
    conn.execute("DELETE FROM raw_records WHERE dataset_id=?", (dataset_id,))
    conn.execute("DELETE FROM executive_summary WHERE dataset_id=?", (dataset_id,))
    conn.execute("DELETE FROM datasets WHERE id=?", (dataset_id,))
    conn.commit()
    conn.close()
