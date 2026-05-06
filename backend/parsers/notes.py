from __future__ import annotations

from pathlib import Path
import re

_DATA_PATH = Path(__file__).resolve().parents[2] / "Operational Info.txt"
_ICAO_HEADER_RE = re.compile(r"^\[([A-Z]{4})\]$")
_cache: dict[str, dict[str, str]] | None = None
_cache_mtime_ns: int | None = None


def _load() -> dict[str, dict[str, str]]:
    if not _DATA_PATH.exists():
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

        if stripped.startswith("DEP:"):
            flush_section()
            current_section = "departure"
            buffer = [stripped[4:].strip()]
            continue

        if stripped.startswith("ARR:"):
            flush_section()
            current_section = "arrival"
            buffer = [stripped[4:].strip()]
            continue

        if current_section:
            buffer.append(line)

    flush_section()
    return result


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
