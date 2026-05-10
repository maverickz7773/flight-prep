from __future__ import annotations
import re
from models.briefing import WeatherData, AirportWeather, SIGMET, FIRWeatherBlock

_OFP_PAGE_RE = re.compile(r"(?m)^Page\s+\d+\s+of\s+\d+\s*$")
_OFP_HEADER_RE = re.compile(r"(?m)^QTR\s+.+?OFP:\d+/\d+/\d+\s*$")

FIR_ICAO_TO_NAME = {
    "OBBB": "Bahrain",
    "OMAE": "Emirates",
    "OOMM": "Muscat",
    "VABF": "Mumbai",
    "VIDP": "Delhi",
    "VOMF": "Chennai",
    "WIIF": "Jakarta",
    "WSJC": "Singapore",
    "WMFC": "Kuala Lumpur",
    "VTBB": "Bangkok",
    "OEJD": "Jeddah",
    "OPKC": "Karachi",
}


def parse_weather(pages: list[str], fir_sequence: list[str]) -> WeatherData:
    wx_pages = _find_wx_pages(pages)
    wx_text = "\n".join(wx_pages) if wx_pages else ""

    departure = _parse_airport_weather(wx_text, "DEPARTURE AIRPORT")
    destination = _parse_airport_weather(wx_text, "DESTINATION AIRPORT")
    alternates = _parse_alternates_weather(wx_text)
    sigmets = _parse_sigmets(wx_text)

    enroute_airports = _parse_enroute_airports(wx_text)

    enroute_fir_blocks = _build_fir_blocks(fir_sequence, sigmets, enroute_airports)

    return WeatherData(
        departure=departure,
        destination=destination,
        alternates=alternates,
        enroute=enroute_fir_blocks,
    )


def _find_wx_pages(pages: list[str]) -> list[str]:
    result = []
    in_wx = False
    for page in pages:
        if "WX FORECAST" in page or "LIDO/WEATHER SERVICE" in page:
            in_wx = True
        if in_wx:
            result.append(page)
            if "AIRPORTLIST ENDED" in page or "NOTAMS" in page:
                break
    return result


def _parse_airport_weather(text: str, section_marker: str) -> AirportWeather | None:
    section_match = re.search(
        rf"{section_marker}:\s*\n(\w{{4}})/(\w+)\s+(.*?)(?=\n(?:DESTINATION|FUEL|ENROUTE|Space|AIRPORTLIST|$))",
        text,
        re.DOTALL,
    )
    if not section_match:
        return None

    icao = section_match.group(1)
    name = section_match.group(3).split("\n")[0].strip()
    block = _sanitize_weather_block(section_match.group(0))

    metar = _extract_metar(block)
    taf = _extract_taf(block)

    return AirportWeather(icao=icao, name=name, metar=metar, taf=taf)


def _parse_alternates_weather(text: str) -> list[AirportWeather]:
    results: list[AirportWeather] = []

    alt_section = re.search(
        r"DESTINATION ALTERNATE:\s*\n(.*?)(?=FUEL ENROUTE|ENROUTE AIRPORT|DEPARTURE AIRPORT|Space|AIRPORTLIST)",
        text,
        re.DOTALL,
    )
    if not alt_section:
        return results

    alt_text = alt_section.group(1)

    for m in re.finditer(r"(\w{4})/(\w+)\s+(.*?)(?=\n\w{4}/|\Z)", alt_text, re.DOTALL):
        icao = m.group(1)
        name = m.group(3).split("\n")[0].strip()
        block = _sanitize_weather_block(m.group(0))
        metar = _extract_metar(block)
        taf = _extract_taf(block)
        results.append(AirportWeather(icao=icao, name=name, metar=metar, taf=taf))

    return results


def _parse_enroute_airports(text: str) -> list[AirportWeather]:
    results: list[AirportWeather] = []

    en_section = re.search(
        r"ENROUTE AIRPORT\(S\):\s*\n(.*?)(?=DEPARTURE AIRPORT|Space|AIRPORTLIST)",
        text,
        re.DOTALL,
    )
    fuel_section = re.search(
        r"FUEL ENROUTE AIRPORT:\s*\n(.*?)(?=ENROUTE AIRPORT|DEPARTURE AIRPORT|Space|AIRPORTLIST)",
        text,
        re.DOTALL,
    )

    for section in [fuel_section, en_section]:
        if not section:
            continue
        sec_text = section.group(1)
        for m in re.finditer(r"(\w{4})/(\w+)\s+(.*?)(?=\n\w{4}/|\Z)", sec_text, re.DOTALL):
            icao = m.group(1)
            name = m.group(3).split("\n")[0].strip()
            block = _sanitize_weather_block(m.group(0))
            metar = _extract_metar(block)
            taf = _extract_taf(block)
            results.append(AirportWeather(icao=icao, name=name, metar=metar, taf=taf))

    return results


