"""
reporting.py - PDF and CSV export
"""
import csv
import json
import os
from datetime import datetime

from database import get_connection
from core.scoring import get_reconciliation_df, get_service_line_summary, get_executive_summary


def export_csv(dataset_id: int, output_path: str) -> str:
    """Export full reconciliation results to CSV."""
    df = get_reconciliation_df(dataset_id)
    if df.empty:
        raise ValueError("No data available for export.")

    # Prettify for export
    export_cols = [
        "record_id", "service_line", "integrity_level",
        "integrity_score", "documentation_gaps",
        "funding_sensitivity_flag", "estimated_variance_pct"
    ]
    out_df = df[export_cols].copy()
    out_df["documentation_gaps"] = out_df["documentation_gaps"].apply(
        lambda x: "; ".join(json.loads(x)) if x else ""
    )
    out_df["integrity_score"] = (out_df["integrity_score"] * 100).round(1).astype(str) + "%"
    out_df["estimated_variance_pct"] = out_df["estimated_variance_pct"].astype(str) + "%"

    out_df.columns = [
        "Record ID", "Service Line", "Integrity Status",
        "Integrity Score", "Documentation Gaps",
        "Sensitivity Flag", "Estimated Variance"
    ]
    out_df.to_csv(output_path, index=False)
    return output_path


def export_pdf(dataset_id: int, output_path: str, dataset_name: str = "Dataset") -> str:
    """
    Generate an executive summary PDF using only stdlib (no reportlab required).
    Falls back to a well-formatted HTML file if PDF libraries unavailable.
    """
    summary = get_executive_summary(dataset_id)
    service_df = get_service_line_summary(dataset_id)
    generated = datetime.now().strftime("%B %d, %Y  %H:%M")

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Executive Summary – {dataset_name}</title>
<style>
  body {{ font-family: Georgia, serif; margin: 40px; color: #1a2942; background: #fff; }}
  h1 {{ font-size: 22pt; color: #1a2942; border-bottom: 2px solid #1a2942; padding-bottom: 8px; }}
  h2 {{ font-size: 14pt; color: #2a4480; margin-top: 28px; }}
  .meta {{ color: #666; font-size: 10pt; margin-bottom: 24px; }}
  .kpi-row {{ display: flex; gap: 24px; margin: 20px 0; flex-wrap: wrap; }}
  .kpi {{ background: #f4f7fb; border-left: 4px solid #2a4480; padding: 14px 20px; min-width: 160px; }}
  .kpi-val {{ font-size: 24pt; font-weight: bold; color: #1a2942; }}
  .kpi-label {{ font-size: 9pt; color: #555; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 4px; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 12px; font-size: 10pt; }}
  th {{ background: #1a2942; color: white; padding: 8px 12px; text-align: left; }}
  td {{ padding: 7px 12px; border-bottom: 1px solid #dde4ef; }}
  tr:nth-child(even) td {{ background: #f7f9fc; }}
  .footer {{ margin-top: 40px; font-size: 9pt; color: #999; border-top: 1px solid #dde; padding-top: 10px; }}
  @media print {{ body {{ margin: 20px; }} }}
</style>
</head>
<body>
<h1>Hospital Documentation & Funding Integrity</h1>
<div class="meta">Executive Summary Report &nbsp;|&nbsp; Dataset: <strong>{dataset_name}</strong> &nbsp;|&nbsp; Generated: {generated}</div>

<h2>Key Performance Indicators</h2>
<div class="kpi-row">
  <div class="kpi">
    <div class="kpi-val">{summary.get('total_records', 0)}</div>
    <div class="kpi-label">Records Analyzed</div>
  </div>
  <div class="kpi">
    <div class="kpi-val">{summary.get('integrity_rate', 0)}%</div>
    <div class="kpi-label">Documentation Integrity Rate</div>
  </div>
  <div class="kpi">
    <div class="kpi-val">{summary.get('mismatch_rate', 0)}%</div>
    <div class="kpi-label">Mismatch Exposure Rate</div>
  </div>
  <div class="kpi">
    <div class="kpi-val">{summary.get('estimated_low_variance', 0)}–{summary.get('estimated_high_variance', 0)}%</div>
    <div class="kpi-label">Estimated Funding Sensitivity</div>
  </div>
  <div class="kpi">
    <div class="kpi-val">{summary.get('highest_risk_service_line', 'N/A')}</div>
    <div class="kpi-label">Highest Risk Service Line</div>
  </div>
</div>

<h2>Service Line Performance</h2>
"""

    if not service_df.empty:
        html += "<table><thead><tr>"
        for col in service_df.columns:
            html += f"<th>{col}</th>"
        html += "</tr></thead><tbody>"
        for _, row in service_df.iterrows():
            html += "<tr>"
            for val in row:
                html += f"<td>{val}</td>"
            html += "</tr>"
        html += "</tbody></table>"
    else:
        html += "<p>No service line data available.</p>"

    html += f"""
<div class="footer">
  Confidential – For Internal Executive Use Only &nbsp;|&nbsp;
  Hospital Documentation &amp; Funding Integrity Dashboard &nbsp;|&nbsp; {generated}
</div>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path
