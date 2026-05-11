from __future__ import annotations

from pathlib import Path
import unittest

from parsers.ofp_parser import parse_ofp


REPO_ROOT = Path(__file__).resolve().parents[2]


class SidStarParserRegressionTests(unittest.TestCase):
    def _parse(self, filename: str):
        sample_pdf = REPO_ROOT / filename
        if not sample_pdf.exists():
            self.skipTest(f"Sample PDF missing: {sample_pdf}")
        return parse_ofp(str(sample_pdf))

    def test_qr_849_parses_standard_sid_and_star(self) -> None:
        briefing = self._parse("QR 849.pdf")

        self.assertEqual(briefing.flight_info.sid, "PUGER1E")
        self.assertEqual(briefing.takeoff.sid, "PUGER1E")
        self.assertEqual(briefing.flight_info.star, "TOVOX2L")
        self.assertEqual(briefing.arrival.star, "TOVOX2L")

    def test_qr_8240_parses_letter_ending_sid_and_star(self) -> None:
        briefing = self._parse("QR 8240.pdf")

        self.assertEqual(briefing.flight_info.sid, "LNO8E")
        self.assertEqual(briefing.takeoff.sid, "LNO8E")
        self.assertEqual(briefing.flight_info.star, "RIXUV3E")
        self.assertEqual(briefing.arrival.star, "RIXUV3E")

    def test_qr_719_parses_no_sid_and_numeric_ending_star(self) -> None:
        briefing = self._parse("QR 719.pdf")

        self.assertIsNone(briefing.flight_info.sid)
        self.assertIsNone(briefing.takeoff.sid)
        self.assertEqual(briefing.flight_info.star, "GLASR3")
        self.assertEqual(briefing.arrival.star, "GLASR3")

    def test_qr_8945_parses_numeric_ending_sid(self) -> None:
        briefing = self._parse("QR 8945.pdf")

        self.assertEqual(briefing.flight_info.sid, "TOMUD3")
        self.assertEqual(briefing.takeoff.sid, "TOMUD3")
        self.assertEqual(briefing.flight_info.star, "LAEEB1P")
        self.assertEqual(briefing.arrival.star, "LAEEB1P")


if __name__ == "__main__":
    unittest.main()
