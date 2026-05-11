from __future__ import annotations
import re
from models.briefing import ArrivalInfo, AlternateInfo
from parsers.procedures import extract_star_from_route_pages, is_procedure_token


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

    arrival_icao = None
    if route_match:
        arrival_icao = route_match.group(2)

    star = extract_star_from_route_pages(pages, arrival_icao, arr_rwy)

    if not star and route_match:
        star_candidate = route_match.group(1)
        if is_procedure_token(star_candidate):
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
