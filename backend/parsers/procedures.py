from __future__ import annotations

import re


ROUTE_PAGE_RE = re.compile(r"PAGE\s+\d+/\d+")
RUNWAY_LINE_RE = re.compile(r"^(?P<icao>[A-Z]{4})/(?P<runway>\d{2}[LRC]?)\b")
PROCEDURE_TOKEN_RE = re.compile(r"^[A-Z]{3,}\d[A-Z0-9]*$")


def is_route_page(page: str) -> bool:
    return (
        bool(ROUTE_PAGE_RE.search(page))
        and "AWY" in page
        and "WPT" in page
        and "PLAN REM" in page
    )


def iter_route_pages(pages: list[str]) -> list[str]:
    return [page for page in pages if is_route_page(page) and "DESTINATION TO ALTERNATE" not in page]


def is_procedure_token(token: str) -> bool:
    return bool(PROCEDURE_TOKEN_RE.fullmatch(token))


def _leading_token(line: str) -> str | None:
    stripped = line.strip()
    if not stripped:
        return None
    return stripped.split()[0]


def _extract_clearance_block(line_iter: list[str], start_idx: int) -> str:
    parts: list[str] = []
    for line in line_iter[start_idx + 1:]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("FL") or stripped.startswith("FUEL TIME"):
            break
        parts.append(stripped)
    return " ".join(parts)


def _find_runway_line_index(lines: list[str], icao: str | None, runway: str | None) -> int | None:
    for idx, line in enumerate(lines):
        stripped = line.strip()
        match = RUNWAY_LINE_RE.match(stripped)
        if not match:
            if icao and runway and re.search(rf"\b{re.escape(icao)}\s+{re.escape(runway)}\b", stripped):
                return idx
            continue
        if icao and match.group("icao") != icao:
            continue
        if runway and match.group("runway") != runway:
            continue
        return idx
    return None


def _extract_sid_from_lines(
    lines: list[str],
    departure_icao: str | None,
    departure_runway: str | None,
) -> str | None:
    runway_idx = _find_runway_line_index(lines, departure_icao, departure_runway)
    if runway_idx is None:
        return None

    runway_line = lines[runway_idx].strip()
    runway_line_patterns: list[re.Pattern[str]] = []
    if departure_icao and departure_runway:
        runway_line_patterns.append(
            re.compile(rf"^{re.escape(departure_icao)}/{re.escape(departure_runway)}\b\s*(?P<rest>.*)$")
        )
        runway_line_patterns.append(
            re.compile(rf"\b{re.escape(departure_icao)}\s+{re.escape(departure_runway)}\b\s*(?P<rest>.*)$")
        )

    for pattern in runway_line_patterns:
        match = pattern.search(runway_line)
        if not match:
            continue
        token = _leading_token(match.group("rest"))
        if token and is_procedure_token(token):
            return token

    for line in lines[runway_idx + 1:]:
        stripped = line.strip()
        if not stripped or stripped.startswith("ELEV "):
            continue
        if stripped.startswith("---") or " FIR " in stripped or stripped.startswith("Page "):
            break
        token = _leading_token(stripped)
        if token and is_procedure_token(token):
            return token

    return None


def extract_sid_from_route_pages(
    pages: list[str],
    departure_icao: str | None,
    departure_runway: str | None,
) -> str | None:
    route_pages = iter_route_pages(pages)
    if route_pages:
        sid = _extract_sid_from_lines(route_pages[0].splitlines(), departure_icao, departure_runway)
        if sid:
            return sid

    for page in pages[:5]:
        if "ATC CLEARANCE" not in page and "DEFRTE:" not in page:
            continue
        sid = _extract_sid_from_lines(page.splitlines(), departure_icao, departure_runway)
        if sid:
            return sid

    return None


def extract_star_from_route_pages(
    pages: list[str],
    arrival_icao: str | None,
    arrival_runway: str | None,
) -> str | None:
    route_pages = iter_route_pages(pages)
    arrival_found = False

    for page in reversed(route_pages):
        lines = page.splitlines()
        start_idx = len(lines) - 1

        if not arrival_found:
            runway_idx = _find_runway_line_index(lines, arrival_icao, arrival_runway)
            if runway_idx is None:
                continue
            arrival_found = True
            for idx in range(runway_idx - 1, -1, -1):
                stripped = lines[idx].strip()
                if not stripped or stripped.startswith("ELEV ") or stripped.startswith("Page "):
                    continue
                token = _leading_token(stripped)
                if token == "DCT":
                    return None
                if token and is_procedure_token(token):
                    return token
            start_idx = runway_idx - 1

        for idx in range(start_idx, -1, -1):
            stripped = lines[idx].strip()
            if not stripped or stripped.startswith("ELEV ") or stripped.startswith("Page "):
                continue
            token = _leading_token(stripped)
            if token and is_procedure_token(token):
                return token

    if arrival_icao and arrival_runway:
        route_pages_forward = iter_route_pages(pages)
        for page in route_pages_forward:
            lines = page.splitlines()
            for idx, line in enumerate(lines):
                stripped = line.strip()
                if "ATC CLEARANCE" not in stripped and "DEFRTE:" not in stripped:
                    continue
                clearance = _extract_clearance_block(lines, idx)
                match = re.search(
                    rf"\b(?P<token>[A-Z0-9]+)\s+{re.escape(arrival_icao)}\s+{re.escape(arrival_runway)}\b",
                    clearance,
                )
                if not match:
                    continue
                token = match.group("token")
                if token == "DCT":
                    return None
                if is_procedure_token(token):
                    return token

    return None
