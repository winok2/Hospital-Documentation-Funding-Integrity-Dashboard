# Hospital Documentation & Funding Integrity Dashboard

A desktop application for analyzing hospital documentation quality and funding integrity. Load CSV datasets, view reconciliation scores by service line, and drill down into individual cases.

## Features

- **Load CSV datasets** – Ingest discharge summaries, ICD codes, CMG weights, and service lines.
- **Overview** – Executive summary and high-level metrics.
- **Service line view** – Charts and scores by service line (e.g. Cardiology, Pulmonology).
- **Case-level view** – Per-record reconciliation and documentation review.
- **Local SQLite storage** – All data stored in `hospital_dashboard.db` in the project folder.
- **Reporting** – Export summaries and reconciliation data (see `reporting.py`).

## Requirements

- Python 3.10+
- Dependencies listed in `requirements.txt` (PyQt6, PyQt6-Charts, pandas)

## Setup

```bash
# Clone or extract the project, then install dependencies
cd hospital_dashboard
pip install -r requirements.txt
```

**Note:** If you have multiple Python versions, install into the same Python you will use to run the app (e.g. `python -m pip install -r requirements.txt` or `py -3.11 -m pip install -r requirements.txt`).

## Running the app

From the project root:

```bash
python main.py
```

If you get `ModuleNotFoundError: No module named 'PyQt6'`, your default `python` may be a different version than the one where you installed packages. Use the interpreter that has the dependencies, for example:

```bash
py -3.11 main.py
```

The main window opens with tabs: **Overview**, **Service Line**, and **Case**. Use **Load Dataset** to choose a CSV file.

## CSV format

Your CSV must include these columns (names are case-insensitive, spaces allowed):

| Column             | Required | Description                    |
|--------------------|----------|--------------------------------|
| `record_id`        | Yes      | Unique record identifier      |
| `discharge_summary`| Yes      | Free-text discharge summary   |
| `icd_codes`        | Yes      | ICD codes (e.g. semicolon-sep)|
| `service_line`     | Yes      | Service line name              |
| `cmg_weight`       | No       | CMG weight (numeric)          |

See `sample_data.csv` for an example.

## Project structure

```
hospital_dashboard/
├── main.py              # Entry point
├── database.py          # SQLite schema and connection
├── reporting.py         # Export / reporting helpers
├── requirements.txt
├── sample_data.csv      # Example input CSV
├── core/
│   ├── ingestion.py     # CSV load and DB insert
│   ├── extraction.py    # Concept extraction from text
│   ├── mapping.py       # Concept mapping / labels
│   ├── reconciliation.py# Case reconciliation logic
│   └── scoring.py       # Dataset scoring and summaries
└── ui/
    ├── main_window.py   # Main window and tabs
    ├── overview_tab.py  # Overview tab
    ├── service_tab.py   # Service line tab
    └── case_tab.py      # Case-level tab
```

## License

Use and modify as needed for your organization.
