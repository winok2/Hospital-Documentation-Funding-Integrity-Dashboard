"""
ui/overview_tab.py - Executive Overview Tab
"""
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QSizePolicy, QHeaderView, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from PyQt6.QtCore import Qt


NAVY = "#1a2942"
LIGHT_NAVY = "#2a4480"
ACCENT = "#3a6bc4"
BG = "#f4f7fb"
WHITE = "#ffffff"
RED_CLR = "#c0392b"
AMBER_CLR = "#d68910"
GREEN_CLR = "#1e8449"


class KPICard(QFrame):
    """A single KPI metric card."""

    def __init__(self, label: str, value: str = "—", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            KPICard {{
                background: {WHITE};
                border: 1px solid #dde4ef;
                border-left: 5px solid {ACCENT};
                border-radius: 4px;
            }}
        """)
        self.setMinimumWidth(160)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(100)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(4)

        self._value_label = QLabel(value)
        self._value_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self._value_label.setStyleSheet(f"color: {NAVY}; border: none;")

        self._text_label = QLabel(label.upper())
        self._text_label.setFont(QFont("Segoe UI", 8))
        self._text_label.setStyleSheet("color: #6b7a99; letter-spacing: 1px; border: none;")
        self._text_label.setWordWrap(True)

        layout.addWidget(self._value_label)
        layout.addWidget(self._text_label)

    def update_value(self, value: str, color: str = None):
        self._value_label.setText(value)
        if color:
            self._value_label.setStyleSheet(f"color: {color}; border: none;")


class OverviewTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(20)

        # ── KPI Row ──────────────────────────────────────────────────────────
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(14)

        self.kpi_total     = KPICard("Records Analyzed")
        self.kpi_integrity = KPICard("Documentation Integrity Rate")
        self.kpi_mismatch  = KPICard("Mismatch Exposure Rate")
        self.kpi_funding   = KPICard("Estimated Funding Sensitivity")
        self.kpi_risk      = KPICard("Highest Risk Service Line")

        for card in [self.kpi_total, self.kpi_integrity, self.kpi_mismatch,
                     self.kpi_funding, self.kpi_risk]:
            kpi_row.addWidget(card)

        root.addLayout(kpi_row)

        # ── Lower row: chart + gaps table ────────────────────────────────────
        lower = QHBoxLayout()
        lower.setSpacing(18)

        # Chart
        chart_frame = QFrame()
        chart_frame.setStyleSheet(f"background: {WHITE}; border: 1px solid #dde4ef; border-radius: 4px;")
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setContentsMargins(14, 12, 14, 12)

        chart_title = QLabel("Mismatch Rate by Service Line")
        chart_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        chart_title.setStyleSheet(f"color: {NAVY};")
        chart_layout.addWidget(chart_title)

        self._chart = QChart()
        self._chart.setBackgroundBrush(QColor(WHITE))
        self._chart.setMargins(self._chart.margins().__class__(4, 4, 4, 4))
        self._chart.legend().setVisible(False)

        self._chart_view = QChartView(self._chart)
        self._chart_view.setMinimumHeight(260)
        self._chart_view.setRenderHint(self._chart_view.renderHints().__class__.Antialiasing)
        chart_layout.addWidget(self._chart_view)

        lower.addWidget(chart_frame, 3)

        # Top gaps table
        gaps_frame = QFrame()
        gaps_frame.setStyleSheet(f"background: {WHITE}; border: 1px solid #dde4ef; border-radius: 4px;")
        gaps_layout = QVBoxLayout(gaps_frame)
        gaps_layout.setContentsMargins(14, 12, 14, 12)

        gaps_title = QLabel("Top Recurring Documentation Gaps")
        gaps_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        gaps_title.setStyleSheet(f"color: {NAVY};")
        gaps_layout.addWidget(gaps_title)

        self._gaps_table = QTableWidget()
        self._gaps_table.setColumnCount(2)
        self._gaps_table.setHorizontalHeaderLabels(["Documentation Gap", "Frequency"])
        self._gaps_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._gaps_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._gaps_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._gaps_table.setAlternatingRowColors(True)
        self._gaps_table.verticalHeader().setVisible(False)
        self._gaps_table.setStyleSheet("""
            QTableWidget { border: none; font-size: 10px; }
            QHeaderView::section { background: #1a2942; color: white; padding: 6px; font-size: 10px; }
            QTableWidget::item:alternate { background: #f4f7fb; }
        """)
        gaps_layout.addWidget(self._gaps_table)

        lower.addWidget(gaps_frame, 2)
        root.addLayout(lower)

    def refresh(self, summary: dict, service_df, gaps_df):
        """Update all KPIs, chart, and gaps table with fresh data."""
        if not summary:
            return

        self.kpi_total.update_value(str(summary.get("total_records", "—")))
        self.kpi_integrity.update_value(f"{summary.get('integrity_rate', '—')}%",
                                         GREEN_CLR if summary.get("integrity_rate", 0) >= 70 else AMBER_CLR)
        self.kpi_mismatch.update_value(f"{summary.get('mismatch_rate', '—')}%",
                                        RED_CLR if summary.get("mismatch_rate", 0) >= 20 else AMBER_CLR)
        low = summary.get("estimated_low_variance", 0)
        high = summary.get("estimated_high_variance", 0)
        self.kpi_funding.update_value(f"{low}–{high}%")
        self.kpi_risk.update_value(str(summary.get("highest_risk_service_line", "—")),
                                    RED_CLR)

        # Update chart
        self._update_chart(service_df)

        # Update gaps table
        self._gaps_table.setRowCount(0)
        if gaps_df is not None and not gaps_df.empty:
            for _, row in gaps_df.iterrows():
                r = self._gaps_table.rowCount()
                self._gaps_table.insertRow(r)
                self._gaps_table.setItem(r, 0, QTableWidgetItem(str(row.iloc[0])))
                freq_item = QTableWidgetItem(str(row.iloc[1]))
                freq_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._gaps_table.setItem(r, 1, freq_item)

    def _update_chart(self, service_df):
        self._chart.removeAllSeries()
        for ax in self._chart.axes():
            self._chart.removeAxis(ax)

        if service_df is None or service_df.empty:
            return

        bar_set = QBarSet("Mismatch Rate")
        bar_set.setColor(QColor(ACCENT))

        categories = []
        for _, row in service_df.iterrows():
            bar_set.append(float(row["Mismatch Rate (%)"]))
            # Truncate long names
            name = str(row["Service Line"])
            categories.append(name[:18] + "…" if len(name) > 18 else name)

        series = QBarSeries()
        series.append(bar_set)
        self._chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        axis_x.setLabelsFont(QFont("Segoe UI", 8))
        self._chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, 100)
        axis_y.setLabelFormat("%.0f%%")
        axis_y.setLabelsFont(QFont("Segoe UI", 8))
        self._chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        self._chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
