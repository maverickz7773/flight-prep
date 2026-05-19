"use client";

import { useState, useMemo } from "react";
import type { FlightInfo, ETOPSInfo, NATSProcedure } from "@/lib/types";
import InlineDisclosure from "../InlineDisclosure";
import Section from "../Section";

function Row({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="flex">
      <span className="text-muted w-28 shrink-0">{label}</span>
      <span className="text-foreground">{value || "N/A"}</span>
    </div>
  );
}

function parseMinutes(hhmm: string): number {
  const h = parseInt(hhmm.slice(0, 2), 10);
  const m = parseInt(hhmm.slice(2, 4), 10);
  return h * 60 + m;
}

function formatMinutes(mins: number): string {
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return `${h}h${m.toString().padStart(2, "0")}m`;
}

function addMinutesToTime(base: string, addMins: number): string {
  const parts = base.split("/");
  const day = parts.length > 1 ? parts[0] : "";
  const time = parts.length > 1 ? parts[1] : parts[0];
  const baseH = parseInt(time.slice(0, 2), 10);
  const baseM = parseInt(time.slice(2, 4), 10);
  let totalMins = baseH * 60 + baseM + addMins;
  let dayNum = day ? parseInt(day, 10) : 0;
  while (totalMins >= 1440) {
    totalMins -= 1440;
    dayNum++;
  }
  const hh = Math.floor(totalMins / 60).toString().padStart(2, "0");
  const mm = (totalMins % 60).toString().padStart(2, "0");
  return day ? `${dayNum.toString().padStart(2, "0")}/${hh}${mm}` : `${hh}${mm}`;
}

