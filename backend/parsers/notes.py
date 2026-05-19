from __future__ import annotations

import logging
from pathlib import Path
import re

_DATA_PATH = Path(__file__).resolve().parents[2] / "Operational Info.txt"
_ICAO_HEADER_RE = re.compile(r"^\[([A-Z]{4})\]$")
_SECTION_RE = re.compile(r"^(DEP|ARR)\s*:\s*(.*)$")
_cache: dict[str, dict[str, str]] | None = None
_cache_mtime_ns: int | None = None
_missing_file_warned = False
logger = logging.getLogger(__name__)


def _load() -> dict[str, dict[str, str]]:
    global _missing_file_warned

    if not _DATA_PATH.exists():
        if not _missing_file_warned:
            logger.warning("Operational info file not found at %s", _DATA_PATH)
            _missing_file_warned = True
        return {}

    text = _DATA_PATH.read_text(encoding="utf-8")
    result: dict[str, dict[str, str]] = {}

    current_icao: str | None = None
    current_section: str | None = None
    buffer: list[str] = []

    def flush_section() -> None:
        nonlocal buffer
        if not current_icao or not current_section:
            buffer = []
            return

        content = "\n".join(line.rstrip() for line in buffer).strip()
        if content:
            result.setdefault(current_icao, {})[current_section] = content
        buffer = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        header_match = _ICAO_HEADER_RE.match(stripped)
        if header_match:
            flush_section()
            current_icao = header_match.group(1)
            current_section = None
            continue

        section_match = _SECTION_RE.match(stripped)
        if section_match:
            flush_section()
            current_section = "departure" if section_match.group(1) == "DEP" else "arrival"
            buffer = [section_match.group(2).strip()]
            continue

        if current_section:
            buffer.append(line)

    flush_section()
    return result


def get_notes_data_path() -> Path:
    return _DATA_PATH


def notes_data_file_exists() -> bool:
    return _DATA_PATH.exists()


def get_airport_notes(icao: str) -> dict[str, str] | None:
    global _cache
    global _cache_mtime_ns

    if not icao:
        return None

    try:
        mtime_ns = _DATA_PATH.stat().st_mtime_ns
    except FileNotFoundError:
        _cache = {}
        _cache_mtime_ns = None
        return None

    if _cache is None or _cache_mtime_ns != mtime_ns:
        _cache = _load()
        _cache_mtime_ns = mtime_ns

    return _cache.get(icao.upper())
