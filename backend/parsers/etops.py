from __future__ import annotations
import re
from models.briefing import ETOPSInfo, ETOPSPoint, ETOPSAlternate, ETOPSSector


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
        sectors=_build_sectors(etops_text),
        entry=entry,
        exit=exit_pt,
        etp_points=etp_points,
        suitable_alternates=alternates,
    )


def _build_sectors(text: str) -> list[ETOPSSector]:
    # Multi-sector: ENTRY1/EXIT1/ENTRY2/EXIT2...
    entry_matches = list(re.finditer(
        r"ENTRY(\d)\s+([\d.]+)\s+[NS][\d.]+\s+\w{4}[^\n]*\n(\w{4})",
        text,
    ))
    exit_matches = list(re.finditer(
        r"EXIT(\d)\s+([\d.]+)\s+[NS][\d.]+\s+\w{4}[^\n]*\n(\w{4})",
        text,
    ))

    if entry_matches:
        sectors: list[ETOPSSector] = []
        for i, em in enumerate(entry_matches):
            num = em.group(1)
            entry_eet = em.group(2)
            entry_icao = em.group(3)
            entry_line = text[em.start():].split("\n")[0]
            entry_fuel = _last_float(entry_line)

            xm = next((x for x in exit_matches if x.group(1) == num), None)
            exit_icao = xm.group(3) if xm else None
            exit_eet = xm.group(2) if xm else None
            exit_fuel = None
            if xm:
                exit_line = text[xm.start():].split("\n")[0]
                exit_fuel = _last_float(exit_line)

            start = em.start()
            end = entry_matches[i + 1].start() if i + 1 < len(entry_matches) else len(text)
            sector_text = text[start:end]
            sectors.append(ETOPSSector(
                sector_number=int(num),
                entry_icao=entry_icao,
                entry_eet=entry_eet,
                entry_fuel=entry_fuel,
                exit_icao=exit_icao,
                exit_eet=exit_eet,
                exit_fuel=exit_fuel,
                alternates=_etp_alternates(sector_text),
            ))
        return sectors

    # Single sector: ENTRY/EXIT without digit
    entry_m = re.search(r"ENTRY\s+([\d.]+)\s+[NS][\d.]+\s+\w{4}[^\n]*\n(\w{4})", text)
    exit_m = re.search(r"EXIT\s+([\d.]+)\s+[NS][\d.]+\s+\w{4}[^\n]*\n(\w{4})", text)
    if entry_m or exit_m:
        entry_fuel = None
        exit_fuel = None
        if entry_m:
            entry_line = text[entry_m.start():].split("\n")[0]
            entry_fuel = _last_float(entry_line)
        if exit_m:
            exit_line = text[exit_m.start():].split("\n")[0]
            exit_fuel = _last_float(exit_line)
        return [ETOPSSector(
            sector_number=1,
            entry_icao=entry_m.group(2) if entry_m else None,
            entry_eet=entry_m.group(1) if entry_m else None,
            entry_fuel=entry_fuel,
            exit_icao=exit_m.group(2) if exit_m else None,
            exit_eet=exit_m.group(1) if exit_m else None,
            exit_fuel=exit_fuel,
            alternates=_etp_alternates(text),
        )]
    return []


def _last_float(line: str) -> float | None:
    nums = re.findall(r"\d+\.\d+", line)
    return float(nums[-1]) if nums else None


def _etp_alternates(text: str) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for m in re.finditer(
        r"ETP\s+[\d.]+\s+[NS][\d.]+\s+(\w{4})[^\n]*(?:\n\s+\S+\s+(\w{4}))?",
        text,
    ):
        for icao in (m.group(1), m.group(2)):
            if icao and icao not in seen:
                seen.add(icao)
                result.append(icao)
    return result


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
