from __future__ import annotations
from datetime import datetime
import re
from zoneinfo import ZoneInfo

from models.briefing import FlightInfo
from parsers.procedures import (
    extract_sid_from_route_pages,
    extract_star_from_route_pages,
    is_procedure_token,
)

ICAO_TIMEZONES: dict[str, str] = {
    "OTHH": "Asia/Qatar",
    "OTBD": "Asia/Qatar",
    "WMKK": "Asia/Kuala_Lumpur",
    "WMKJ": "Asia/Kuala_Lumpur",
    "WMKP": "Asia/Kuala_Lumpur",
    "WSSS": "Asia/Singapore",
    "WIII": "Asia/Jakarta",
    "WADD": "Asia/Makassar",
    "WIMM": "Asia/Jakarta",
    "VTBS": "Asia/Bangkok",
    "VTBD": "Asia/Bangkok",
    "VTSG": "Asia/Bangkok",
    "VTSP": "Asia/Bangkok",
    "VHHH": "Asia/Hong_Kong",
    "RPLL": "Asia/Manila",
    "RKSI": "Asia/Seoul",
    "RJTT": "Asia/Tokyo",
    "RJAA": "Asia/Tokyo",
    "VOMM": "Asia/Kolkata",
    "VOBL": "Asia/Kolkata",
    "VOCI": "Asia/Kolkata",
    "VIDP": "Asia/Kolkata",
    "VABB": "Asia/Kolkata",
    "VCRI": "Asia/Kolkata",
    "VCBI": "Asia/Colombo",
    "OPKR": "Asia/Karachi",
    "OPLA": "Asia/Karachi",
    "OPRN": "Asia/Karachi",
    "OEJN": "Asia/Riyadh",
    "OERK": "Asia/Riyadh",
    "OEDF": "Asia/Riyadh",
    "OMDB": "Asia/Dubai",
    "OMAD": "Asia/Dubai",
    "OMSJ": "Asia/Dubai",
    "OOMS": "Asia/Muscat",
    "OOSA": "Asia/Muscat",
    "OKBK": "Asia/Kuwait",
    "OBIC": "Asia/Qatar",
    "OBBI": "Asia/Bahrain",
    "OLBA": "Asia/Beirut",
    "EGLL": "Europe/London",
    "EGLC": "Europe/London",
    "EGKK": "Europe/London",
    "LFPG": "Europe/Paris",
    "LFPO": "Europe/Paris",
    "EDDF": "Europe/Berlin",
    "EDDM": "Europe/Berlin",
    "KJFK": "America/New_York",
    "KLAX": "America/Los_Angeles",
    "KSEA": "America/Los_Angeles",
    "KORD": "America/Chicago",
    "KATL": "America/New_York",
    "KIAD": "America/New_York",
    "CYYZ": "America/Toronto",
    "CYVR": "America/Vancouver",
    "YSSY": "Australia/Sydney",
    "YMML": "Australia/Melbourne",
    "FAOR": "Africa/Johannesburg",
    "FACT": "Africa/Johannesburg",
    "SBGR": "America/Sao_Paulo",
    "LEMD": "Europe/Madrid",
    "LEBL": "Europe/Madrid",
    "LIRF": "Europe/Rome",
    "LIMC": "Europe/Rome",
    "LTFM": "Europe/Istanbul",
    "UUEE": "Europe/Moscow",
    "UUDD": "Europe/Moscow",
    "ZBAA": "Asia/Shanghai",
    "ZSPD": "Asia/Shanghai",
    "ZGGG": "Asia/Shanghai",
    "VDPP": "Asia/Phnom_Penh",
    "VDTI": "Asia/Ho_Chi_Minh",
    "VLVT": "Asia/Vientiane",
    "VRMM": "Asia/Yangon",
}


def _extract_cruise_levels(
    block: str,
) -> list[str]:
    lines = block.splitlines()
    cruise_levels: list[str] = []
    in_route_section = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("ATC CLEARANCE"):
            in_route_section = True
            continue
        if not in_route_section:
            continue
        if stripped.startswith("FUEL TIME"):
            break
        if "FL" not in stripped or "STA " in stripped:
            continue
        for fl in re.findall(r"FL\d{3}", stripped):
            cruise_levels.append(fl)

    return cruise_levels


def _format_utc_offset(offset_seconds: int) -> str:
    total_minutes = offset_seconds // 60
    sign = "+" if total_minutes >= 0 else "-"
    total_minutes = abs(total_minutes)
    hours, minutes = divmod(total_minutes, 60)
    if minutes == 0:
        return f"{sign}{hours}"
    return f"{sign}{hours}:{minutes:02d}"


def _get_utc_offset(icao: str, flight_date: str) -> str | None:
    timezone_name = ICAO_TIMEZONES.get(icao)
    if not timezone_name or not flight_date:
        return None

    try:
        flight_dt = datetime.strptime(flight_date, "%d%b%y")
        tz = ZoneInfo(timezone_name)
        offset = flight_dt.replace(tzinfo=tz).utcoffset()
    except Exception:
        return None

    if offset is None:
        return None

    return _format_utc_offset(int(offset.total_seconds()))


