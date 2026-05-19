from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from parsers import notes
from parsers.ofp_parser import parse_ofp


REPO_ROOT = Path(__file__).resolve().parents[2]


class AirportNotesIntegrationTests(unittest.TestCase):
    def test_loader_accepts_section_labels_with_space_before_colon(self) -> None:
        sample_text = """[TEST]
DEP : Departure note
Second line
ARR : Arrival note
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / "Operational Info.txt"
            test_path.write_text(sample_text, encoding="utf-8")

            original_path = notes._DATA_PATH
            original_cache = notes._cache
            original_mtime = notes._cache_mtime_ns
            original_warned = notes._missing_file_warned
            try:
                notes._DATA_PATH = test_path
                notes._cache = None
                notes._cache_mtime_ns = None
                notes._missing_file_warned = False
                parsed = notes.get_airport_notes("TEST")
            finally:
                notes._DATA_PATH = original_path
                notes._cache = original_cache
                notes._cache_mtime_ns = original_mtime
                notes._missing_file_warned = original_warned

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["departure"], "Departure note\nSecond line")
        self.assertEqual(parsed["arrival"], "Arrival note")

    def test_qr_8945_contains_departure_and_arrival_notes(self) -> None:
        sample_pdf = REPO_ROOT / "QR 8945.pdf"
        if not sample_pdf.exists():
            self.skipTest(f"Sample PDF missing: {sample_pdf}")

        briefing = parse_ofp(str(sample_pdf))

        self.assertIsNotNone(briefing.airport_notes)
        self.assertTrue(briefing.airport_notes.departure)
        self.assertTrue(briefing.airport_notes.arrival)

    def test_qr_8240_has_no_airport_notes(self) -> None:
        sample_pdf = REPO_ROOT / "QR 8240.pdf"
        if not sample_pdf.exists():
            self.skipTest(f"Sample PDF missing: {sample_pdf}")

        briefing = parse_ofp(str(sample_pdf))

        self.assertIsNone(briefing.airport_notes)

    def test_qr_8974_picks_up_vdti_arrival_notes(self) -> None:
        sample_pdf = REPO_ROOT / "QR 8974.pdf"
        if not sample_pdf.exists():
            self.skipTest(f"Sample PDF missing: {sample_pdf}")

        briefing = parse_ofp(str(sample_pdf))

        self.assertIsNotNone(briefing.airport_notes)
        self.assertTrue(briefing.airport_notes.departure)
        self.assertTrue(briefing.airport_notes.arrival)


if __name__ == "__main__":
    unittest.main()
