from __future__ import annotations
import re
from models.briefing import TakeoffData, FlightInfo


def parse_takeoff(pages: list[str], flight_info: FlightInfo) -> TakeoffData:
    text = "\n".join(pages[:5])

    toc_temp_match = re.search(r"TOC\s+TEMP\s+([MP]\d+)", text)
    toc_temp = toc_temp_match.group(1) if toc_temp_match else None

    dep_wx_match = re.search(
        r"(?:OTHH|" + re.escape(flight_info.departure_icao) + r")\s+WX/ATIS",
        text,
    )

    wind_match = re.search(
        r"SA\s+\d+\s+(\d{5}(?:G\d+)?KT)",
        "\n".join(pages[:25]),
    )
    wind_at_dep = None
    for page in pages:
        if "DEPARTURE AIRPORT:" in page:
            w = re.search(r"SA\s+\d+\s+(\d{5}(?:G\d+)?KT|VRB\d+KT)", page)
            if w:
                wind_at_dep = w.group(1)
            break

    return TakeoffData(
        runway=flight_info.departure_runway,
        sid=flight_info.sid,
        v1="Not available — use EFB/OPT",
        vr="Not available — use EFB/OPT",
        v2="Not available — use EFB/OPT",
        flaps="Not available — use EFB/OPT",
        toc_temperature=toc_temp,
        wind_at_departure=wind_at_dep,
    )
