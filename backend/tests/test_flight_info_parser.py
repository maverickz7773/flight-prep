from __future__ import annotations

from pathlib import Path
import unittest

from parsers.ofp_parser import parse_ofp


REPO_ROOT = Path(__file__).resolve().parents[2]


class FlightInfoParserRegressionTests(unittest.TestCase):
    def _parse(self, filename: str):
        sample_pdf = REPO_ROOT / filename
        if not sample_pdf.exists():
            self.skipTest(f"Sample PDF missing: {sample_pdf}")
        return parse_ofp(str(sample_pdf))

    def test_qr_8452_preserves_step_climb_levels(self) -> None:
        briefing = self._parse("QR 8452.pdf")

        self.assertEqual(
            briefing.flight_info.cruise_levels,
            ["FL270", "FL290", "FL310", "FL350", "FL370", "FL390"],
        )

    def test_qr_8240_parses_single_cruise_level(self) -> None:
        briefing = self._parse("QR 8240.pdf")

        self.assertEqual(briefing.flight_info.cruise_levels, ["FL310"])

    def test_qr_707_uses_timezone_offset_and_preserves_cruise_levels(self) -> None:
        briefing = self._parse("QR 707.pdf")

        self.assertEqual(briefing.flight_info.arrival_utc_offset, "-4")
        self.assertEqual(
            briefing.flight_info.cruise_levels,
            ["FL320", "FL340", "FL360", "FL380", "FL360", "FL380"],
        )
        self.assertEqual(briefing.weights.ezfw, 205441)

    def test_qr_849_preserves_existing_offsets_cruise_and_zfw(self) -> None:
        briefing = self._parse("QR 849.pdf")

        self.assertEqual(briefing.flight_info.arrival_utc_offset, "+3")
        self.assertEqual(
            briefing.flight_info.cruise_levels,
            ["FL340", "FL360", "FL340", "FL300"],
        )
        self.assertEqual(briefing.weights.ezfw, 217315)

    def test_qr_8974_parses_timezone_cruise_and_real_zfw(self) -> None:
        briefing = self._parse("QR 8974.pdf")

        self.assertEqual(briefing.flight_info.arrival_utc_offset, "+7")
        self.assertEqual(
            briefing.flight_info.cruise_levels,
            ["FL330", "FL350", "FL370", "FL330"],
        )
        self.assertEqual(briefing.weights.ezfw, 149808)


if __name__ == "__main__":
    unittest.main()
