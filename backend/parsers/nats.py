from __future__ import annotations

import logging
from pathlib import Path
import re

from models.briefing import NATSOverview, NATSProcedure, RouteSummary


_DATA_PATH = Path(__file__).resolve().parents[2] / "NATS Procedure.txt"
_SECTION_HEADER_RE = re.compile(r"^\[(NATS [^\]]+)\]$")
_FIR_LABEL_RE = re.compile(r"^(.*?)\s+\(([A-Z]{4})\)$")
_TMI_RE = re.compile(r"\bTMI(?:\s+IS)?\s*[:.]?\s*(\d+)\b", re.IGNORECASE)
_SYNTHETIC_BOUNDARY_RE = re.compile(r"^(ENTRY|EXIT)\d+$")
_COORD_TOKEN_RE = re.compile(r"^[NS]\d{4}[EW]\d{5}$")
_TRIGGER_FIRS = {"ENOB", "BIRD", "EGGX", "BGGL", "CZQX", "KZWY"}
_cache: dict[str, str] | None = None
_cache_mtime_ns: int | None = None
_missing_file_warned = False
logger = logging.getLogger(__name__)


def _load_sections() -> dict[str, str]:
    global _missing_file_warned

    if not _DATA_PATH.exists():
        if not _missing_file_warned:
            logger.warning("NATS procedure file not found at %s", _DATA_PATH)
            _missing_file_warned = True
        return {}

    text = _DATA_PATH.read_text(encoding="utf-8")
    result: dict[str, str] = {}
    current_section: str | None = None
    buffer: list[str] = []

    def flush_section() -> None:
        nonlocal buffer
        if not current_section:
            buffer = []
            return
        content = "\n".join(line.rstrip() for line in buffer).strip()
        result[current_section] = content
        buffer = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        header_match = _SECTION_HEADER_RE.match(stripped)
        if header_match:
            flush_section()
            current_section = header_match.group(1)
            continue
        if current_section:
            buffer.append(line)

    flush_section()
    return result


def _get_sections() -> dict[str, str]:
    global _cache
    global _cache_mtime_ns

    try:
        mtime_ns = _DATA_PATH.stat().st_mtime_ns
    except FileNotFoundError:
        _cache = {}
        _cache_mtime_ns = None
        return {}

    if _cache is None or _cache_mtime_ns != mtime_ns:
        _cache = _load_sections()
        _cache_mtime_ns = mtime_ns

    return _cache


def get_nats_sections() -> dict[str, str]:
    return dict(_get_sections())


def _extract_trigger_firs(fir_sequence: list[str]) -> list[str]:
    trigger_firs: list[str] = []
    for fir_label in fir_sequence:
        match = _FIR_LABEL_RE.match(fir_label)
        if not match:
            continue
        fir_icao = match.group(2)
        if fir_icao in _TRIGGER_FIRS and fir_icao not in trigger_firs:
            trigger_firs.append(fir_icao)
    return trigger_firs


def _is_real_waypoint_name(name: str | None) -> bool:
    if not name:
        return False
    if _SYNTHETIC_BOUNDARY_RE.match(name):
        return False
    if _COORD_TOKEN_RE.match(name):
        return False
    return True


def _find_trigger_segment(route: RouteSummary) -> tuple[int, int] | None:
    start_idx: int | None = None
    end_idx: int | None = None

    for idx, waypoint in enumerate(route.waypoints):
        if waypoint.fir_icao in _TRIGGER_FIRS:
            if start_idx is None:
                start_idx = idx
            end_idx = idx
            continue
        if start_idx is not None:
            break

    if start_idx is None or end_idx is None:
        return None
    return start_idx, end_idx


