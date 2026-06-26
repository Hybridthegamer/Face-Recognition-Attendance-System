"""
Report Generator — implements GenerateReport algorithm (Chapter 3, Section 3.8.3)

ALGORITHM: GenerateReport(course_code, threshold_pct)
  1. total_sessions ← COUNT(*) FROM Sessions WHERE course_code
  2. students       ← DISTINCT user_id FROM AttendanceRecords JOIN Sessions
  3. FOR EACH student:
       attended ← COUNT(*) WHERE user_id AND course
       pct      ← (attended / total_sessions) * 100
       status   ← 'PASS' IF pct >= threshold_pct ELSE 'FAIL'
  4. Sort by percentage descending
  5. Render to GUI; provide CSV export option
"""

import csv
import os
from datetime import datetime

from src.config import REPORTS_DIR, DEFAULT_THRESHOLD_PCT


class ReportGenerator:
    def __init__(self, db_manager):
        self.db = db_manager
        os.makedirs(REPORTS_DIR, exist_ok=True)

    def generate(self, course_code: str, threshold_pct: float = DEFAULT_THRESHOLD_PCT):
        """Returns (rows, total_sessions)."""
        return self.db.get_report_data(course_code, threshold_pct)

    def export_csv(self, course_code: str, threshold_pct: float = DEFAULT_THRESHOLD_PCT) -> str:
        """Export report to CSV and return the file path."""
        rows, total = self.generate(course_code, threshold_pct)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{course_code}_{ts}.csv"
        filepath = os.path.join(REPORTS_DIR, filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Name', 'Institution ID', 'Department', 'Programme',
                'Sessions Attended', f'Total Sessions ({total})',
                'Percentage (%)', f'Status (threshold={threshold_pct}%)'
            ])
            for r in rows:
                writer.writerow([
                    r['name'], r['institution_id'], r['department'], r['programme'],
                    r['attended'], r['total_sessions'],
                    f"{r['percentage']:.1f}", r['status'],
                ])
        return filepath
