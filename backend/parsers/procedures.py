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


def _find_runway_line_index(lines: list[str], icao: str | None, runway: str | None) -> int | None:
    for idx, line in enumerate(lines):
        match = RUNWAY_LINE_RE.match(line.strip())
        if not match:
            continue
        if icao and match.group("icao") != icao:
            continue
        if runway and match.group("runway") != runway:
            continue
        return idx
    return None


def extract_sid_from_route_pages(
    pages: list[str],
    departure_icao: str | None,
    departure_runway: str | None,
) -> str | None:
    route_pages = iter_route_pages(pages)
    if not route_pages:
        return None

    lines = route_pages[0].splitlines()
    runway_idx = _find_runway_line_index(lines, departure_icao, departure_runway)
    if runway_idx is None:
        return None

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
            start_idx = runway_idx - 1

        for idx in range(start_idx, -1, -1):
            stripped = lines[idx].strip()
            if not stripped or stripped.startswith("ELEV ") or stripped.startswith("Page "):
                continue
            token = _leading_token(stripped)
            if token and is_procedure_token(token):
                return token

    return None
