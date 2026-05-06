from __future__ import annotations

from pathlib import Path
import unittest

from parsers.ofp_parser import parse_ofp


REPO_ROOT = Path(__file__).resolve().parents[2]


class AirportNotesIntegrationTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
