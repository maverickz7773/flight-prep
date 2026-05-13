from __future__ import annotations

from pathlib import Path
import unittest

from parsers.enroute_info import get_enroute_info
from parsers.ofp_parser import parse_ofp


REPO_ROOT = Path(__file__).resolve().parents[2]


class EnrouteInfoIntegrationTests(unittest.TestCase):
    def _parse(self, filename: str):
        sample_pdf = REPO_ROOT / filename
        if not sample_pdf.exists():
            self.skipTest(f"Sample PDF missing: {sample_pdf}")
        return parse_ofp(str(sample_pdf))

    def test_known_fir_blocks_load_from_text_file(self) -> None:
        self.assertIn("Restricted Airspace", get_enroute_info("OEJD") or "")
        self.assertIn("Contingency Communication", get_enroute_info("OJAC") or "")
        self.assertIn("Airspace Status", get_enroute_info("OSTT") or "")
        self.assertIn("Navigation Performance", get_enroute_info("LTAA") or "")

    def test_unknown_fir_returns_none(self) -> None:
        self.assertIsNone(get_enroute_info("KZSE"))

    def test_qr_239_contains_only_firs_with_available_notes(self) -> None:
        briefing = self._parse("QR 239.pdf")

        self.assertEqual(
            [(item.fir_name, item.fir_icao) for item in briefing.route.enroute_info],
            [
                ("BAHRAIN", "OBBB"),
                ("JEDDAH", "OEJD"),
                ("AMMAN", "OJAC"),
                ("DAMASCUS", "OSTT"),
                ("ANKARA", "LTAA"),
            ],
        )

    def test_qr_719_contains_partial_fir_note_coverage(self) -> None:
        briefing = self._parse("QR 719.pdf")

        self.assertEqual(
            [item.fir_icao for item in briefing.route.enroute_info],
            ["OEJD", "OJAC", "OSTT", "LTAA"],
        )


if __name__ == "__main__":
    unittest.main()
