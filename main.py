"""
Face Recognition Attendance System
Entry point — initialises all subsystems and starts the Tkinter GUI.

Usage:
    python main.py
"""

import sys
import os

# Ensure the project root is on the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gui.app import FaceAttendanceApp

if __name__ == "__main__":
    app = FaceAttendanceApp()
    app.run()
