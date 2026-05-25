from __future__ import annotations

from pathlib import Path
import unittest

from parsers.ofp_parser import parse_ofp


REPO_ROOT = Path(__file__).resolve().parents[2]


class FuelParserRegressionTests(unittest.TestCase):
    def _parse(self, filename: str):
        sample_pdf = REPO_ROOT / filename
        if not sample_pdf.exists():
            self.skipTest(f"Sample PDF missing: {sample_pdf}")
        return parse_ofp(str(sample_pdf))

    def test_qr_1150_parses_minimum_contingency_fuel(self) -> None:
        briefing = self._parse("QR 1150.pdf")

        self.assertEqual(briefing.fuel.contingency, 590)
        self.assertEqual(briefing.fuel.contingency_type, "MINM")
        self.assertEqual(briefing.fuel.contingency_time, "0005")

    def test_qr_8974_preserves_percent_contingency_fuel(self) -> None:
        briefing = self._parse("QR 8974.pdf")

        self.assertEqual(briefing.fuel.contingency, 1185)
        self.assertEqual(briefing.fuel.contingency_type, "3P/C VTBS")
        self.assertEqual(briefing.fuel.contingency_time, "0010")


if __name__ == "__main__":
    unittest.main()
