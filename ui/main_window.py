"""
ui/main_window.py - Main application window
"""
import os
import sys
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTabWidget, QPushButton, QFileDialog, QMessageBox, QFrame,
    QProgressDialog, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ui.overview_tab import OverviewTab
from ui.service_tab import ServiceTab
from ui.case_tab import CaseTab

NAVY = "#1a2942"
LIGHT_NAVY = "#2a4480"
ACCENT = "#3a6bc4"
BG = "#f4f7fb"
WHITE = "#ffffff"


class ProcessingWorker(QObject):
    """Background worker for data ingestion and processing."""
    finished = pyqtSignal(int, str)
    error = pyqtSignal(str)

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            from core.ingestion import load_csv
            from core.scoring import process_dataset
            dataset_id, dataset_name = load_csv(self.file_path)
            process_dataset(dataset_id)
            self.finished.emit(dataset_id, dataset_name)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hospital Documentation & Funding Integrity Dashboard")
        self.setMinimumSize(1200, 780)
        self._dataset_id = None
        self._dataset_name = "No Dataset Loaded"
        self._thread = None

        self._apply_global_style()
        self._build_ui()

    def _apply_global_style(self):
        self.setStyleSheet(f"""
            QMainWindow {{
                background: {BG};
            }}
            QTabWidget::pane {{
                border: 1px solid #dde4ef;
                background: {BG};
                border-radius: 4px;
            }}
            QTabBar::tab {{
                background: #dde4ef;
                color: {NAVY};
                padding: 10px 28px;
                font-family: 'Segoe UI';
                font-size: 10px;
                font-weight: bold;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
                min-width: 160px;
            }}
            QTabBar::tab:selected {{
                background: {NAVY};
                color: white;
            }}
            QTabBar::tab:hover:!selected {{
                background: #c5cfe8;
            }}
            QScrollBar:vertical {{
                background: #f0f3f9;
                width: 8px;
            }}
            QScrollBar::handle:vertical {{
                background: #b0bcd6;
                border-radius: 4px;
            }}
        """)

    def _build_ui(self):
        central = QWidget()
        central.setStyleSheet(f"background: {BG};")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header bar ────────────────────────────────────────────────────────
        header = QFrame()
        header.setFixedHeight(72)
        header.setStyleSheet(f"background: {NAVY}; border-bottom: 3px solid {ACCENT};")

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(28, 0, 28, 0)
        header_layout.setSpacing(16)

        # Logo mark
        logo_mark = QLabel("⬡")
        logo_mark.setFont(QFont("Segoe UI", 20))
        logo_mark.setStyleSheet("color: #5b8dee; border: none;")
        header_layout.addWidget(logo_mark)

        # Title group
        title_group = QVBoxLayout()
        title_group.setSpacing(1)

        title = QLabel("DOCUMENTATION & FUNDING INTEGRITY DASHBOARD")
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title.setStyleSheet("color: white; letter-spacing: 2px; border: none;")

        subtitle = QLabel("Hospital Decision Intelligence Platform")
        subtitle.setFont(QFont("Segoe UI", 8))
        subtitle.setStyleSheet("color: #8fa8d4; border: none;")

        title_group.addWidget(title)
        title_group.addWidget(subtitle)
        header_layout.addLayout(title_group)
        header_layout.addStretch()

        # Dataset info
        info_group = QVBoxLayout()
        info_group.setSpacing(2)
        info_group.setAlignment(Qt.AlignmentFlag.AlignRight)

        self._dataset_label = QLabel("No Dataset Loaded")
        self._dataset_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._dataset_label.setStyleSheet("color: #8fa8d4; border: none;")
        self._dataset_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        self._date_label = QLabel(datetime.now().strftime("%B %d, %Y"))
        self._date_label.setFont(QFont("Segoe UI", 8))
        self._date_label.setStyleSheet("color: #6b85b0; border: none;")
        self._date_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        info_group.addWidget(self._dataset_label)
        info_group.addWidget(self._date_label)
        header_layout.addLayout(info_group)

        # Load button
        self._load_btn = QPushButton("  Load Dataset  ")
        self._load_btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._load_btn.setFixedHeight(36)
        self._load_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: white;
                border-radius: 4px;
                padding: 0 18px;
                border: none;
            }}
            QPushButton:hover {{ background: #2a5bbc; }}
            QPushButton:pressed {{ background: #1e4899; }}
        """)
        self._load_btn.clicked.connect(self._load_dataset)
        header_layout.addWidget(self._load_btn)

        root.addWidget(header)

        # ── Tab widget ────────────────────────────────────────────────────────
        content = QWidget()
        content.setStyleSheet(f"background: {BG};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 16)

        self._tabs = QTabWidget()

        self._overview_tab = OverviewTab()
        self._service_tab = ServiceTab()
        self._case_tab = CaseTab()
        self._case_tab.request_clear.connect(self._clear_dataset)

        self._tabs.addTab(self._overview_tab, "  Executive Overview  ")
        self._tabs.addTab(self._service_tab, "  Service Line Insights  ")
        self._tabs.addTab(self._case_tab, "  Case Review & Export  ")

        content_layout.addWidget(self._tabs)
        root.addWidget(content)

        # ── Status bar ────────────────────────────────────────────────────────
        status = QFrame()
        status.setFixedHeight(28)
        status.setStyleSheet(f"background: {NAVY}; border-top: 1px solid {LIGHT_NAVY};")
        status_layout = QHBoxLayout(status)
        status_layout.setContentsMargins(20, 0, 20, 0)

        self._status_label = QLabel("Ready — Load a CSV dataset to begin analysis")
        self._status_label.setFont(QFont("Segoe UI", 8))
        self._status_label.setStyleSheet("color: #6b85b0; border: none;")
        status_layout.addWidget(self._status_label)
        status_layout.addStretch()

        version = QLabel("v1.0  |  Offline Mode  |  Hospital Intelligence Platform")
        version.setFont(QFont("Segoe UI", 8))
        version.setStyleSheet("color: #4a6080; border: none;")
        status_layout.addWidget(version)

        root.addWidget(status)

    def _load_dataset(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Patient Dataset", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return

        self._load_btn.setEnabled(False)
        self._status_label.setText("Processing dataset… please wait.")

        self._thread = QThread()
        self._worker = ProcessingWorker(path)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_processing_done)
        self._worker.error.connect(self._on_processing_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.start()

    def _on_processing_done(self, dataset_id: int, dataset_name: str):
        self._dataset_id = dataset_id
        self._dataset_name = dataset_name
        self._dataset_label.setText(f"Dataset: {dataset_name}")
        self._load_btn.setEnabled(True)
        self._status_label.setText(f"Analysis complete — {dataset_name}")
        self._refresh_all_tabs()

    def _on_processing_error(self, error: str):
        self._load_btn.setEnabled(True)
        self._status_label.setText("Error during processing.")
        QMessageBox.critical(self, "Processing Error", f"Failed to load dataset:\n\n{error}")

    def _refresh_all_tabs(self):
        if not self._dataset_id:
            return

        from core.scoring import (
            get_executive_summary, get_service_line_summary,
            get_top_documentation_gaps, get_reconciliation_df
        )
        from core.ingestion import get_raw_records

        summary = get_executive_summary(self._dataset_id)
        service_df = get_service_line_summary(self._dataset_id)
        gaps_df = get_top_documentation_gaps(self._dataset_id)
        recon_df = get_reconciliation_df(self._dataset_id)
        raw_df = get_raw_records(self._dataset_id)
        raw_records = raw_df.to_dict("records") if not raw_df.empty else []

        self._overview_tab.refresh(summary, service_df, gaps_df)
        self._service_tab.refresh(service_df, recon_df)
        self._case_tab.refresh(raw_records, recon_df, self._dataset_id, self._dataset_name)

    def _clear_dataset(self):
        if not self._dataset_id:
            return
        from database import clear_dataset
        clear_dataset(self._dataset_id)
        self._dataset_id = None
        self._dataset_name = "No Dataset Loaded"
        self._dataset_label.setText("No Dataset Loaded")
        self._status_label.setText("Dataset cleared — Load a new CSV to continue")

        self._overview_tab.refresh({}, None, None)
        self._service_tab.refresh(None, None)
        self._case_tab.refresh([], None, None)
