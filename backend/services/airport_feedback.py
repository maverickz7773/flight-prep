from __future__ import annotations

from contextlib import closing
from datetime import datetime, timezone
import os
from pathlib import Path
import sqlite3

from models.briefing import (
    AirportFeedback,
    AirportFeedbackCreate,
    AirportFeedbackEntry,
    FIRFeedbackCreate,
    FIRFeedbackEntry,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
LOCAL_DATA_DIR = REPO_ROOT / "data"
DEFAULT_DB_NAME = "airport_feedback.sqlite3"


def _normalize_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    lowered = value.strip().lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    return None


def airport_feedback_enabled() -> bool:
    env_override = _normalize_bool(os.getenv("AIRPORT_FEEDBACK_ENABLED"))
    if env_override is not None:
        return env_override

    if os.getenv("RENDER") or os.getenv("RENDER_SERVICE_ID"):
        return False

    return True


def get_airport_feedback_db_path() -> Path:
    env_path = os.getenv("AIRPORT_FEEDBACK_DB_PATH")
    if env_path:
        return Path(env_path)

    container_data_dir = Path("/app/data")
    if container_data_dir.exists():
        return container_data_dir / DEFAULT_DB_NAME

    return LOCAL_DATA_DIR / DEFAULT_DB_NAME


def _connect() -> sqlite3.Connection:
    db_path = get_airport_feedback_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS airport_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section TEXT NOT NULL CHECK (section IN ('departure', 'arrival')),
            airport_icao TEXT NOT NULL,
            flight_date TEXT NOT NULL,
            route_text TEXT,
            from_icao TEXT NOT NULL,
            to_icao TEXT NOT NULL,
            sid TEXT,
            star TEXT,
            runway TEXT,
            approach_runway TEXT,
            comments TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS fir_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fir_icao TEXT NOT NULL,
            fir_name TEXT NOT NULL,
            flight_date TEXT NOT NULL,
            route_text TEXT,
            from_icao TEXT NOT NULL,
            to_icao TEXT NOT NULL,
            comments TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    existing_columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(airport_feedback)").fetchall()
    }
    if "route_text" not in existing_columns:
        conn.execute("ALTER TABLE airport_feedback ADD COLUMN route_text TEXT")
    if "star" not in existing_columns:
        conn.execute("ALTER TABLE airport_feedback ADD COLUMN star TEXT")
    if "runway" not in existing_columns:
        conn.execute("ALTER TABLE airport_feedback ADD COLUMN runway TEXT")
    conn.commit()
    return conn


def _row_to_entry(row: sqlite3.Row) -> AirportFeedbackEntry:
    return AirportFeedbackEntry(
        id=int(row["id"]),
        section=str(row["section"]),
        airport_icao=str(row["airport_icao"]),
        flight_date=str(row["flight_date"]),
        route_text=row["route_text"],
        from_icao=str(row["from_icao"]),
        to_icao=str(row["to_icao"]),
        sid=row["sid"],
        star=row["star"],
        runway=row["runway"],
        approach_runway=row["approach_runway"],
        comments=str(row["comments"]),
        created_at=str(row["created_at"]),
    )


def _row_to_fir_entry(row: sqlite3.Row) -> FIRFeedbackEntry:
    return FIRFeedbackEntry(
        id=int(row["id"]),
        fir_icao=str(row["fir_icao"]),
        fir_name=str(row["fir_name"]),
        flight_date=str(row["flight_date"]),
        route_text=row["route_text"],
        from_icao=str(row["from_icao"]),
        to_icao=str(row["to_icao"]),
        comments=str(row["comments"]),
        created_at=str(row["created_at"]),
    )


def _list_for_section(conn: sqlite3.Connection, airport_icao: str, section: str) -> list[AirportFeedbackEntry]:
    rows = conn.execute(
        """
        SELECT *
        FROM airport_feedback
        WHERE airport_icao = ? AND section = ?
        ORDER BY datetime(created_at) DESC, id DESC
        """,
        (airport_icao.upper(), section),
    ).fetchall()
    return [_row_to_entry(row) for row in rows]


def _list_for_fir(conn: sqlite3.Connection, fir_icao: str) -> list[FIRFeedbackEntry]:
    rows = conn.execute(
        """
        SELECT *
        FROM fir_feedback
        WHERE fir_icao = ?
        ORDER BY datetime(created_at) DESC, id DESC
        """,
        (fir_icao.upper(),),
    ).fetchall()
    return [_row_to_fir_entry(row) for row in rows]


