"""
main.py - Application entry point
Hospital Documentation & Funding Integrity Dashboard

Usage:
    python main.py
"""
import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

from database import initialize_database
from ui.main_window import MainWindow


def main():
    # Initialize local SQLite database
    initialize_database()

    app = QApplication(sys.argv)
    app.setApplicationName("Hospital Documentation & Funding Integrity Dashboard")
    app.setOrganizationName("Hospital Intelligence Platform")

    # Set application-wide default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
