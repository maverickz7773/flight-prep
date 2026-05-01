from __future__ import annotations
import pdfplumber

from models.briefing import BriefingData, OperationalInsight
from parsers.flight_info import parse_flight_info
from parsers.fuel import parse_fuel
from parsers.weights import parse_weights
from parsers.route import parse_route
from parsers.etops import parse_etops
from parsers.weather import parse_weather
from parsers.notams import parse_notams
from parsers.crew_alerts import parse_crew_alerts
from parsers.takeoff import parse_takeoff
from parsers.mel import parse_mel


def extract_pages(pdf_path: str) -> list[str]:
    pages: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages.append(text)
    return pages


def parse_ofp(pdf_path: str) -> BriefingData:
    pages = extract_pages(pdf_path)
    raw_text = "\n".join(pages)

    flight_info = parse_flight_info(pages)
    fuel = parse_fuel(pages)
    weights = parse_weights(pages)
    route = parse_route(pages)
    etops = parse_etops(pages)
    takeoff = parse_takeoff(pages, flight_info)
    arrival_info = parse_route_arrival(pages)
    weather = parse_weather(pages, route.fir_sequence)
    notams = parse_notams(pages, route.fir_sequence)
    crew_alerts = parse_crew_alerts(pages)
    mel_items = parse_mel(pages, pdf_path)

    enroute_airports: list[str] = []
    for fir_block in weather.enroute:
        for airport in fir_block.airports:
            if airport.icao not in enroute_airports:
                enroute_airports.append(airport.icao)
    for alt_wx in weather.alternates:
        if alt_wx.icao not in enroute_airports:
            enroute_airports.append(alt_wx.icao)
    if etops:
        for alt in etops.suitable_alternates:
            if alt.icao not in enroute_airports:
                enroute_airports.append(alt.icao)
    for alt in arrival_info.alternates:
        if alt.icao not in enroute_airports:
            enroute_airports.append(alt.icao)

    insights = generate_insights(fuel, weights, etops, weather, notams, route)

    return BriefingData(
        flight_info=flight_info,
        fuel=fuel,
        weights=weights,
        takeoff=takeoff,
        route=route,
        etops=etops,
        arrival=arrival_info,
        weather=weather,
        notams=notams,
        mel_items=mel_items,
        crew_alerts=crew_alerts,
        operational_insights=insights,
        enroute_airport_list=enroute_airports,
    )


def parse_route_arrival(pages: list[str]):
    from parsers.arrival import parse_arrival
    return parse_arrival(pages)


def generate_insights(fuel, weights, etops, weather, notams, route) -> list[OperationalInsight]:
    insights: list[OperationalInsight] = []

    if weights.elwt_pct and weights.elwt_pct > 95:
        insights.append(OperationalInsight(
            severity="CAUTION",
            text=f"Landing weight {weights.elwt_pct:.1f}% of MLWT — monitor fuel burn",
        ))

    if fuel.extra and fuel.extra > 20000:
        insights.append(OperationalInsight(
            severity="INFO",
            text=f"Heavy extra fuel ({fuel.extra:,} kg) — likely tankering",
        ))

    sigmet_count = sum(len(fir.sigmets) for fir in weather.enroute)
    if sigmet_count > 0:
        insights.append(OperationalInsight(
            severity="CAUTION",
            text=f"{sigmet_count} SIGMET(s) along route — review enroute weather by FIR",
        ))

    if etops and etops.entry:
        insights.append(OperationalInsight(
            severity="INFO",
            text="ETOPS sector — brief diversion alternates and procedures",
        ))

    for notam in notams.departure:
        lower = notam.text.lower()
        if "gps" in lower or "gnss" in lower:
            insights.append(OperationalInsight(
                severity="CAUTION",
                text="GPS/GNSS interference risk at departure — review QRH procedures",
            ))
            break

    for notam in notams.departure:
        lower = notam.text.lower()
        if "ils" in lower and "not avbl" in lower:
            insights.append(OperationalInsight(
                severity="CAUTION",
                text="ILS not available at departure — non-precision approaches only",
            ))
            break

    for notam in notams.destination:
        lower = notam.text.lower()
        if "slot" in lower or "arrive earlier" in lower.replace("do not ", ""):
            if "do not" in lower or "not plan" in lower:
                insights.append(OperationalInsight(
                    severity="CAUTION",
                    text="Arrival slot restriction at destination — check STA constraints",
                ))
                break

    return insights
