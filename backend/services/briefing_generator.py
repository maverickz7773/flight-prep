from __future__ import annotations
from models.briefing import BriefingData


def _ft(t: str | None) -> str:
    if not t or len(t) != 4:
        return ""
    return f" ({t[:2]}:{t[2:]})"


def generate_text_briefing(data: BriefingData) -> str:
    lines: list[str] = []
    fi = data.flight_info
    f = data.fuel
    w = data.weights
    t = data.takeoff
    r = data.route
    a = data.arrival

    lines.append("=" * 60)
    lines.append(f"  {fi.flight_number} / {fi.date}    {fi.departure_icao} → {fi.arrival_icao}")
    lines.append(f"  {fi.aircraft_type}  {fi.registration}")
    if data.mel_items:
        mel_refs = ", ".join(m.reference for m in data.mel_items)
        lines.append(f"  MEL/CDL: {mel_refs}")
    else:
        lines.append("  MEL/CDL: N/A")
    lines.append("=" * 60)

    lines.append("")
    lines.append("1. FLIGHT OVERVIEW")
    lines.append("-" * 40)
    dep_utc = f" (UTC{fi.departure_utc_offset})" if fi.departure_utc_offset else ""
    arr_utc = f" (UTC{fi.arrival_utc_offset})" if fi.arrival_utc_offset else ""
    lines.append(f"  STD: {fi.std}{dep_utc}    STA: {fi.sta}{arr_utc}")
    lines.append(f"  BLK: {fi.block_time}    TRIP: {fi.trip_time}")
    lines.append(f"  RWY: {fi.departure_runway or 'N/A'} → {fi.arrival_runway or 'N/A'}")
    lines.append(f"  SID: {fi.sid or 'N/A'}    STAR: {fi.star or 'N/A'}")
    lines.append(f"  CRUISE: {' → '.join(fi.cruise_levels) if fi.cruise_levels else 'N/A'}")
    lines.append(f"  CI: {fi.cost_index or 'N/A'}    ETOPS: {fi.etops_minutes or 'N/A'} MIN")
    lines.append(f"  GND DIST: {fi.ground_distance or 'N/A'} nm    WC: {fi.wind_component or 'N/A'}")

    lines.append("")
    lines.append("2. FUEL (KG)")
    lines.append("-" * 40)
    lines.append(f"  TAXI:  {f.taxi:>8,}{_ft(f.taxi_time)}    RAMP:  {f.ramp:>8,}{_ft(f.ramp_time)}")
    lines.append(f"  TRIP:  {f.trip:>8,}{_ft(f.trip_time)}    T/O:   {f.takeoff or 0:>8,}")
    lines.append(f"  CONT:  {f.contingency:>8,}{_ft(f.contingency_time)}    EXTRA: {f.extra:>8,}{_ft(f.extra_time)}")
    lines.append(f"  ALTN:  {f.alternate:>8,}{_ft(f.alternate_time)}    MIN:   {f.min_fuel_required or 0:>8,}{_ft(f.min_fuel_time)}")
    lines.append(f"  FINL:  {f.final_reserve:>8,}{_ft(f.final_reserve_time)}")
    if f.expected_landing:
        lines.append(f"  LANDING: {f.expected_landing:>6,} (est)")
    if f.plan_req is not None:
        margin_str = ""
        if f.plan_margin is not None:
            sign = "+" if f.plan_margin >= 0 else ""
            margin_str = f" ({sign}{f.plan_margin:.1f})"
        lines.append(f"  P.R: {f.plan_req:.1f}{margin_str}    REM: {f.plan_rem or 0:.1f}")

    lines.append("")
    lines.append("3. WEIGHTS (KG)")
    lines.append("-" * 40)
    lines.append(f"  ZFW: {w.ezfw:>8,} / {w.mzfw:>8,}  {w.ezfw_pct or 0:.1f}%")
    lines.append(f"  TOW: {w.etow:>8,} / {w.mtow:>8,}  {w.etow_pct or 0:.1f}%")
    ldw_warn = " ⚠ CLOSE" if w.elwt_pct and w.elwt_pct > 95 else ""
    lines.append(f"  LDW: {w.elwt:>8,} / {w.mlwt:>8,}  {w.elwt_pct or 0:.1f}%{ldw_warn}")

    lines.append("")
    lines.append("4. TAKEOFF")
    lines.append("-" * 40)
    lines.append(f"  RWY: {t.runway or 'N/A'}    SID: {t.sid or 'N/A'}")
    lines.append(f"  TOC TEMP: {t.toc_temperature or 'N/A'}    WIND: {t.wind_at_departure or 'N/A'}")
    lines.append("  V-speeds / Flaps: use EFB/OPT")

    lines.append("")
    lines.append("5. ROUTE")
    lines.append("-" * 40)
    lines.append(f"  {r.route_string}")
    if r.fir_sequence:
        lines.append(f"  FIR: {' → '.join(r.fir_sequence)}")
    if r.highest_mora:
        lines.append(f"  MORA: {r.highest_mora}")

    if data.etops:
        e = data.etops
        lines.append("  ETOPS:")
        if e.entry:
            lines.append(f"    ENTRY: EET {e.entry.eet}  ALT: {e.entry.alternate_icao}")
        for etp in e.etp_points:
            alt2 = f"/{etp.alternate_icao_2}" if etp.alternate_icao_2 else ""
            lines.append(f"    ETP:   EET {etp.eet}  ALT: {etp.alternate_icao}{alt2}")
        if e.exit:
            lines.append(f"    EXIT:  EET {e.exit.eet}  ALT: {e.exit.alternate_icao}")

    lines.append("")
    lines.append("6. ARRIVAL")
    lines.append("-" * 40)
    lines.append(f"  RWY: {a.runway or 'N/A'}    STAR: {a.star or 'N/A'}")
    if a.alternates:
        lines.append("  ALTERNATES:")
        for alt in a.alternates:
            lines.append(
                f"    {alt.icao} {alt.runway or ''} "
                f"{alt.distance or ''}nm FL{alt.flight_level or ''} "
                f"{alt.time or ''} {alt.fuel or 0:,}kg"
            )

    lines.append("")
    lines.append("7. WEATHER & NOTAMS")
    lines.append("-" * 40)
    wx = data.weather
    n = data.notams
    if wx.departure:
        lines.append(f"  DEP ({wx.departure.icao}):")
        if wx.departure.metar:
            lines.append(f"    METAR: {wx.departure.metar}")
        if wx.departure.taf:
            lines.append(f"    TAF:   {wx.departure.taf}")
        high_dep = [x for x in n.departure if x.relevance == "HIGH"]
        for item in high_dep:
            lines.append(f"    ⚠ {item.summary or item.text[:80]}")
    if wx.destination:
        lines.append(f"  DEST ({wx.destination.icao}):")
        if wx.destination.metar:
            lines.append(f"    METAR: {wx.destination.metar}")
        if wx.destination.taf:
            lines.append(f"    TAF:   {wx.destination.taf}")
        high_dest = [x for x in n.destination if x.relevance == "HIGH"]
        for item in high_dest:
            lines.append(f"    ⚠ {item.summary or item.text[:80]}")
    if wx.alternates:
        lines.append("  ALTERNATES:")
        for alt_wx in wx.alternates:
            lines.append(f"    {alt_wx.icao}:")
            if alt_wx.metar:
                lines.append(f"      METAR: {alt_wx.metar}")
            if alt_wx.taf:
                lines.append(f"      TAF:   {alt_wx.taf}")
            alt_notams = next((b for b in n.alternates if b.icao == alt_wx.icao), None)
            if alt_notams:
                for item in [x for x in alt_notams.notams if x.relevance == "HIGH"]:
                    lines.append(f"      ⚠ {item.summary or item.text[:80]}")

    if data.enroute_airport_list:
        lines.append(f"  ENROUTE AIRPORTS: {' '.join(data.enroute_airport_list)}")

    lines.append("")
    lines.append("8. OPERATIONAL INSIGHTS")
    lines.append("-" * 40)
    for ins in data.operational_insights:
        icon = "⚠" if ins.severity == "CAUTION" else "!!" if ins.severity == "WARNING" else "*"
        lines.append(f"  {icon} {ins.text}")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)
