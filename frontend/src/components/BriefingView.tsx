"use client";

import { useMemo } from "react";
import type { BriefingData } from "@/lib/types";
import FlightOverview from "./sections/FlightOverview";
import FuelSection from "./sections/FuelSection";
import WeightSection from "./sections/WeightSection";
import TakeoffSection from "./sections/TakeoffSection";
import RouteSection from "./sections/RouteSection";
import ArrivalSection from "./sections/ArrivalSection";
import WxNotamSection from "./sections/WxNotamSection";
import InsightsSection from "./sections/InsightsSection";
import SolatSection from "./sections/SolatSection";
import NavSidebar from "./NavSidebar";

function parseTimeStr(s: string): number {
  const parts = s.split("/");
  const t = parts.length > 1 ? parts[1] : parts[0];
  return parseInt(t.slice(0, 2), 10) * 60 + parseInt(t.slice(2, 4), 10);
}

function fmtUtcTime(mins: number): string {
  const m = ((mins % 1440) + 1440) % 1440;
  return `${String(Math.floor(m / 60)).padStart(2, "0")}${String(m % 60).padStart(2, "0")}z`;
}

export default function BriefingView({ data }: { data: BriefingData }) {
  const fi = data.flight_info;

  const airportTimes = useMemo(() => {
    const times: Record<string, string> = {};
    const stdMins = parseTimeStr(fi.std);
    const staMins = parseTimeStr(fi.sta);

    times[fi.departure_icao] = fmtUtcTime(stdMins);
    times[fi.arrival_icao] = fmtUtcTime(staMins);

    for (const alt of data.arrival.alternates) {
      if (!times[alt.icao]) times[alt.icao] = `~${fmtUtcTime(staMins)}`;
    }

    for (const altWx of data.weather.alternates) {
      if (!times[altWx.icao]) times[altWx.icao] = `~${fmtUtcTime(staMins)}`;
    }

    for (const firBlock of data.weather.enroute) {
      const firWpts = data.route.waypoints.filter(
        (w) => w.fir_icao === firBlock.fir_icao && w.eta,
      );
      if (firWpts.length > 0) {
        const midEta = firWpts[Math.floor(firWpts.length / 2)].eta!;
        const etaMins =
          parseInt(midEta.slice(0, 2), 10) * 60 +
          parseInt(midEta.slice(2, 4), 10);
        for (const airport of firBlock.airports) {
          if (!times[airport.icao])
            times[airport.icao] = `~${fmtUtcTime(stdMins + etaMins)}`;
        }
      }
    }

    if (data.etops) {
      for (const alt of data.etops.suitable_alternates) {
        if (!times[alt.icao]) {
          const midMins = Math.floor(
            ((staMins - stdMins + 1440) % 1440) / 2,
          );
          times[alt.icao] = `~${fmtUtcTime(stdMins + midMins)}`;
        }
      }
    }

    return times;
  }, [fi, data]);

  return (
    <>
    <NavSidebar />
    <div className="max-w-4xl mx-auto p-2 sm:p-4 space-y-1 pb-4">
      <div id="section-header" className="bg-surface border border-accent-green/30 rounded-lg p-4 mb-4">
        <div className="flex justify-between items-start">
          <div>
            <span className="text-accent-green text-2xl font-bold">
              {fi.flight_number}
            </span>
            {fi.callsign && fi.callsign !== fi.flight_number && (
              <span className="text-muted text-lg ml-2">{fi.callsign}</span>
            )}
            <span className="text-muted ml-3">{fi.date}</span>
          </div>
          <div className="text-right">
            <span className="text-foreground font-bold text-lg">
              {fi.departure_icao} → {fi.arrival_icao}
            </span>
          </div>
        </div>
        <div className="flex justify-between text-sm text-muted mt-1">
          <span>
            {fi.aircraft_type} {fi.registration}
          </span>
          <span>
            {fi.departure_runway && fi.arrival_runway
              ? `RWY ${fi.departure_runway} → ${fi.arrival_runway}`
              : ""}
          </span>
        </div>
        {data.mel_items.length > 0 ? (
          <div className="mt-2 pt-2 border-t border-accent-amber/30">
            <p className="text-accent-amber text-xs font-bold mb-1">
              MEL/CDL ITEMS ({data.mel_items.length})
            </p>
            {data.mel_items.map((mel, i) => (
              <div key={i} className="text-xs ml-2 mb-0.5">
                <span className="text-accent-amber font-bold">{mel.reference}</span>
                <span className="text-foreground ml-2">{mel.description}</span>
                {mel.remark && (
                  <span className="text-muted ml-1">— {mel.remark}</span>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="mt-2 pt-2 border-t border-border">
            <p className="text-xs text-muted">MEL/CDL: N/A</p>
          </div>
        )}
      </div>

      <FlightOverview data={fi} etops={data.etops} ezfw={data.weights.ezfw} />
      <FuelSection data={data.fuel} />
      <WeightSection data={data.weights} />
      <TakeoffSection
        data={data.takeoff}
        departureWeather={data.weather.departure}
        departureTime={data.weather.departure ? airportTimes[data.weather.departure.icao] : undefined}
        departureReferenceTime={data.flight_info.std}
        flightDate={data.flight_info.date}
        departureBriefing={data.departure_briefing}
        departureNote={data.airport_notes?.departure ?? null}
      />
      <RouteSection route={data.route} ezfw={data.weights.ezfw} />
      <ArrivalSection
        data={data.arrival}
        destinationWeather={data.weather.destination}
        destinationTime={data.weather.destination ? airportTimes[data.weather.destination.icao] : undefined}
        destinationReferenceTime={data.flight_info.sta}
        flightDate={data.flight_info.date}
        arrivalBriefing={data.arrival_briefing}
        arrivalNote={data.airport_notes?.arrival ?? null}
      />
      <WxNotamSection
        weather={data.weather}
        notams={data.notams}
        enrouteAirportList={data.enroute_airport_list}
        airportTimes={airportTimes}
        flightDate={data.flight_info.date}
        firSequence={data.route.fir_sequence}
      />
      <InsightsSection
        insights={data.operational_insights}
        alerts={data.crew_alerts}
      />
      <SolatSection
        waypoints={data.route.waypoints}
        std={data.flight_info.std}
        flightDate={data.flight_info.date}
        cruiseFlightLevels={data.route.cruise_flight_levels}
      />
    </div>
    </>
  );
}
