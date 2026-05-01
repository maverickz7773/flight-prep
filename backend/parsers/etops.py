from __future__ import annotations
import re
from models.briefing import ETOPSInfo, ETOPSPoint, ETOPSAlternate


def parse_etops(pages: list[str]) -> ETOPSInfo | None:
    etops_text = None
    for page in pages:
        if "ETOPS INFORMATION" in page:
            etops_text = page
            break

    if not etops_text:
        return None

    entry = _parse_point(etops_text, "ENTRY")
    exit_pt = _parse_point(etops_text, "EXIT")

    etp_points: list[ETOPSPoint] = []
    for m in re.finditer(
        r"ETP\s+([\d.]+)\s+([NS]\d+\.?\d*)\s+(\w{4})\s+.*?(\w{4})?",
        etops_text,
    ):
        etp_points.append(ETOPSPoint(
            point_type="ETP",
            eet=m.group(1),
            position=m.group(2),
            alternate_icao=m.group(3),
            alternate_icao_2=m.group(4) if m.group(4) else None,
        ))

    if not etp_points:
        etp_match = re.search(
            r"ETP\s+([\d.]+)\s+([NS]\d+\.?\d*)\s+(\w{4})",
            etops_text,
        )
        if etp_match:
            line = etops_text[etp_match.start():]
            alt2 = re.search(r"\n\s+\S+\s+(\w{4})", line)
            etp_points.append(ETOPSPoint(
                point_type="ETP",
                eet=etp_match.group(1),
                position=etp_match.group(2),
                alternate_icao=etp_match.group(3),
                alternate_icao_2=alt2.group(1) if alt2 else None,
            ))

    alternates: list[ETOPSAlternate] = []
    alt_section = re.search(
        r"SUITABLE\s+ALTN\s+AIRPORTS:(.*?)(?:Page\s+\d+|$)",
        etops_text,
        re.DOTALL,
    )
    if alt_section:
        for m in re.finditer(
            r"(\w{4})\s+(\d{2}[LRC]?)\s+(\d{4}-\d{4})\s+(\S+)\s+(\S+/\S+)\s+(\S+/\S+)",
            alt_section.group(1),
        ):
            alternates.append(ETOPSAlternate(
                icao=m.group(1),
                runway=m.group(2),
                period=m.group(3),
                approach=m.group(4),
                weather=m.group(5),
                minima=m.group(6),
            ))

    return ETOPSInfo(
        entry=entry,
        exit=exit_pt,
        etp_points=etp_points,
        suitable_alternates=alternates,
    )


def _parse_point(text: str, point_type: str) -> ETOPSPoint | None:
    m = re.search(
        rf"{point_type}\s+([\d.]+)\s+([NS]\d+\.?\d*)\s+(\w{{4}})",
        text,
    )
    if not m:
        return None

    fuel_m = re.search(
        rf"{point_type}\s+[\d.]+\s+\S+\s+\w{{4}}.*?([\d.]+)\s*$",
        text,
        re.MULTILINE,
    )

    return ETOPSPoint(
        point_type=point_type,
        eet=m.group(1),
        position=m.group(2),
        alternate_icao=m.group(3),
        fuel_remaining=float(fuel_m.group(1)) if fuel_m else None,
    )
