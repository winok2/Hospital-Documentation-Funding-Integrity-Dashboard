# Hospital Documentation & Funding Integrity Dashboard

**Clinical Documentation–Coding Reconciliation Engine (Offline MVP)** — An offline desktop application that helps hospitals identify documentation–coding inconsistencies in retrospective discharge data.

Hospitals generate large volumes of clinical documentation that are coded for reporting and case-mix analysis. Gaps between documented conditions and assigned ICD-10-CA codes can affect reporting accuracy and financial planning. This tool provides a **read-only analytics layer** that extracts concepts from discharge summaries, compares them to assigned codes, flags potential mismatches, and produces executive-level metrics. It runs entirely **offline** within a secure hospital environment.

---

## Features

- **Offline desktop app** — Python + PyQt6; no internet or cloud; deployable inside secure networks.
- **Batch CSV ingestion** — Upload structured discharge data; required fields validated; local processing only.
- **Clinical concept extraction** — Medical terms from free-text summaries with basic negation handling.
- **Coding reconciliation** — Map documented terms to simplified ICD-10-CA; identify documented-but-uncoded or potentially overcoded cases.
- **Funding sensitivity (MVP)** — Placeholder logic to estimate variance range when mismatches are detected; department-level aggregation.
- **Executive dashboard** — Overall mismatch rate, average missing codes per record, variance range, service-line comparison.
- **Case-level drilldown** — Record-level reconciliation view, expandable details, exportable results.
- **Local SQLite storage** — Processed sessions saved in `hospital_dashboard.db`; reload previous analyses; no external database.
- **Reporting** — Export summaries and reconciliation data (see `reporting.py`).

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

**Design principles:** Read-only analytics (no EMR write-back); low friction (file-based ingestion); transparent reconciliation logic; hospital-appropriate UI.

**Intended users:** HIM teams, CDI leads, finance/case-mix analysts, quality and performance teams.

**Current scope (MVP)** — Retrospective batch analytics only. This version does *not* integrate with EMR APIs, modify documentation, provide real-time coding prompts, or replace coding systems.

**Future direction** — Potential evolution: departmental documentation feedback, targeted education analytics, near-real-time pre-discharge flagging, compliance reporting modules.

---

## Disclaimer

This MVP uses simplified ICD mapping and placeholder funding sensitivity logic. It is for **research, prototyping, and internal evaluation** only. It does not replace certified coding review or official case-mix methodologies.

---

## License

Use and modify as needed for your organization.
