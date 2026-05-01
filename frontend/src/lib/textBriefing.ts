import type { BriefingData } from "./types";

export function generateTextBriefing(data: BriefingData): string {
  const lines: string[] = [];
  const fi = data.flight_info;
  const f = data.fuel;
  const w = data.weights;
  const t = data.takeoff;
  const r = data.route;
  const a = data.arrival;

  const fmt = (n: number) => n.toLocaleString();
  const ft = (t: string | null | undefined) =>
    t && t.length === 4 ? ` (${t.slice(0, 2)}:${t.slice(2)})` : "";
  const sep = "=".repeat(60);
  const hr = "-".repeat(40);

  lines.push(sep);
  lines.push(`  ${fi.flight_number} / ${fi.date}    ${fi.departure_icao} → ${fi.arrival_icao}`);
  lines.push(`  ${fi.aircraft_type}  ${fi.registration}`);
  if (data.mel_items.length > 0) {
    lines.push(`  MEL/CDL: ${data.mel_items.map((m) => m.reference).join(", ")}`);
  } else {
    lines.push("  MEL/CDL: N/A");
  }
  lines.push(sep);

  lines.push("");
  lines.push("1. FLIGHT OVERVIEW");
  lines.push(hr);
  const depUtc = fi.departure_utc_offset ? ` (UTC${fi.departure_utc_offset})` : "";
  const arrUtc = fi.arrival_utc_offset ? ` (UTC${fi.arrival_utc_offset})` : "";
  lines.push(`  STD: ${fi.std}${depUtc}    STA: ${fi.sta}${arrUtc}`);
  lines.push(`  BLK: ${fi.block_time}    TRIP: ${fi.trip_time}`);
  lines.push(`  RWY: ${fi.departure_runway ?? "N/A"} → ${fi.arrival_runway ?? "N/A"}`);
  lines.push(`  SID: ${fi.sid ?? "N/A"}    STAR: ${fi.star ?? "N/A"}`);
  lines.push(`  CRUISE: ${fi.cruise_levels.join(" → ") || "N/A"}`);
  lines.push(`  CI: ${fi.cost_index ?? "N/A"}    ETOPS: ${fi.etops_minutes ?? "N/A"} MIN`);
  lines.push(`  GND DIST: ${fi.ground_distance ?? "N/A"} nm    WC: ${fi.wind_component ?? "N/A"}`);

  lines.push("");
  lines.push("2. FUEL (KG)");
  lines.push(hr);
  lines.push(`  TAXI:  ${fmt(f.taxi).padStart(8)}${ft(f.taxi_time)}    RAMP:  ${fmt(f.ramp).padStart(8)}${ft(f.ramp_time)}`);
  lines.push(`  TRIP:  ${fmt(f.trip).padStart(8)}${ft(f.trip_time)}    T/O:   ${fmt(f.takeoff ?? 0).padStart(8)}`);
  lines.push(`  CONT:  ${fmt(f.contingency).padStart(8)}${ft(f.contingency_time)}    EXTRA: ${fmt(f.extra).padStart(8)}${ft(f.extra_time)}`);
  lines.push(`  ALTN:  ${fmt(f.alternate).padStart(8)}${ft(f.alternate_time)}    MIN:   ${fmt(f.min_fuel_required ?? 0).padStart(8)}${ft(f.min_fuel_time)}`);
  lines.push(`  FINL:  ${fmt(f.final_reserve).padStart(8)}${ft(f.final_reserve_time)}`);
  if (f.expected_landing) {
    lines.push(`  LANDING: ${fmt(f.expected_landing)} (est)`);
  }
  if (f.plan_req != null) {
    let marginStr = "";
    if (f.plan_margin != null) {
      const sign = f.plan_margin >= 0 ? "+" : "";
      marginStr = ` (${sign}${f.plan_margin.toFixed(1)})`;
    }
    lines.push(`  P.R: ${f.plan_req.toFixed(1)}${marginStr}    REM: ${(f.plan_rem ?? 0).toFixed(1)}`);
  }

  lines.push("");
  lines.push("3. WEIGHTS (KG)");
  lines.push(hr);
  lines.push(`  ZFW: ${fmt(w.ezfw).padStart(8)} / ${fmt(w.mzfw).padStart(8)}  ${(w.ezfw_pct ?? 0).toFixed(1)}%`);
  lines.push(`  TOW: ${fmt(w.etow).padStart(8)} / ${fmt(w.mtow).padStart(8)}  ${(w.etow_pct ?? 0).toFixed(1)}%`);
  const ldwWarn = w.elwt_pct && w.elwt_pct > 95 ? " ⚠ CLOSE" : "";
  lines.push(`  LDW: ${fmt(w.elwt).padStart(8)} / ${fmt(w.mlwt).padStart(8)}  ${(w.elwt_pct ?? 0).toFixed(1)}%${ldwWarn}`);

  lines.push("");
  lines.push("4. TAKEOFF");
  lines.push(hr);
  lines.push(`  RWY: ${t.runway ?? "N/A"}    SID: ${t.sid ?? "N/A"}`);
  lines.push(`  TOC TEMP: ${t.toc_temperature ?? "N/A"}    WIND: ${t.wind_at_departure ?? "N/A"}`);
  lines.push("  V-speeds / Flaps: use EFB/OPT");

  lines.push("");
  lines.push("5. ROUTE");
  lines.push(hr);
  lines.push(`  ${r.route_string}`);
  if (r.fir_sequence.length > 0) {
    lines.push(`  FIR: ${r.fir_sequence.join(" → ")}`);
  }
  if (r.highest_mora) {
    lines.push(`  MORA: ${r.highest_mora}`);
  }

  if (data.etops) {
    const e = data.etops;
    lines.push("  ETOPS:");
    if (e.entry) lines.push(`    ENTRY: EET ${e.entry.eet}  ALT: ${e.entry.alternate_icao}`);
    for (const etp of e.etp_points) {
      const alt2 = etp.alternate_icao_2 ? `/${etp.alternate_icao_2}` : "";
      lines.push(`    ETP:   EET ${etp.eet}  ALT: ${etp.alternate_icao}${alt2}`);
    }
    if (e.exit) lines.push(`    EXIT:  EET ${e.exit.eet}  ALT: ${e.exit.alternate_icao}`);
  }

  lines.push("");
  lines.push("6. ARRIVAL");
  lines.push(hr);
  lines.push(`  RWY: ${a.runway ?? "N/A"}    STAR: ${a.star ?? "N/A"}`);
  if (a.alternates.length > 0) {
    lines.push("  ALTERNATES:");
    for (const alt of a.alternates) {
      lines.push(`    ${alt.icao} ${alt.runway ?? ""} ${alt.distance ?? ""}nm FL${alt.flight_level ?? ""} ${alt.time ?? ""} ${fmt(alt.fuel ?? 0)}kg`);
    }
  }

  lines.push("");
  lines.push("7. WEATHER & NOTAMS");
  lines.push(hr);
  const wx = data.weather;
  const notamData = data.notams;
  if (wx.departure) {
    lines.push(`  DEP (${wx.departure.icao}):`);
    if (wx.departure.metar) lines.push(`    METAR: ${wx.departure.metar}`);
    if (wx.departure.taf) lines.push(`    TAF:   ${wx.departure.taf}`);
    const highDep = notamData.departure.filter((n) => n.relevance === "HIGH");
    for (const item of highDep) {
      lines.push(`    ! ${item.summary ?? item.text.slice(0, 80)}`);
    }
  }
  if (wx.destination) {
    lines.push(`  DEST (${wx.destination.icao}):`);
    if (wx.destination.metar) lines.push(`    METAR: ${wx.destination.metar}`);
    if (wx.destination.taf) lines.push(`    TAF:   ${wx.destination.taf}`);
    const highDest = notamData.destination.filter((n) => n.relevance === "HIGH");
    for (const item of highDest) {
      lines.push(`    ! ${item.summary ?? item.text.slice(0, 80)}`);
    }
  }
  if (wx.alternates.length > 0) {
    lines.push("  ALTERNATES:");
    for (const altWx of wx.alternates) {
      lines.push(`    ${altWx.icao}:`);
      if (altWx.metar) lines.push(`      METAR: ${altWx.metar}`);
      if (altWx.taf) lines.push(`      TAF:   ${altWx.taf}`);
      const altNotams = notamData.alternates.find((b) => b.icao === altWx.icao);
      if (altNotams) {
        for (const item of altNotams.notams.filter((n) => n.relevance === "HIGH")) {
          lines.push(`      ! ${item.summary ?? item.text.slice(0, 80)}`);
        }
      }
    }
  }

  if (data.enroute_airport_list.length > 0) {
    lines.push(`  ENROUTE AIRPORTS: ${data.enroute_airport_list.join(" ")}`);
  }

  lines.push("");
  lines.push("8. OPERATIONAL INSIGHTS");
  lines.push(hr);
  for (const ins of data.operational_insights) {
    const icon = ins.severity === "CAUTION" ? "!" : ins.severity === "WARNING" ? "!!" : "*";
    lines.push(`  ${icon} ${ins.text}`);
  }

  lines.push("");
  lines.push(sep);

  return lines.join("\n");
}
