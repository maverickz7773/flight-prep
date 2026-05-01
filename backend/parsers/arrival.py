from __future__ import annotations
import re
from models.briefing import ArrivalInfo, AlternateInfo


def parse_arrival(pages: list[str]) -> ArrivalInfo:
    text = "\n".join(pages[:5])

    arr_rwy = None
    star = None

    route_match = re.search(
        r"\w{4}\s+\d{2}[LRC]?\s+(?:[A-Z][A-Z0-9]+\s+)+(\w+)\s+(\w{4})\s+(\d{2}[LRC]?)",
        text,
    )
    if route_match:
        arr_rwy = route_match.group(3)

    for page in reversed(pages):
        if not (re.search(r"PAGE\s+\d+/\d+", page) and "AWY" in page and "WPT" in page):
            continue
        if "DESTINATION TO ALTERNATE" in page:
            continue
        arr_line = re.search(
            r"(\w+\d+[A-Z])\s+\d+\s+.*?\n\w{4}/\d{2}[LRC]?\s+\d{4}",
            page,
        )
        if arr_line:
            star = arr_line.group(1)
            break

    if not star and route_match:
        star_candidate = route_match.group(1)
        if re.match(r"[A-Z]+\d+[A-Z]", star_candidate):
            star = star_candidate

    alternates: list[AlternateInfo] = []
    alt_pattern = re.compile(
        r"(\w{4})\s+(\d{2}[LRC]?)\s+(\d{4})\s+(\d{3})\s+([MP]\d{3})\s+(\d{4})\s+(\d+)\s+(.*?)$",
        re.MULTILINE,
    )

    for page in pages[:5]:
        if "DEST ALTN" not in page:
            continue
        for m in alt_pattern.finditer(page):
            alternates.append(AlternateInfo(
                icao=m.group(1),
                runway=m.group(2),
                distance=int(m.group(3)),
                flight_level=m.group(4),
                wind_component=m.group(5),
                time=m.group(6),
                fuel=int(m.group(7)),
                route=m.group(8).strip(),
            ))

    if not alternates:
        for page in pages[:5]:
            for m in re.finditer(
                r"(\w{4})\s+(\d{2}[LRC]?)\s+(\d{4})\s+(\d{3})\s+\S+\s+(\d{4})\s+(\d+)\s+(.+?)$",
                page,
                re.MULTILINE,
            ):
                icao = m.group(1)
                if icao in ("MZFW", "MTOW", "MLWT", "CONT", "DEST"):
                    continue
                alternates.append(AlternateInfo(
                    icao=icao,
                    runway=m.group(2),
                    distance=int(m.group(3)),
                    flight_level=m.group(4),
                    time=m.group(5),
                    fuel=int(m.group(6)),
                    route=m.group(7).strip(),
                ))

    return ArrivalInfo(
        runway=arr_rwy,
        star=star,
        alternates=alternates,
    )
