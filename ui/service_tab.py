"""
ui/service_tab.py - Service Line Insights Tab
"""
import json
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy,
    QListWidget, QListWidgetItem, QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis

NAVY = "#1a2942"
ACCENT = "#3a6bc4"
WHITE = "#ffffff"
BG = "#f4f7fb"


class ServiceTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._recon_df = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        header = QLabel("Service Line Performance Intelligence")
        header.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {NAVY};")
        root.addWidget(header)

        sub = QLabel("Select a service line to explore documentation patterns and gap distribution.")
        sub.setFont(QFont("Segoe UI", 9))
        sub.setStyleSheet("color: #6b7a99;")
        root.addWidget(sub)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── Left: summary table ───────────────────────────────────────────────
        left = QFrame()
        left.setStyleSheet(f"background: {WHITE}; border: 1px solid #dde4ef; border-radius: 4px;")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(14, 12, 14, 12)

        tbl_label = QLabel("Service Line Summary")
        tbl_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        tbl_label.setStyleSheet(f"color: {NAVY};")
        left_layout.addWidget(tbl_label)

        self._service_table = QTableWidget()
        self._service_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._service_table.setAlternatingRowColors(True)
        self._service_table.verticalHeader().setVisible(False)
        self._service_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._service_table.setStyleSheet("""
            QTableWidget { border: none; font-size: 10px; }
            QHeaderView::section { background: #1a2942; color: white; padding: 6px; font-size: 10px; }
            QTableWidget::item:alternate { background: #f4f7fb; }
            QTableWidget::item:selected { background: #2a4480; color: white; }
        """)
        self._service_table.selectionModel().selectionChanged.connect(self._on_row_selected)
        left_layout.addWidget(self._service_table)

        splitter.addWidget(left)

        # ── Right: detail panel ───────────────────────────────────────────────
        right = QFrame()
        right.setStyleSheet(f"background: {WHITE}; border: 1px solid #dde4ef; border-radius: 4px;")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(16, 14, 16, 14)
        right_layout.setSpacing(14)

        self._detail_title = QLabel("Select a service line to view details")
        self._detail_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self._detail_title.setStyleSheet(f"color: {NAVY};")
        right_layout.addWidget(self._detail_title)

        # Chart
        self._chart = QChart()
        self._chart.setBackgroundBrush(QColor(WHITE))
        self._chart.legend().setVisible(False)
        self._chart_view = QChartView(self._chart)
        self._chart_view.setMinimumHeight(200)
        right_layout.addWidget(self._chart_view)

        # Gap list
        gap_label = QLabel("Most Common Documentation Gaps")
        gap_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        gap_label.setStyleSheet(f"color: {NAVY};")
        right_layout.addWidget(gap_label)

        self._gap_list = QListWidget()
        self._gap_list.setStyleSheet("""
            QListWidget { border: 1px solid #dde4ef; border-radius: 3px; font-size: 10px; }
            QListWidget::item { padding: 5px 8px; border-bottom: 1px solid #eef; }
            QListWidget::item:alternate { background: #f7f9fc; }
        """)
        self._gap_list.setAlternatingRowColors(True)
        right_layout.addWidget(self._gap_list)

        splitter.addWidget(right)
        splitter.setSizes([520, 400])

        root.addWidget(splitter)

    def refresh(self, service_df: pd.DataFrame, recon_df: pd.DataFrame):
        self._recon_df = recon_df
        self._service_table.clear()

        if service_df is None or service_df.empty:
            self._service_table.setRowCount(0)
            return

        cols = list(service_df.columns)
        self._service_table.setColumnCount(len(cols))
        self._service_table.setHorizontalHeaderLabels(cols)
        self._service_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, len(cols)):
            self._service_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        self._service_table.setRowCount(len(service_df))
        for row_idx, (_, row) in enumerate(service_df.iterrows()):
            for col_idx, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter if col_idx > 0 else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self._service_table.setItem(row_idx, col_idx, item)

    def _on_row_selected(self, selected, deselected):
        indexes = selected.indexes()
        if not indexes:
            return
        row = indexes[0].row()
        service_name = self._service_table.item(row, 0).text()
        self._show_service_detail(service_name)

    def _show_service_detail(self, service_name: str):
        if self._recon_df is None:
            return

        df = self._recon_df[self._recon_df["service_line"] == service_name]
        self._detail_title.setText(f"{service_name} — Integrity Breakdown")

        # Chart: integrity level distribution
        self._chart.removeAllSeries()
        for ax in self._chart.axes():
            self._chart.removeAxis(ax)

        counts = {"Green": 0, "Amber": 0, "Red": 0}
        for lvl in df["integrity_level"]:
            if lvl in counts:
                counts[lvl] += 1

        colors = {"Green": "#1e8449", "Amber": "#d68910", "Red": "#c0392b"}
        series = QBarSeries()
        for label, count in counts.items():
            bs = QBarSet(label)
            bs.setColor(QColor(colors[label]))
            bs.append(count)
            series.append(bs)

        self._chart.addSeries(series)
        axis_x = QBarCategoryAxis()
        axis_x.append(["Case Distribution"])
        self._chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)
        axis_y = QValueAxis()
        axis_y.setLabelFormat("%d")
        self._chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)
        self._chart.legend().setVisible(True)
        self._chart.setTitle(f"Integrity Level Distribution – {service_name}")

        # Gap frequency
        all_gaps = []
        for gaps_json in df["documentation_gaps"]:
            try:
                all_gaps.extend(json.loads(gaps_json))
            except Exception:
                pass

        self._gap_list.clear()
        if all_gaps:
            gap_counts = pd.Series(all_gaps).value_counts().head(8)
            for gap, cnt in gap_counts.items():
                self._gap_list.addItem(f"[{cnt}×]  {gap}")
        else:
            self._gap_list.addItem("No documentation gaps identified for this service line.")
