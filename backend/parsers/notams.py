from __future__ import annotations
import re
from models.briefing import NOTAMData, NOTAMItem, AirportNotamBlock, FIRNotamBlock


HIGH_KEYWORDS = [
    "rwy", "runway", "clsd", "closed", "not avbl", "suspended",
    "ils", "rnp", "apch", "approach", "sid", "star",
    "gps", "gnss", "interference",
    "do not", "not plan to arrive",
    "missed approach",
]

MEDIUM_KEYWORDS = [
    "twy", "taxiway", "stand", "downgraded",
    "papi", "meht", "lighting", "lgt",
    "stopbar", "stop bar",
    "wip", "works",
]


def parse_notams(pages: list[str], fir_sequence: list[str]) -> NOTAMData:
    notam_pages = _find_notam_pages(pages)
    if not notam_pages:
        return NOTAMData()

    notam_text = "\n".join(notam_pages)
    sections = _split_all_sections(notam_text)

    departure_notams = _parse_section_notams(sections.get("DEPARTURE", ""), "DEPARTURE")
    destination_notams = _parse_section_notams(sections.get("DESTINATION", ""), "DESTINATION")

    alternate_blocks = _parse_per_airport_section(sections.get("ALTERNATE", ""), "ALTERNATE")

    enroute_airport_blocks: list[AirportNotamBlock] = []
    for key in ("ENROUTE_AIRPORT", "ETOPS_SUITABLE", "ETOPS_AVAILABLE"):
        enroute_airport_blocks.extend(
            _parse_per_airport_section(sections.get(key, ""), "ENROUTE")
        )
    seen_icao: set[str] = set()
    deduped: list[AirportNotamBlock] = []
    for block in enroute_airport_blocks:
        if block.icao in seen_icao:
            existing = next(b for b in deduped if b.icao == block.icao)
            existing_refs = {n.reference for n in existing.notams}
            for n in block.notams:
                if n.reference not in existing_refs:
                    existing.notams.append(n)
        else:
            seen_icao.add(block.icao)
            deduped.append(block)
    enroute_airport_blocks = deduped

    fir_notams: list[NOTAMItem] = []
    for key in ("AREA_DEP_DEST", "AREA_DEST_ALT", "EXT_DEPARTURE", "EXT_DESTINATION", "EXT_ALTERNATE"):
        fir_notams.extend(_parse_section_notams(sections.get(key, ""), "FIR"))

    enroute_fir_blocks = _build_enroute_blocks(fir_sequence, fir_notams)

    return NOTAMData(
        departure=departure_notams,
        destination=destination_notams,
        alternates=alternate_blocks,
        enroute_airports=enroute_airport_blocks,
        enroute=enroute_fir_blocks,
    )


def _find_notam_pages(pages: list[str]) -> list[str]:
    result = []
    in_notams = False
    for page in pages:
        if "LIDO-NOTAM-BULLETIN" in page or "NOTAMS" in page:
            in_notams = True
        if in_notams:
            if "END OF LIDO-NOTAM-BULLETIN" in page:
                result.append(page)
                break
            result.append(page)
    return result


def _split_all_sections(text: str) -> dict[str, str]:
    markers = [
        ("DEPARTURE", r"DEPARTURE\s+AIRPORT"),
        ("DESTINATION", r"DESTINATION\s+AIRPORT"),
        ("ALTERNATE", r"DESTINATION\s+ALTERNATE(?:\(S\))?"),
        ("ETOPS_SUITABLE", r"ETOPS\s+SUITABLE\s+ENROUTE\s+AIRPORT(?:\(S\))?"),
        ("ETOPS_AVAILABLE", r"ETOPS\s+AVAILABLE\s+ENROUTE\s+AIRPORT(?:\(S\))?"),
        ("ENROUTE_AIRPORT", r"ENROUTE\s+AIRPORT(?:\(S\))?"),
        ("EXT_DEPARTURE", r"EXTENDED\s+AREA\s+AROUND\s+DEPARTURE"),
        ("AREA_DEP_DEST", r"AREA\s+ENROUTE\s+DEPARTURE\s*-\s*DESTINATION"),
        ("EXT_DESTINATION", r"EXTENDED\s+AREA\s+AROUND\s+DESTINATION(?!\s+ALTERNATE)"),
        ("AREA_DEST_ALT", r"AREA\s+ENROUTE\s+DESTINATION\s*-\s*DESTINATION\s+ALTERNATE"),
        ("EXT_ALTERNATE", r"EXTENDED\s+AREA\s+AROUND\s+DESTINATION\s+ALTERNATE"),
        ("ENROUTE_FIR", r"(?<!AROUND\s)ENROUTE(?!\s+AIRPORT)(?!\s+DEPARTURE)(?!\s+DESTINATION)"),
    ]

    eq_line = r"={3,}"
    positions: list[tuple[str, int]] = []
    for name, pattern in markers:
        full = eq_line + r"\s*\n\s*" + pattern + r"\s*\n\s*" + eq_line
        for m in re.finditer(full, text):
            positions.append((name, m.end()))

    positions.sort(key=lambda x: x[1])

    sections: dict[str, str] = {}
    for i, (name, start) in enumerate(positions):
        end = positions[i + 1][1] if i + 1 < len(positions) else len(text)
        section_text = text[start:end]
        next_eq = re.search(r"={3,}\s*\n", section_text)
        if next_eq:
            section_text = section_text[:next_eq.start()]
        if name in sections:
            sections[name] += "\n" + section_text
        else:
            sections[name] = section_text

    return sections