export default function FlightOverview({
  data,
  etops,
  ezfw,
  natsProcedure,
}: {
  data: FlightInfo;
  etops: ETOPSInfo | null;
  ezfw: number;
  natsProcedure: NATSProcedure | null;
}) {
  const [crewCount, setCrewCount] = useState<2 | 3 | 4>(2);

  const tripMins = useMemo(() => {
    if (!data.trip_time) return 0;
    return parseMinutes(data.trip_time);
  }, [data.trip_time]);

  const restPeriods = useMemo(() => {
    if (crewCount === 2 || tripMins === 0) return null;

    const windowStart = 20;
    const windowEnd = tripMins - 60;
    const availableWindow = windowEnd - windowStart;
    if (availableWindow <= 0) return null;

    const slots = crewCount === 3 ? 3 : 2;
    const slotDuration = Math.floor(availableWindow / slots);
    const periods: { label: string; start: string; duration: string }[] = [];

    for (let i = 0; i < slots; i++) {
      periods.push({
        label: `Rest ${i + 1}`,
        start: addMinutesToTime(data.std, windowStart + slotDuration * i),
        duration: formatMinutes(slotDuration),
      });
    }

    return periods;
  }, [crewCount, tripMins, data.std]);

  const stdDisplay = data.std
    ? `${data.std}${data.departure_utc_offset ? ` (UTC${data.departure_utc_offset})` : ""}`
    : "N/A";
  const staDisplay = data.sta
    ? `${data.sta}${data.arrival_utc_offset ? ` (UTC${data.arrival_utc_offset})` : ""}`
    : "N/A";

  return (
    <Section number={1} title="FLIGHT OVERVIEW">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-0.5">
        <Row label="STD" value={stdDisplay} />
        <Row label="STA" value={staDisplay} />
        <Row label="BLOCK" value={data.block_time} />
        <Row label="TRIP" value={data.trip_time} />
        <Row label="SID" value={data.sid} />
        <Row label="STAR" value={data.star} />
        <Row
          label="CRUISE"
          value={data.cruise_levels.join(" → ") || "N/A"}
        />
        <Row label="CI" value={data.cost_index?.toString() ?? "N/A"} />
        <Row
          label="GND DIST"
          value={data.ground_distance ? `${data.ground_distance} nm` : "N/A"}
        />
        <Row label="WIND" value={data.wind_component} />
      </div>

      {etops && etops.sectors.length > 0 && (
        <div className="mt-3 pt-2 border-t border-border space-y-0.5">
          {data.etops_minutes && (
            <Row label="ETOPS" value={`${data.etops_minutes} MIN`} />
          )}
          {etops.sectors.map((s) => {
            const multi = etops.sectors.length > 1;
            const pfx = multi ? `S${s.sector_number} ` : "";
            const gw = (fuel: number | null) =>
              fuel != null ? `  GW ${(ezfw / 1000 + fuel).toFixed(1)}t` : "";
            return (
              <div key={s.sector_number} className="space-y-0.5">
                {s.entry_icao && (
                  <Row
                    label={`${pfx}ENTRY`}
                    value={`${s.entry_icao}${s.entry_eet ? `  EET ${s.entry_eet}` : ""}${gw(s.entry_fuel)}`}
                  />
                )}
                {s.exit_icao && (
                  <Row
                    label={`${pfx}EXIT`}
                    value={`${s.exit_icao}${s.exit_eet ? `  EET ${s.exit_eet}` : ""}${gw(s.exit_fuel)}`}
                  />
                )}
                {s.alternates.length > 0 && (
                  <Row label={`${pfx}ALTN`} value={s.alternates.join(", ")} />
                )}
              </div>
            );
          })}
        </div>
      )}
      {(!etops || etops.sectors.length === 0) && data.etops_minutes && (
        <div className="mt-3 pt-2 border-t border-border">
          <Row label="ETOPS" value={`${data.etops_minutes} MIN`} />
        </div>
      )}

      <div className="mt-3 pt-2 border-t border-border">
        <div className="flex items-center gap-3 mb-1">
          <span className="text-muted text-xs w-28 shrink-0">CREW</span>
          <div className="flex gap-1">
            {([2, 3, 4] as const).map((n) => (
              <button
                key={n}
                onClick={() => setCrewCount(n)}
                className={`px-3 py-0.5 text-xs rounded border transition-colors no-print ${
                  crewCount === n
                    ? "bg-accent-green/20 border-accent-green text-accent-green"
                    : "border-border text-muted hover:border-muted"
                }`}
              >
                {n}
              </button>
            ))}
          </div>
          {crewCount === 2 && (
            <span className="text-muted text-xs">No rest</span>
          )}
        </div>

        {restPeriods && restPeriods.length > 0 && (
          <div className="space-y-0.5 ml-0">
            {restPeriods.map((r) => (
              <div key={r.label} className="flex text-xs">
                <span className="text-muted w-28 shrink-0">{r.label}</span>
                <span className="text-accent-green">
                  {r.start} ({r.duration})
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {natsProcedure && (
        <div className="mt-3 pt-2 border-t border-border">
          <InlineDisclosure title="NATS">
            <div className="space-y-1 text-xs">
              <p className="text-accent-amber font-bold">NATS OVERVIEW</p>
              <Row label="TMI" value={natsProcedure.overview.tmi} />
              <div className="flex">
                <span className="text-muted w-28 shrink-0">ROUTE</span>
                <span className="text-foreground whitespace-pre-line break-words">
                  {natsProcedure.overview.route || "N/A"}
                </span>
              </div>
              <Row
                label="ENTRY"
                value={
                  natsProcedure.overview.entry_point
                    ? `${natsProcedure.overview.entry_point}${natsProcedure.overview.entry_eet ? `  EET ${natsProcedure.overview.entry_eet}` : ""}${natsProcedure.overview.entry_fir ? `  ${natsProcedure.overview.entry_fir}` : ""}`
                    : "N/A"
                }
              />
              <Row
                label="EXIT"
                value={
                  natsProcedure.overview.exit_point
                    ? `${natsProcedure.overview.exit_point}${natsProcedure.overview.exit_eet ? `  EET ${natsProcedure.overview.exit_eet}` : ""}${natsProcedure.overview.exit_fir ? `  ${natsProcedure.overview.exit_fir}` : ""}`
                    : "N/A"
                }
              />
            </div>
          </InlineDisclosure>
        </div>
      )}
    </Section>
  );
}
