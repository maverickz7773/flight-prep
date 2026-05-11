from __future__ import annotations

from pathlib import Path
import unittest

from parsers.ofp_parser import parse_ofp


REPO_ROOT = Path(__file__).resolve().parents[2]


class ETOPSParserRegressionTests(unittest.TestCase):
    def test_qr_719_parses_exit1_with_continuation_line(self) -> None:
        sample_pdf = REPO_ROOT / "QR 719.pdf"
        if not sample_pdf.exists():
            self.skipTest(f"Sample PDF missing: {sample_pdf}")

        briefing = parse_ofp(str(sample_pdf))
        sectors = briefing.etops.sectors if briefing.etops else []

        self.assertEqual(len(sectors), 2)
        self.assertEqual(sectors[0].entry_icao, "ENBR")
        self.assertEqual(sectors[0].exit_icao, "BIKF")
        self.assertEqual(sectors[1].entry_icao, "BIKF")
        self.assertEqual(sectors[1].exit_icao, "CYEG")

    def test_qr_8452_preserves_existing_sector_parsing(self) -> None:
        sample_pdf = REPO_ROOT / "QR 8452.pdf"
        if not sample_pdf.exists():
            self.skipTest(f"Sample PDF missing: {sample_pdf}")

        briefing = parse_ofp(str(sample_pdf))
        sectors = briefing.etops.sectors if briefing.etops else []

        self.assertEqual(len(sectors), 2)
        self.assertEqual(sectors[0].entry_icao, "OOSA")
        self.assertEqual(sectors[0].exit_icao, "VOCI")
        self.assertEqual(sectors[1].entry_icao, "VCBI")
        self.assertEqual(sectors[1].exit_icao, "YPAD")


if __name__ == "__main__":
    unittest.main()
