from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

import main
from models.briefing import AirportFeedbackCreate, FIRFeedbackCreate
from services import airport_feedback


class AirportFeedbackServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self._old_enabled = os.environ.get("AIRPORT_FEEDBACK_ENABLED")
        self._old_db_path = os.environ.get("AIRPORT_FEEDBACK_DB_PATH")
        self._tempdir = tempfile.TemporaryDirectory()
        os.environ["AIRPORT_FEEDBACK_ENABLED"] = "1"
        os.environ["AIRPORT_FEEDBACK_DB_PATH"] = str(
            Path(self._tempdir.name) / "airport_feedback.sqlite3"
        )

    def tearDown(self) -> None:
        if self._old_enabled is None:
            os.environ.pop("AIRPORT_FEEDBACK_ENABLED", None)
        else:
            os.environ["AIRPORT_FEEDBACK_ENABLED"] = self._old_enabled

        if self._old_db_path is None:
            os.environ.pop("AIRPORT_FEEDBACK_DB_PATH", None)
        else:
            os.environ["AIRPORT_FEEDBACK_DB_PATH"] = self._old_db_path

        self._tempdir.cleanup()

    def test_create_list_and_delete_feedback_entries(self) -> None:
        older_departure_entry = airport_feedback.create_airport_feedback(
            AirportFeedbackCreate(
                section="departure",
                airport_icao="OTHH",
                flight_date="01Jun26",
                from_icao="OTHH",
                to_icao="OLBA",
                route_text="OTHH → OLBA",
                sid="TULUB2A",
                runway="34L",
                comments="Older departure feedback entry",
            )
        )
        newer_departure_entry = airport_feedback.create_airport_feedback(
            AirportFeedbackCreate(
                section="departure",
                airport_icao="OTHH",
                flight_date="02Jun26",
                from_icao="OTHH",
                to_icao="EGLL",
                route_text="OTHH → EGLL",
                sid="NARMI1J",
                runway="16L",
                comments="Newer departure feedback entry from a different route",
            )
        )
        older_arrival_entry = airport_feedback.create_airport_feedback(
            AirportFeedbackCreate(
                section="arrival",
                airport_icao="OLBA",
                flight_date="01Jun26",
                from_icao="OTHH",
                to_icao="OLBA",
                comments="Older arrival feedback entry",
            )
        )
        newer_arrival_entry = airport_feedback.create_airport_feedback(
            AirportFeedbackCreate(
                section="arrival",
                airport_icao="OLBA",
                flight_date="03Jun26",
                from_icao="WMKK",
                to_icao="OLBA",
                comments="Newer arrival feedback entry from a different route",
            )
        )

        grouped = airport_feedback.get_airport_feedback("OTHH", "OLBA")

        self.assertIsNotNone(grouped)
        self.assertEqual(
            [entry.id for entry in grouped.departure],
            [newer_departure_entry.id, older_departure_entry.id],
        )
        self.assertEqual(
            [entry.id for entry in grouped.arrival],
            [newer_arrival_entry.id, older_arrival_entry.id],
        )
        self.assertEqual(grouped.departure[0].route_text, "OTHH → EGLL")
        self.assertEqual(grouped.departure[0].runway, "16L")

        deleted = airport_feedback.delete_airport_feedback(newer_departure_entry.id)
        self.assertTrue(deleted)

        grouped_after_delete = airport_feedback.get_airport_feedback("OTHH", "OLBA")

        self.assertIsNotNone(grouped_after_delete)
        self.assertEqual([entry.id for entry in grouped_after_delete.departure], [older_departure_entry.id])
        self.assertEqual(
            [entry.id for entry in grouped_after_delete.arrival],
            [newer_arrival_entry.id, older_arrival_entry.id],
        )

    def test_create_list_and_delete_fir_feedback_entries(self) -> None:
        older_fir_entry = airport_feedback.create_fir_feedback(
            FIRFeedbackCreate(
                fir_icao="WMFC",
                fir_name="KUALA LUMPUR FIR",
                flight_date="10May26",
                route_text="WMKK DCT IGARI L894 OTHH",
                from_icao="WMKK",
                to_icao="OTHH",
                comments="Older FIR feedback entry",
            )
        )
        newer_fir_entry = airport_feedback.create_fir_feedback(
            FIRFeedbackCreate(
                fir_icao="WMFC",
                fir_name="KUALA LUMPUR FIR",
                flight_date="31May26",
                route_text="WMKK DCT PULIP L894 OTHH",
                from_icao="WMKK",
                to_icao="OTHH",
                comments="Newer FIR feedback entry from a different OFP",
            )
        )

        grouped = airport_feedback.get_fir_feedback(["WMFC", "OBBB"])

        self.assertIsNotNone(grouped)
        self.assertEqual(
            [entry.id for entry in grouped["WMFC"]],
            [newer_fir_entry.id, older_fir_entry.id],
        )
        self.assertEqual(grouped["WMFC"][0].route_text, "WMKK DCT PULIP L894 OTHH")
        self.assertEqual(grouped["OBBB"], [])

        deleted = airport_feedback.delete_fir_feedback(newer_fir_entry.id)
        self.assertTrue(deleted)

        grouped_after_delete = airport_feedback.get_fir_feedback(["WMFC"])

        self.assertIsNotNone(grouped_after_delete)
        self.assertEqual([entry.id for entry in grouped_after_delete["WMFC"]], [older_fir_entry.id])


class AirportFeedbackApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._old_enabled = os.environ.get("AIRPORT_FEEDBACK_ENABLED")
        self._old_db_path = os.environ.get("AIRPORT_FEEDBACK_DB_PATH")
        self._tempdir = tempfile.TemporaryDirectory()
        self._db_path = Path(self._tempdir.name) / "airport_feedback.sqlite3"
        os.environ["AIRPORT_FEEDBACK_ENABLED"] = "1"
        os.environ["AIRPORT_FEEDBACK_DB_PATH"] = str(self._db_path)
        self.client = TestClient(main.app)

    def tearDown(self) -> None:
        if self._old_enabled is None:
            os.environ.pop("AIRPORT_FEEDBACK_ENABLED", None)
        else:
            os.environ["AIRPORT_FEEDBACK_ENABLED"] = self._old_enabled

        if self._old_db_path is None:
            os.environ.pop("AIRPORT_FEEDBACK_DB_PATH", None)
        else:
            os.environ["AIRPORT_FEEDBACK_DB_PATH"] = self._old_db_path

        self._tempdir.cleanup()

    def test_post_get_and_delete_feedback(self) -> None:
        departure_create_res = self.client.post(
            "/api/airport-feedback",
            json={
                "section": "departure",
                "airport_icao": "OTHH",
                "flight_date": "01Jun26",
                "route_text": "OTHH → EGLL",
                "from_icao": "OTHH",
                "to_icao": "EGLL",
                "sid": "TULUB2A",
                "star": None,
                "runway": "34L",
                "approach_runway": None,
                "comments": "Departure feedback should be grouped by OTHH only.",
            },
        )
        self.assertEqual(departure_create_res.status_code, 200)
        departure_created = departure_create_res.json()
        self.assertEqual(departure_created["route_text"], "OTHH → EGLL")
        self.assertEqual(departure_created["runway"], "34L")

        arrival_create_res = self.client.post(
            "/api/airport-feedback",
            json={
                "section": "arrival",
                "airport_icao": "OLBA",
                "flight_date": "01Jun26",
                "from_icao": "OTHH",
                "to_icao": "OLBA",
                "route_text": None,
                "sid": None,
                "star": "CHEKA.1N",
                "runway": None,
                "approach_runway": "03",
                "comments": "Watch descent coordination with Damascus.",
            },
        )
        self.assertEqual(arrival_create_res.status_code, 200)
        arrival_created = arrival_create_res.json()
        self.assertEqual(arrival_created["section"], "arrival")

        get_res = self.client.get(
            "/api/airport-feedback",
            params={"departure": "OTHH", "arrival": "OLBA"},
        )
        self.assertEqual(get_res.status_code, 200)
        grouped = get_res.json()
        self.assertEqual(len(grouped["departure"]), 1)
        self.assertEqual(grouped["departure"][0]["airport_icao"], "OTHH")
        self.assertEqual(grouped["departure"][0]["route_text"], "OTHH → EGLL")
        self.assertEqual(len(grouped["arrival"]), 1)
        self.assertEqual(grouped["arrival"][0]["star"], "CHEKA.1N")
        self.assertEqual(grouped["arrival"][0]["comments"], "Watch descent coordination with Damascus.")

        delete_res = self.client.delete(f"/api/airport-feedback/{arrival_created['id']}")
        self.assertEqual(delete_res.status_code, 200)
        self.assertEqual(delete_res.json(), {"deleted": True})

        get_after_delete = self.client.get(
            "/api/airport-feedback",
            params={"departure": "OTHH", "arrival": "OLBA"},
        )
        self.assertEqual(get_after_delete.status_code, 200)
        self.assertEqual(len(get_after_delete.json()["departure"]), 1)
        self.assertEqual(get_after_delete.json()["arrival"], [])

    def test_post_get_and_delete_fir_feedback(self) -> None:
        create_res = self.client.post(
            "/api/fir-feedback",
            json={
                "fir_icao": "WMFC",
                "fir_name": "KUALA LUMPUR FIR",
                "flight_date": "10May26",
                "route_text": "WMKK DCT IGARI L894 OTHH",
                "from_icao": "WMKK",
                "to_icao": "OTHH",
                "comments": "Keep an eye on CPDLC logon timing.",
            },
        )
        self.assertEqual(create_res.status_code, 200)
        created = create_res.json()
        self.assertEqual(created["fir_icao"], "WMFC")
        self.assertEqual(created["route_text"], "WMKK DCT IGARI L894 OTHH")

        second_create_res = self.client.post(
            "/api/fir-feedback",
            json={
                "fir_icao": "WMFC",
                "fir_name": "KUALA LUMPUR FIR",
                "flight_date": "31May26",
                "route_text": "WMKK DCT PULIP L894 OTHH",
                "from_icao": "WMKK",
                "to_icao": "OTHH",
                "comments": "Second history entry for the same FIR.",
            },
        )
        self.assertEqual(second_create_res.status_code, 200)

        get_res = self.client.get(
            "/api/fir-feedback",
            params={"firs": "WMFC,OBBB"},
        )
        self.assertEqual(get_res.status_code, 200)
        grouped = get_res.json()
        self.assertEqual(len(grouped["WMFC"]), 2)
        self.assertEqual(grouped["WMFC"][0]["flight_date"], "31May26")
        self.assertEqual(grouped["WMFC"][1]["flight_date"], "10May26")
        self.assertEqual(grouped["OBBB"], [])

        delete_res = self.client.delete(f"/api/fir-feedback/{created['id']}")
        self.assertEqual(delete_res.status_code, 200)
        self.assertEqual(delete_res.json(), {"deleted": True})

        get_after_delete = self.client.get(
            "/api/fir-feedback",
            params={"firs": "WMFC"},
        )
        self.assertEqual(get_after_delete.status_code, 200)
        self.assertEqual(len(get_after_delete.json()["WMFC"]), 1)
        self.assertEqual(get_after_delete.json()["WMFC"][0]["flight_date"], "31May26")

    def test_disabled_mode_hides_feature_and_rejects_mutations(self) -> None:
        os.environ["AIRPORT_FEEDBACK_ENABLED"] = "0"

        get_res = self.client.get(
            "/api/airport-feedback",
            params={"departure": "OTHH", "arrival": "OLBA"},
        )
        self.assertEqual(get_res.status_code, 200)
        self.assertIsNone(get_res.json())

        create_res = self.client.post(
            "/api/airport-feedback",
            json={
                "section": "departure",
                "airport_icao": "OTHH",
                "flight_date": "01Jun26",
                "route_text": "OTHH → OLBA",
                "from_icao": "OTHH",
                "to_icao": "OLBA",
                "sid": "TULUB2A",
                "star": None,
                "runway": "34L",
                "approach_runway": None,
                "comments": "Should be rejected while disabled.",
            },
        )
        self.assertEqual(create_res.status_code, 403)

        delete_res = self.client.delete("/api/airport-feedback/1")
        self.assertEqual(delete_res.status_code, 403)

        fir_get_res = self.client.get(
            "/api/fir-feedback",
            params={"firs": "WMFC"},
        )
        self.assertEqual(fir_get_res.status_code, 200)
        self.assertIsNone(fir_get_res.json())

        fir_create_res = self.client.post(
            "/api/fir-feedback",
            json={
                "fir_icao": "WMFC",
                "fir_name": "KUALA LUMPUR FIR",
                "flight_date": "10May26",
                "route_text": "WMKK DCT IGARI L894 OTHH",
                "from_icao": "WMKK",
                "to_icao": "OTHH",
                "comments": "Should be rejected while disabled.",
            },
        )
        self.assertEqual(fir_create_res.status_code, 403)

        fir_delete_res = self.client.delete("/api/fir-feedback/1")
        self.assertEqual(fir_delete_res.status_code, 403)


if __name__ == "__main__":
    unittest.main()