def _parse_sigmets(text: str) -> list[SIGMET]:
    results: list[SIGMET] = []
    sigmet_section = re.search(r"SIGMETs:\s*\n(.*?)(?=Tropical Cyclone|Volcanic Ash|DESTINATION|$)", text, re.DOTALL)
    if not sigmet_section:
        return results

    sec_text = sigmet_section.group(1)
    if "No Wx data available" in sec_text and len(sec_text.strip()) < 30:
        return results

    entries = re.split(r"\n(?=\w{4}\s+[A-Z].*?(?:FIR|UIR)\s*$)", sec_text, flags=re.MULTILINE)

    for entry in entries:
        entry = entry.strip()
        if not entry or "No Wx data" in entry:
            continue

        header_match = re.match(r"(\w{4})\s+(.*?)(?:FIR|UIR)\s*$", entry, re.MULTILINE)
        if not header_match:
            continue

        fir_icao = header_match.group(1)
        fir_name = header_match.group(2).strip() + " FIR"

        raw_lines = entry[header_match.end():].strip()
        raw = raw_lines.rstrip("=").strip()

        phenomenon = None
        if "EMBD TS" in raw:
            phenomenon = "Embedded Thunderstorms"
        elif "SEV TURB" in raw:
            phenomenon = "Severe Turbulence"
        elif "SEV ICE" in raw:
            phenomenon = "Severe Icing"

        top_m = re.search(r"TOP\s+(?:ABV\s+)?FL(\d+)", raw)
        top = f"FL{top_m.group(1)}" if top_m else None

        results.append(SIGMET(
            fir_icao=fir_icao,
            fir_name=fir_name,
            raw_text=raw,
            phenomenon=phenomenon,
            top=top,
        ))

    return results


def _build_fir_blocks(
    fir_sequence: list[str],
    sigmets: list[SIGMET],
    enroute_airports: list[AirportWeather],
) -> list[FIRWeatherBlock]:
    blocks: list[FIRWeatherBlock] = []

    for fir_label in fir_sequence:
        icao_match = re.search(r"\((\w{4})\)", fir_label)
        if not icao_match:
            continue
        fir_icao = icao_match.group(1)
        fir_name = fir_label.split("(")[0].strip()

        fir_sigmets = [s for s in sigmets if s.fir_icao == fir_icao]

        fir_airports = _match_airports_to_fir(fir_icao, enroute_airports)

        if fir_sigmets or fir_airports:
            blocks.append(FIRWeatherBlock(
                fir_icao=fir_icao,
                fir_name=fir_name,
                sigmets=fir_sigmets,
                airports=fir_airports,
            ))

    return blocks


def _match_airports_to_fir(fir_icao: str, airports: list[AirportWeather]) -> list[AirportWeather]:
    fir_prefix_map = {
        "OBBB": ["OB", "OT"],
        "OMAE": ["OM"],
        "OOMM": ["OO"],
        "OEJD": ["OE"],
        "OPKC": ["OP"],
        "VABF": ["VA"],
        "VIDP": ["VI"],
        "VOMF": ["VO"],
        "VOCI": ["VO"],
        "WIIF": ["WI", "WA"],
        "WSJC": ["WS"],
        "WMFC": ["WM"],
        "VTBB": ["VT"],
        "VCBI": ["VC"],
    }

    prefixes = fir_prefix_map.get(fir_icao, [fir_icao[:2]])
    return [a for a in airports if any(a.icao.startswith(p) for p in prefixes)]


def _extract_metar(block: str) -> str | None:
    m = re.search(r"SA\s+(\d{6}\s+.*?)=", block, re.DOTALL)
    if m:
        return m.group(1).replace("\n", " ").strip()
    return None


def _extract_taf(block: str) -> str | None:
    matches = re.findall(r"FT\s+(\d{6}\s+.*?)=", block, re.DOTALL)
    if not matches:
        return None

    # When a forecast spans a PDF page break, the block may contain an older partial
    # FT section followed by the continued/latest full FT section. Prefer the last one
    # after sanitizing page footer/header artifacts.
    return matches[-1].replace("\n", " ").strip()


def _sanitize_weather_block(block: str) -> str:
    block = _OFP_PAGE_RE.sub("", block)
    block = _OFP_HEADER_RE.sub("", block)
    block = re.sub(r"\n{2,}", "\n", block)
    return block.strip()
