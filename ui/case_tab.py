"""
ui/case_tab.py - Case Review & Export Tab
"""
import json
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView,
    QDialog, QTextEdit, QScrollArea, QFileDialog, QMessageBox,
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

NAVY = "#1a2942"
ACCENT = "#3a6bc4"
WHITE = "#ffffff"
BG = "#f4f7fb"


STATUS_COLORS = {
    "Green": ("#1e8449", "#d5f5e3"),
    "Amber": ("#7d6608", "#fdebd0"),
    "Red":   ("#922b21", "#fadbd8"),
}


class CaseDetailDialog(QDialog):
    def __init__(self, record: dict, recon: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Case Detail — Record {record.get('record_id', '')}")
        self.setMinimumSize(700, 560)
        self.setStyleSheet(f"background: {WHITE};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header
        hdr = QLabel(f"Record ID: {record.get('record_id', '')}  |  Service Line: {record.get('service_line', '')}")
        hdr.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        hdr.setStyleSheet(f"color: {NAVY};")
        layout.addWidget(hdr)

        level = recon.get("integrity_level", "Green")
        fg, bg = STATUS_COLORS.get(level, ("#000", "#fff"))
        badge = QLabel(f"  Integrity Status: {level}  ")
        badge.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        badge.setStyleSheet(f"color: {fg}; background: {bg}; border-radius: 3px; padding: 2px 8px;")
        badge.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        layout.addWidget(badge)

        # Discharge summary
        layout.addWidget(self._section("Discharge Summary"))
        summary_box = QTextEdit()
        summary_box.setReadOnly(True)
        summary_box.setPlainText(record.get("discharge_summary", "Not available"))
        summary_box.setMaximumHeight(140)
        summary_box.setStyleSheet("border: 1px solid #dde4ef; font-size: 10px; padding: 6px;")
        layout.addWidget(summary_box)

        # Documented clinical concepts
        layout.addWidget(self._section("Documented Clinical Concepts"))
        concepts = json.loads(recon.get("extracted_concepts", "[]"))
        concepts_label = QLabel(", ".join(concepts) if concepts else "No clinical concepts identified")
        concepts_label.setWordWrap(True)
        concepts_label.setStyleSheet(f"color: #2c3e50; font-size: 10px; padding: 6px; background: {BG}; border: 1px solid #dde4ef;")
        layout.addWidget(concepts_label)

        # Assigned ICD codes
        layout.addWidget(self._section("Assigned ICD Codes"))
        icd_label = QLabel(record.get("icd_codes", "None") or "None")
        icd_label.setWordWrap(True)
        icd_label.setStyleSheet(f"color: #2c3e50; font-size: 10px; padding: 6px; background: {BG}; border: 1px solid #dde4ef;")
        layout.addWidget(icd_label)

        # Suggested review areas
        layout.addWidget(self._section("Suggested Review Areas"))
        gaps = json.loads(recon.get("documentation_gaps", "[]"))
        if gaps:
            gaps_text = "\n".join(f"  •  {g}" for g in gaps)
        else:
            gaps_text = "  No documentation gaps identified. Record appears well-documented."
        review_label = QLabel(gaps_text)
        review_label.setWordWrap(True)
        review_label.setStyleSheet(
            f"color: {'#922b21' if gaps else '#1e8449'}; font-size: 10px; padding: 8px; "
            f"background: {'#fadbd8' if gaps else '#d5f5e3'}; border: 1px solid #dde4ef;"
        )
        layout.addWidget(review_label)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(100)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {NAVY}; color: white; border-radius: 4px;
                padding: 6px 14px; font-size: 10px;
            }}
            QPushButton:hover {{ background: {ACCENT}; }}
        """)
        close_btn.clicked.connect(self.close)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _section(self, title: str) -> QLabel:
        lbl = QLabel(title)
        lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {NAVY}; border-bottom: 1px solid #dde4ef; padding-bottom: 2px;")
        return lbl


class CaseTab(QWidget):
    request_clear = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._records = []
        self._recon = []
        self._dataset_id = None
        self._dataset_name = "Dataset"
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        # Header + buttons
        top = QHBoxLayout()
        title = QLabel("Case Review & Documentation Intelligence")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {NAVY};")
        top.addWidget(title)
        top.addStretch()

        btn_style = lambda bg, hover: f"""
            QPushButton {{
                background: {bg}; color: white; border-radius: 4px;
                padding: 7px 16px; font-size: 10px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {hover}; }}
        """

        self._btn_pdf = QPushButton("Export Executive Summary")
        self._btn_pdf.setStyleSheet(btn_style(NAVY, ACCENT))
        self._btn_pdf.clicked.connect(self._export_pdf)

        self._btn_csv = QPushButton("Export Detailed CSV")
        self._btn_csv.setStyleSheet(btn_style("#2a6099", "#3a78b8"))
        self._btn_csv.clicked.connect(self._export_csv)

        self._btn_clear = QPushButton("Clear Dataset")
        self._btn_clear.setStyleSheet(btn_style("#922b21", "#c0392b"))
        self._btn_clear.clicked.connect(self._confirm_clear)

        for btn in [self._btn_pdf, self._btn_csv, self._btn_clear]:
            top.addWidget(btn)

        root.addLayout(top)

        sub = QLabel("Click any row to view full case detail and documentation review areas.")
        sub.setFont(QFont("Segoe UI", 9))
        sub.setStyleSheet("color: #6b7a99;")
        root.addWidget(sub)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels([
            "Record ID", "Service Line", "Integrity Status",
            "Documentation Gaps", "Sensitivity Flag"
        ])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setStyleSheet("""
            QTableWidget { border: 1px solid #dde4ef; font-size: 10px; }
            QHeaderView::section { background: #1a2942; color: white; padding: 7px; font-size: 10px; }
            QTableWidget::item:alternate { background: #f4f7fb; }
            QTableWidget::item:selected { background: #2a4480; color: white; }
        """)
        self._table.cellDoubleClicked.connect(self._open_detail)
        root.addWidget(self._table)

    def refresh(self, records: list, recon_df, dataset_id: int, dataset_name: str = "Dataset"):
        self._records = records
        self._recon = recon_df.to_dict("records") if recon_df is not None and not recon_df.empty else []
        self._dataset_id = dataset_id
        self._dataset_name = dataset_name

        self._table.setRowCount(0)
        for recon in self._recon:
            row = self._table.rowCount()
            self._table.insertRow(row)

            self._table.setItem(row, 0, QTableWidgetItem(str(recon.get("record_id", ""))))
            self._table.setItem(row, 1, QTableWidgetItem(str(recon.get("service_line", ""))))

            level = recon.get("integrity_level", "Green")
            fg, bg = STATUS_COLORS.get(level, ("#000", "#fff"))
            status_item = QTableWidgetItem(f"  {level}  ")
            status_item.setForeground(QColor(fg))
            status_item.setBackground(QColor(bg))
            status_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self._table.setItem(row, 2, status_item)

            gaps = json.loads(recon.get("documentation_gaps", "[]"))
            gaps_str = "; ".join(gaps[:2]) + (" …" if len(gaps) > 2 else "") if gaps else "None identified"
            self._table.setItem(row, 3, QTableWidgetItem(gaps_str))

            flag = recon.get("funding_sensitivity_flag", "Minimal")
            flag_item = QTableWidgetItem(flag)
            flag_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if flag == "High":
                flag_item.setForeground(QColor("#c0392b"))
            elif flag == "Elevated":
                flag_item.setForeground(QColor("#d68910"))
            self._table.setItem(row, 4, flag_item)

    def _open_detail(self, row: int, col: int):
        if row >= len(self._recon):
            return
        recon = self._recon[row]
        record_id = recon.get("record_id", "")
        record = next((r for r in self._records if str(r.get("record_id")) == str(record_id)), {})
        dlg = CaseDetailDialog(record, recon, self)
        dlg.exec()

    def _export_pdf(self):
        if not self._dataset_id:
            QMessageBox.warning(self, "No Data", "Please load a dataset before exporting.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Executive Summary", f"{self._dataset_name}_executive_summary.html",
            "HTML Files (*.html);;All Files (*)"
        )
        if path:
            try:
                from reporting import export_pdf
                export_pdf(self._dataset_id, path, self._dataset_name)
                QMessageBox.information(self, "Export Complete",
                    f"Executive summary saved to:\n{path}\n\nOpen in any web browser to view or print.")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", str(e))

    def _export_csv(self):
        if not self._dataset_id:
            QMessageBox.warning(self, "No Data", "Please load a dataset before exporting.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", f"{self._dataset_name}_case_review.csv",
            "CSV Files (*.csv);;All Files (*)"
        )
        if path:
            try:
                from reporting import export_csv
                export_csv(self._dataset_id, path)
                QMessageBox.information(self, "Export Complete", f"CSV saved to:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", str(e))

    def _confirm_clear(self):
        if not self._dataset_id:
            return
        reply = QMessageBox.question(
            self, "Clear Dataset",
            "This will permanently remove the current dataset and all analysis results.\n\nProceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.request_clear.emit()