def _parse_per_airport_section(text: str, category: str) -> list[AirportNotamBlock]:
    if not text.strip():
        return []

    blocks: list[AirportNotamBlock] = []
    airport_splits = re.split(r"\n(?=[A-Z]{4}\s+/\w{3}\s+)", text)

    for chunk in airport_splits:
        header = re.match(r"([A-Z]{4})\s+/\w{3}\s+(.*?)(?:\s*-\s*DETAILED INFO)?\s*$", chunk, re.MULTILINE)
        if not header:
            continue

        icao = header.group(1)
        name = header.group(2).strip()
        notams = _parse_section_notams(chunk, category)

        blocks.append(AirportNotamBlock(
            icao=icao,
            name=name,
            notams=notams,
        ))

    return blocks


def _parse_section_notams(text: str, category: str) -> list[NOTAMItem]:
    if not text.strip():
        return []

    notams: list[NOTAMItem] = []

    pattern = re.compile(
        r"(\d[A-Z]\d+/\d{2}|SX\d+/\d{2}|CO\d+/\d{2}|1W\d+/\d{2})\s+VALID:\s+"
        r"(\d{2}-\w{3}-\d{2}\s+\d{4}|\d{2}\s*-\s*\w{3}\s*-\s*\d{2}\s+\d{4})\s*-\s*"
        r"(.*?)\n(.*?)(?=(?:\d[A-Z]\d+/\d{2}|SX\d+/\d{2}|CO\d+/\d{2}|1W\d+/\d{2})\s+VALID:|"
        r"\+{5,}|={5,}|Page\s+\d+\s+of\s+\d+|\Z)",
        re.DOTALL,
    )

    for m in pattern.finditer(text):
        ref = m.group(1)
        valid_from = m.group(2).strip()
        valid_to = m.group(3).strip()
        body = m.group(4).strip()

        body = re.sub(r"Page\s+\d+\s+of\s+\d+", "", body).strip()
        body = re.sub(r"QTR?\s+\d+/\d+\w+\d+/\w+-\w+\s+Reg:\w+\s+OFP:\S+", "", body).strip()

        subcategory = _classify_subcategory(text[:m.start()], body)
        relevance = _score_relevance(body)
        summary = _generate_summary(body)

        notams.append(NOTAMItem(
            reference=ref,
            valid_from=valid_from,
            valid_to=valid_to,
            category=category,
            subcategory=subcategory,
            text=body,
            relevance=relevance,
            summary=summary,
        ))

    return notams


def _classify_subcategory(context_before: str, body: str) -> str:
    last_header = ""
    for m in re.finditer(r"\+{5,}\s*(\w[\w\s/]+?)\s*\+{5,}", context_before):
        last_header = m.group(1).strip()

    if "RUNWAY" in last_header:
        return "RUNWAY"
    if "APPROACH" in last_header:
        return "APPROACH"
    if "SID" in last_header or "STAR" in last_header:
        return "SID/STAR"
    if "AIRPORT" in last_header:
        return "AIRPORT"

    lower = body.lower()
    if any(kw in lower for kw in ["rwy", "runway", "tora", "toda", "asda", "lda"]):
        return "RUNWAY"
    if any(kw in lower for kw in ["ils", "rnp apch", "approach", "missed approach"]):
        return "APPROACH"
    if any(kw in lower for kw in ["sid", "star", "departure procedure"]):
        return "SID/STAR"
    if any(kw in lower for kw in ["twy", "taxiway", "stand"]):
        return "TAXIWAY"

    return "GENERAL"


def _score_relevance(body: str) -> str:
    lower = body.lower()
    for kw in HIGH_KEYWORDS:
        if kw in lower:
            return "HIGH"
    for kw in MEDIUM_KEYWORDS:
        if kw in lower:
            return "MEDIUM"
    return "LOW"


def _generate_summary(body: str) -> str:
    lines = [l.strip() for l in body.split("\n") if l.strip()]
    if not lines:
        return ""
    first_line = lines[0]
    if len(first_line) > 120:
        return first_line[:117] + "..."
    return first_line


def _build_enroute_blocks(
    fir_sequence: list[str],
    fir_notams: list[NOTAMItem],
) -> list[FIRNotamBlock]:
    blocks: list[FIRNotamBlock] = []

    for fir_label in fir_sequence:
        icao_match = re.search(r"\((\w{4})\)", fir_label)
        if not icao_match:
            continue
        fir_icao = icao_match.group(1)
        fir_name = fir_label.split("(")[0].strip()

        matched = [n for n in fir_notams if _notam_matches_fir(n, fir_icao)]

        if matched:
            blocks.append(FIRNotamBlock(
                fir_icao=fir_icao,
                fir_name=fir_name,
                notams=matched,
            ))

    return blocks


def _notam_matches_fir(notam: NOTAMItem, fir_icao: str) -> bool:
    return fir_icao.lower() in notam.text.lower() or fir_icao[:2].lower() in notam.text[:20].lower()