def _resolve_boundary_waypoints(
    route: RouteSummary,
    start_idx: int,
    end_idx: int,
) -> tuple[int, int]:
    entry_idx = start_idx
    exit_idx = end_idx

    if not _is_real_waypoint_name(route.waypoints[entry_idx].name):
        for idx in range(entry_idx - 1, -1, -1):
            if _is_real_waypoint_name(route.waypoints[idx].name):
                entry_idx = idx
                break
        for idx in range(start_idx + 1, len(route.waypoints)):
            if _is_real_waypoint_name(route.waypoints[idx].name):
                entry_idx = idx
                break

    if not _is_real_waypoint_name(route.waypoints[exit_idx].name):
        for idx in range(exit_idx + 1, len(route.waypoints)):
            if _is_real_waypoint_name(route.waypoints[idx].name):
                exit_idx = idx
                break
        else:
            for idx in range(exit_idx - 1, -1, -1):
                if _is_real_waypoint_name(route.waypoints[idx].name):
                    exit_idx = idx
                    break

    return entry_idx, exit_idx


def _build_route_segment(
    route: RouteSummary,
    entry_name: str,
    exit_name: str,
) -> str | None:
    if not route.route_string:
        return None

    tokens = route.route_string.replace("\n", " ").split()
    if not tokens:
        return None

    try:
        start_token_idx = tokens.index(entry_name)
    except ValueError:
        return None

    end_token_idx = None
    for idx in range(start_token_idx, len(tokens)):
        if tokens[idx] == exit_name:
            end_token_idx = idx
            break

    if end_token_idx is None or end_token_idx < start_token_idx:
        return None

    segment_tokens = tokens[start_token_idx : end_token_idx + 1]
    while segment_tokens and segment_tokens[-1] == "DCT":
        segment_tokens.pop()

    return " ".join(segment_tokens).strip() or None


def _extract_tmi(pages: list[str]) -> str | None:
    text = "\n".join(pages[:25])
    match = _TMI_RE.search(text)
    if match:
        return match.group(1)
    return None


def _extract_enroute_callouts(enroute_text: str, trigger_firs: list[str]) -> list[str]:
    callouts: list[str] = []
    for raw_line in enroute_text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if any(fir_icao in stripped for fir_icao in trigger_firs):
            callouts.append(stripped)
            continue
        if "BIRD" in trigger_firs and "BIRD" in stripped:
            callouts.append(stripped)
    return callouts


def parse_nats_procedure(pages: list[str], route: RouteSummary) -> NATSProcedure | None:
    sections = _get_sections()
    trigger_firs = _extract_trigger_firs(route.fir_sequence)
    if not trigger_firs:
        return None

    trigger_segment = _find_trigger_segment(route)
    overview = NATSOverview()
    if trigger_segment:
        start_idx, end_idx = trigger_segment
        entry_idx, exit_idx = _resolve_boundary_waypoints(route, start_idx, end_idx)
        entry_waypoint = route.waypoints[entry_idx]
        exit_waypoint = route.waypoints[exit_idx]
        overview = NATSOverview(
            tmi=_extract_tmi(pages),
            route=_build_route_segment(route, entry_waypoint.name, exit_waypoint.name),
            entry_point=entry_waypoint.name,
            entry_eet=entry_waypoint.eta,
            entry_fir=entry_waypoint.fir_icao,
            exit_point=exit_waypoint.name,
            exit_eet=exit_waypoint.eta,
            exit_fir=exit_waypoint.fir_icao,
        )
    else:
        overview = NATSOverview(tmi=_extract_tmi(pages))

    overview_text = sections.get("NATS Overview", "")
    preflight_text = sections.get("NATS Preflight and Planning", "")
    enroute_text = sections.get("NATS Enroute", "")
    exit_text = sections.get("NATS Exit", "")

    return NATSProcedure(
        trigger_firs=trigger_firs,
        overview_text=overview_text,
        preflight_text=preflight_text,
        enroute_text=enroute_text,
        exit_text=exit_text,
        enroute_fir_callouts=_extract_enroute_callouts(enroute_text, trigger_firs),
        overview=overview,
    )
