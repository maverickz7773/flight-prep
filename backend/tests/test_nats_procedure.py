from __future__ import annotations

from pathlib import Path
import unittest

from parsers.nats import get_nats_sections
from parsers.ofp_parser import parse_ofp


REPO_ROOT = Path(__file__).resolve().parents[2]


class NATSProcedureIntegrationTests(unittest.TestCase):
    def _parse(self, filename: str):
        sample_pdf = REPO_ROOT / filename
        if not sample_pdf.exists():
            self.skipTest(f"Sample PDF missing: {sample_pdf}")
        return parse_ofp(str(sample_pdf))

    def test_nats_sections_load_from_text_file(self) -> None:
        sections = get_nats_sections()

        self.assertIn("NATS Overview", sections)
        self.assertIn("NATS Preflight and Planning", sections)
        self.assertIn("NATS Enroute", sections)
        self.assertIn("NATS Exit", sections)

    def test_qr_707_triggers_nats_and_builds_overview(self) -> None:
        briefing = self._parse("QR 707.pdf")

        self.assertIsNotNone(briefing.nats_procedure)
        assert briefing.nats_procedure is not None
        self.assertEqual(briefing.nats_procedure.trigger_firs, ["EGGX", "CZQX"])
        self.assertEqual(briefing.nats_procedure.overview.tmi, "137")
        self.assertEqual(
            briefing.nats_procedure.overview.route,
            "GOMUP DCT N5900W02000 DCT N5830W03000 DCT N5800W04000 DCT N5630W05000 DCT IRLOK",
        )
        self.assertEqual(briefing.nats_procedure.overview.entry_point, "GOMUP")
        self.assertEqual(briefing.nats_procedure.overview.entry_fir, "EGGX")
        self.assertEqual(briefing.nats_procedure.overview.exit_point, "IRLOK")
        self.assertEqual(briefing.nats_procedure.overview.exit_fir, "CZQX")
        self.assertIn("Shanwick EGGX : 90 - 30 mins", briefing.nats_procedure.enroute_fir_callouts)
        self.assertIn("Gander CZQX : 90 - 60 mins", briefing.nats_procedure.enroute_fir_callouts)

    def test_qr_719_triggers_nats_for_north_atlantic_firs(self) -> None:
        briefing = self._parse("QR 719.pdf")

        self.assertIsNotNone(briefing.nats_procedure)
        assert briefing.nats_procedure is not None
        self.assertEqual(briefing.nats_procedure.trigger_firs, ["BIRD", "BGGL"])
        self.assertEqual(
            briefing.nats_procedure.overview.route,
            "ISVIG DCT N6700W01000 DCT N7000W02000 DCT N7300W04000 DCT N7300W06000 DCT MEDPA",
        )
        self.assertEqual(briefing.nats_procedure.overview.entry_point, "ISVIG")
        self.assertEqual(briefing.nats_procedure.overview.exit_point, "MEDPA")
        self.assertTrue(any("BIRD" in line for line in briefing.nats_procedure.enroute_fir_callouts))

    def test_qr_239_does_not_trigger_nats(self) -> None:
        briefing = self._parse("QR 239.pdf")
        self.assertIsNone(briefing.nats_procedure)

    def test_qr_8452_does_not_trigger_nats(self) -> None:
        briefing = self._parse("QR 8452.pdf")
        self.assertIsNone(briefing.nats_procedure)


if __name__ == "__main__":
    unittest.main()
