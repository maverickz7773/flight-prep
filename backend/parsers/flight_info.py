from __future__ import annotations
import re
from models.briefing import FlightInfo

ICAO_UTC_OFFSET: dict[str, str] = {
    "OTHH": "+3", "OTBD": "+3",
    "WMKK": "+8", "WMKJ": "+8", "WMKP": "+8",
    "WSSS": "+8",
    "WIII": "+7", "WADD": "+8", "WIMM": "+7",
    "VTBS": "+7", "VTBD": "+7", "VTSG": "+7", "VTSP": "+7",
    "VHHH": "+8",
    "RPLL": "+8",
    "RKSI": "+9",
    "RJTT": "+9", "RJAA": "+9",
    "VOMM": "+5:30", "VOBL": "+5:30", "VOCI": "+5:30", "VIDP": "+5:30",
    "VABB": "+5:30", "VCRI": "+5:30", "VCBI": "+5:30",
    "OPKR": "+5", "OPLA": "+5", "OPRN": "+5",
    "OEJN": "+3", "OERK": "+3", "OEDF": "+3",
    "OMDB": "+4", "OMAD": "+4", "OMSJ": "+4",
    "OOMS": "+4", "OOSA": "+4",
    "OKBK": "+3",
    "OBIC": "+3", "OBBI": "+3",
    "EGLL": "+0", "EGLC": "+0", "EGKK": "+0",
    "LFPG": "+1", "LFPO": "+1",
    "EDDF": "+1", "EDDM": "+1",
    "KJFK": "-5", "KLAX": "-8", "KORD": "-6", "KATL": "-5",
    "CYYZ": "-5", "CYVR": "-8",
    "YSSY": "+10", "YMML": "+10",
    "FAOR": "+2", "FACT": "+2",
    "SBGR": "-3",
    "LEMD": "+1", "LEBL": "+1",
    "LIRF": "+1", "LIMC": "+1",
    "LTFM": "+3",
    "UUEE": "+3", "UUDD": "+3",
    "ZBAA": "+8", "ZSPD": "+8", "ZGGG": "+8",
    "VDPP": "+7",
    "VLVT": "+7",
    "VRMM": "+5",
}


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

    cruise_levels: list[str] = []
    cl_line = re.search(r"(FL\d{3}(?:\s+\w+/FL\d{3})+)", atc_block or text)
    if cl_line:
        cruise_levels = [f"FL{fl}" for fl in re.findall(r"FL(\d{3})", cl_line.group(1))]

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

    sid = None
    star = None

    # SID: found in waypoint pages as the airway name near departure runway
    for page in pages:
        dep_rwy_pattern = re.search(
            r"\w{4}/(\d{2}[LRC]?)\s+\d{3}\s+\.\.\.\.",
            page,
        )
        if dep_rwy_pattern:
            sid_match = re.search(
                r"(\w+\d+[A-Z])\s+\d{3}\s+CLB",
                page,
            )
            if sid_match:
                sid = sid_match.group(1)
            break

    # STAR: found on the last route leg page, airway name on the line before ICAO/RWY
    # Skip alternate route pages ("DESTINATION TO ALTERNATE")
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

    if not star and route_string:
        parts = route_string.split()
        if parts:
            star_candidate = parts[-1]
            if re.match(r"[A-Z]+\d+[A-Z]", star_candidate):
                star = star_candidate

    gnd_dist_match = re.search(r"GND\s+DIST\s+(\d+)", text)
    ground_distance = int(gnd_dist_match.group(1)) if gnd_dist_match else None

    wc_match = re.search(r"WC\s+([PM]\d+)", text)
    wind_component = wc_match.group(1) if wc_match else None

    dep_utc = ICAO_UTC_OFFSET.get(dep_icao)
    arr_utc = ICAO_UTC_OFFSET.get(arr_icao)

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