def get_airport_feedback(departure: str, arrival: str) -> AirportFeedback | None:
    if not airport_feedback_enabled():
        return None

    with closing(_connect()) as conn:
        departure_items = _list_for_section(conn, departure, "departure") if departure else []
        arrival_items = _list_for_section(conn, arrival, "arrival") if arrival else []

    return AirportFeedback(
        departure=departure_items,
        arrival=arrival_items,
    )


def get_fir_feedback(firs: list[str]) -> dict[str, list[FIRFeedbackEntry]] | None:
    if not airport_feedback_enabled():
        return None

    unique_firs = list(dict.fromkeys(fir.strip().upper() for fir in firs if fir and fir.strip()))
    if not unique_firs:
        return {}

    with closing(_connect()) as conn:
        return {fir: _list_for_fir(conn, fir) for fir in unique_firs}


def create_airport_feedback(payload: AirportFeedbackCreate) -> AirportFeedbackEntry:
    if not airport_feedback_enabled():
        raise RuntimeError("Airport feedback feature is disabled")

    section = payload.section.strip().lower()
    if section not in {"departure", "arrival"}:
        raise ValueError("section must be departure or arrival")

    comments = payload.comments.strip()
    if not comments:
        raise ValueError("comments are required")

    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with closing(_connect()) as conn:
        cursor = conn.execute(
            """
            INSERT INTO airport_feedback (
                section,
                airport_icao,
                flight_date,
                route_text,
                from_icao,
                to_icao,
                sid,
                star,
                runway,
                approach_runway,
                comments,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                section,
                payload.airport_icao.upper(),
                payload.flight_date.strip(),
                payload.route_text.strip() if payload.route_text else None,
                payload.from_icao.upper(),
                payload.to_icao.upper(),
                payload.sid.strip() if payload.sid else None,
                payload.star.strip() if payload.star else None,
                payload.runway.strip() if payload.runway else None,
                payload.approach_runway.strip() if payload.approach_runway else None,
                comments,
                created_at,
            ),
        )
        entry_id = int(cursor.lastrowid)
        conn.commit()
        row = conn.execute(
            "SELECT * FROM airport_feedback WHERE id = ?",
            (entry_id,),
        ).fetchone()

    if row is None:
        raise RuntimeError("Failed to load created airport feedback entry")

    return _row_to_entry(row)


def create_fir_feedback(payload: FIRFeedbackCreate) -> FIRFeedbackEntry:
    if not airport_feedback_enabled():
        raise RuntimeError("Airport feedback feature is disabled")

    fir_icao = payload.fir_icao.strip().upper()
    fir_name = payload.fir_name.strip()
    comments = payload.comments.strip()
    if not fir_icao:
        raise ValueError("fir_icao is required")
    if not fir_name:
        raise ValueError("fir_name is required")
    if not payload.flight_date.strip():
        raise ValueError("flight_date is required")
    if not payload.from_icao.strip() or not payload.to_icao.strip():
        raise ValueError("from_icao and to_icao are required")
    if not comments:
        raise ValueError("comments are required")

    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with closing(_connect()) as conn:
        cursor = conn.execute(
            """
            INSERT INTO fir_feedback (
                fir_icao,
                fir_name,
                flight_date,
                route_text,
                from_icao,
                to_icao,
                comments,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fir_icao,
                fir_name,
                payload.flight_date.strip(),
                payload.route_text.strip() if payload.route_text else None,
                payload.from_icao.strip().upper(),
                payload.to_icao.strip().upper(),
                comments,
                created_at,
            ),
        )
        entry_id = int(cursor.lastrowid)
        conn.commit()
        row = conn.execute(
            "SELECT * FROM fir_feedback WHERE id = ?",
            (entry_id,),
        ).fetchone()

    if row is None:
        raise RuntimeError("Failed to load created FIR feedback entry")

    return _row_to_fir_entry(row)


def delete_airport_feedback(entry_id: int) -> bool:
    if not airport_feedback_enabled():
        raise RuntimeError("Airport feedback feature is disabled")

    with closing(_connect()) as conn:
        cursor = conn.execute(
            "DELETE FROM airport_feedback WHERE id = ?",
            (entry_id,),
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_fir_feedback(entry_id: int) -> bool:
    if not airport_feedback_enabled():
        raise RuntimeError("Airport feedback feature is disabled")

    with closing(_connect()) as conn:
        cursor = conn.execute(
            "DELETE FROM fir_feedback WHERE id = ?",
            (entry_id,),
        )
        conn.commit()
        return cursor.rowcount > 0
