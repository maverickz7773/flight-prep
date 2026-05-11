from __future__ import annotations
import re
from models.briefing import ETOPSInfo, ETOPSPoint, ETOPSAlternate, ETOPSSector

_SECTOR_MARKER_RE = re.compile(r"^(ENTRY|EXIT)(\d*)\b", re.MULTILINE)
_ICAO_TOKEN_RE = re.compile(r"\b([A-Z]{4})\b")


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
    sector_section = text.split("ETOPS SUITABLE ALTN AIRPORTS:", 1)[0]
    marker_matches = list(_SECTOR_MARKER_RE.finditer(sector_section))
    if not marker_matches:
        return []

    sectors_by_number: dict[int, dict[str, object | None]] = {}

    for i, marker in enumerate(marker_matches):
        start = marker.start()
        end = marker_matches[i + 1].start() if i + 1 < len(marker_matches) else len(sector_section)
        block = sector_section[start:end].strip()
        kind = marker.group(1).lower()
        raw_number = marker.group(2)
        sector_number = int(raw_number) if raw_number else 1

        parsed = _parse_sector_marker_block(block)
        sector = sectors_by_number.setdefault(
            sector_number,
            {
                "sector_number": sector_number,
                "entry_icao": None,
                "entry_eet": None,
                "entry_fuel": None,
                "exit_icao": None,
                "exit_eet": None,
                "exit_fuel": None,
                "alternates": [],
            },
        )

        sector[f"{kind}_icao"] = parsed["icao"]
        sector[f"{kind}_eet"] = parsed["eet"]
        sector[f"{kind}_fuel"] = parsed["fuel"]

    ordered_numbers = sorted(sectors_by_number)
    sectors: list[ETOPSSector] = []
    for idx, sector_number in enumerate(ordered_numbers):
        sector = sectors_by_number[sector_number]
        entry_marker = next(
            (m for m in marker_matches if m.group(1) == "ENTRY" and (int(m.group(2)) if m.group(2) else 1) == sector_number),
            None,
        )
        if entry_marker:
            entry_start = entry_marker.start()
            next_entry = next(
                (
                    m for m in marker_matches
                    if m.start() > entry_start and m.group(1) == "ENTRY"
                ),
                None,
            )
            sector_end = next_entry.start() if next_entry else len(sector_section)
            sector["alternates"] = _etp_alternates(sector_section[entry_start:sector_end])

        sectors.append(ETOPSSector(**sector))

    return sectors


def _parse_sector_marker_block(block: str) -> dict[str, str | float | None]:
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    if not lines:
        return {"icao": None, "eet": None, "fuel": None}

    first_line = lines[0]
    parts = first_line.split()
    eet = parts[1] if len(parts) > 1 else None
    fuel = _last_float(first_line)

    icao = None
    for line in lines[1:]:
        token_match = _ICAO_TOKEN_RE.search(line)
        if token_match:
            icao = token_match.group(1)
            break

    return {
        "icao": icao,
        "eet": eet,
        "fuel": fuel,
    }


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