def parse_flight_info(pages: list[str]) -> FlightInfo:
    text = "\n".join(pages[:5])

    header = re.search(
        r"(\w{2,3})\s+(\d+)/(\d{2}\w{3}\d{2})/(\w{3,4})-(\w{3,4})\s+Reg:(\w+)",
        text,
    )
    flight_number = ""
    date = ""
    dep_icao = ""
    arr_icao = ""
    registration = ""
    callsign: str | None = None
    if header:
        airline_code = header.group(1)
        flight_num = header.group(2)
        flight_number = f"QR{flight_num}" if airline_code in ("QTR", "QR") else f"{airline_code}{flight_num}"
        date = header.group(3)
        registration = header.group(6)

    callsign_match = re.search(r"PAGE\s+\d+/\d+\s+(\w+)/\w+\s+\d{2}\w{3}", text)
    if callsign_match:
        callsign = callsign_match.group(1)

    station_match = re.search(
        r"QR\d+\s+\d+\w+\s+(\w{4})/(\w{4})\s+\w+\s+\w+",
        text,
    )
    if station_match:
        dep_icao = station_match.group(1)
        arr_icao = station_match.group(2)
    elif header:
        h_dep = header.group(4)
        h_arr = header.group(5)
        if len(h_dep) == 4 and len(h_arr) == 4:
            dep_icao = h_dep
            arr_icao = h_arr

    aircraft = re.search(r"(B77W|B77L|B788|B789|A35K|A388|A333|A332|A321|A320)\s+\w+", text)
    aircraft_type = aircraft.group(1) if aircraft else ""

    etops_match = re.search(r"ETOPS[:\s]*(\d+)\s*MIN", text)
    etops_minutes = int(etops_match.group(1)) if etops_match else None

    ci_match = re.search(r"(?:SPEED\s+)?CI\s+(\d+)", text)
    cost_index = int(ci_match.group(1)) if ci_match else None

    std_match = re.search(r"STD\s+(\d{2}/\d{4})", text)
    std = std_match.group(1) if std_match else ""

    sta_match = re.search(r"STA\s+(\d{2}/\d{4})", text)
    sta = sta_match.group(1) if sta_match else ""

    blk_match = re.search(r"BLK\s+(\d{4})", text)
    block_time = blk_match.group(1) if blk_match else ""

    trip_time_match = re.search(r"TRIP\s+\d+\s+(\d{4})", text)
    trip_time = trip_time_match.group(1) if trip_time_match else ""

    disp_match = re.search(r"DISP:(\w+\s+\w+)", text)
    dispatcher = disp_match.group(1).strip() if disp_match else None

    pic_match = re.search(r"PIC[:\s]*([A-Z]+\s+[A-Za-z]+)", text)
    pic = pic_match.group(1).strip() if pic_match else None

    atc_block = ""
    for page in pages[:5]:
        if "ATC CLEARANCE" in page or re.search(r"\w{4}\s+\d{2}[LRC]?\s+\w+\s+\w+", page):
            atc_block = page
            break

    dep_rwy = None
    arr_rwy = None
    route_string = None

    route_match = re.search(
        r"(\w{4})\s+(\d{2}[LRC]?)\s+((?:[A-Z][A-Z0-9]+\s+)+)(\w{4})\s+(\d{2}[LRC]?)",
        atc_block or text,
    )
    if route_match:
        dep_rwy = route_match.group(2)
        arr_rwy = route_match.group(5)
        route_string = route_match.group(3).strip()

    cruise_levels = _extract_cruise_levels(atc_block or text)

    sid = extract_sid_from_route_pages(pages, dep_icao or None, dep_rwy)
    star = extract_star_from_route_pages(pages, arr_icao or None, arr_rwy)

    if not star and route_string:
        parts = route_string.split()
        if parts:
            star_candidate = parts[-1]
            if is_procedure_token(star_candidate):
                star = star_candidate

    gnd_dist_match = re.search(r"GND\s+DIST\s+(\d+)", text)
    ground_distance = int(gnd_dist_match.group(1)) if gnd_dist_match else None

    wc_match = re.search(r"WC\s+([PM]\d+)", text)
    wind_component = wc_match.group(1) if wc_match else None

    dep_utc = _get_utc_offset(dep_icao, date)
    arr_utc = _get_utc_offset(arr_icao, date)

    return FlightInfo(
        flight_number=flight_number,
        callsign=callsign,
        date=date,
        departure_icao=dep_icao,
        arrival_icao=arr_icao,
        aircraft_type=aircraft_type,
        registration=registration,
        etops_minutes=etops_minutes,
        cost_index=cost_index,
        std=std,
        sta=sta,
        block_time=block_time,
        trip_time=trip_time,
        departure_utc_offset=dep_utc,
        arrival_utc_offset=arr_utc,
        dispatcher=dispatcher,
        pic=pic,
        cruise_levels=cruise_levels,
        departure_runway=dep_rwy,
        arrival_runway=arr_rwy,
        sid=sid,
        star=star,
        route_string=route_string,
        ground_distance=ground_distance,
        wind_component=wind_component,
    )
