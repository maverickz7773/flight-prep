from __future__ import annotations

import logging
from pathlib import Path
import re

from models.briefing import EnrouteInfoItem


_DATA_PATH = Path(__file__).resolve().parents[2] / "Enroute Info.txt"
_ICAO_HEADER_RE = re.compile(r"^\[([A-Z]{4})\]$")
_cache: dict[str, str] | None = None
_cache_mtime_ns: int | None = None
_missing_file_warned = False
logger = logging.getLogger(__name__)


def _load() -> dict[str, str]:
    global _missing_file_warned

    if not _DATA_PATH.exists():
        if not _missing_file_warned:
            logger.warning("Enroute info file not found at %s", _DATA_PATH)
            _missing_file_warned = True
        return {}

    text = _DATA_PATH.read_text(encoding="utf-8")
    result: dict[str, str] = {}
    current_icao: str | None = None
    buffer: list[str] = []

    def flush_block() -> None:
        nonlocal buffer
        if not current_icao:
            buffer = []
            return

        content = "\n".join(line.rstrip() for line in buffer).strip()
        if content:
            result[current_icao] = content
        buffer = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        header_match = _ICAO_HEADER_RE.match(stripped)
        if header_match:
            flush_block()
            current_icao = header_match.group(1)
            continue

        if current_icao:
            buffer.append(line)

    flush_block()
    return result


def get_enroute_info(icao: str) -> str | None:
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


def build_enroute_info_items(fir_sequence: list[str]) -> list[EnrouteInfoItem]:
    items: list[EnrouteInfoItem] = []

    for fir_label in fir_sequence:
        match = re.search(r"^(.*?)\s+\(([A-Z]{4})\)$", fir_label)
        if not match:
            continue

        fir_name = match.group(1).strip()
        fir_icao = match.group(2)
        notes = get_enroute_info(fir_icao)
        if not notes:
            continue

        items.append(
            EnrouteInfoItem(
                fir_icao=fir_icao,
                fir_name=fir_name,
                notes=notes,
            )
        )

    return items
