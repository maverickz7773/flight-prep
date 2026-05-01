"use client";

import { useState, useMemo } from "react";
import type { Waypoint } from "@/lib/types";
import {
  calculatePrayerTimes,
  parseCoordinate,
  flToMeters,
} from "@/lib/prayerTimes";
import Section from "../Section";

function fmtUtc(d: Date): string {
  const hh = d.getUTCHours().toString().padStart(2, "0");
  const mm = d.getUTCMinutes().toString().padStart(2, "0");
  return `${hh}:${mm}`;
}

function parseFlightDate(dateStr: string): Date {
  // Format: "29APR26" or "30Apr26"
  const m = dateStr.match(/(\d{2})(\w{3})(\d{2})/);
  if (!m) return new Date();
  const day = parseInt(m[1], 10);
  const monStr = m[2].toUpperCase();
  const year = 2000 + parseInt(m[3], 10);
  const months: Record<string, number> = {
    JAN: 0, FEB: 1, MAR: 2, APR: 3, MAY: 4, JUN: 5,
    JUL: 6, AUG: 7, SEP: 8, OCT: 9, NOV: 10, DEC: 11,
  };
  return new Date(Date.UTC(year, months[monStr] ?? 0, day));
}

function etaToUtcMinutes(std: string, etaElapsed: string): number {
  // STD: "29/0600", ETA elapsed: "0135"
  const parts = std.split("/");
  const time = parts.length > 1 ? parts[1] : parts[0];
  const stdH = parseInt(time.slice(0, 2), 10);
  const stdM = parseInt(time.slice(2, 4), 10);
  const etaH = parseInt(etaElapsed.slice(0, 2), 10);
  const etaM = parseInt(etaElapsed.slice(2, 4), 10);
  return stdH * 60 + stdM + etaH * 60 + etaM;
}


export default function SolatSection({
  waypoints,
  std,
  flightDate,
  cruiseFlightLevels,
}: {
  waypoints: Waypoint[];
  std: string;
  flightDate: string;
  cruiseFlightLevels: string[];
}) {
  const [selectedIdx, setSelectedIdx] = useState<number>(-1);
  const [selectedFL, setSelectedFL] = useState<string>("");
  const [useAltitude, setUseAltitude] = useState(true);

  const eligibleWaypoints = useMemo(
    () => waypoints.filter((w) => w.latitude && w.longitude && w.eta),
    [waypoints],
  );

  const selected = selectedIdx >= 0 ? eligibleWaypoints[selectedIdx] : null;

  const result = useMemo(() => {
    if (!selected?.latitude || !selected?.longitude || !selected?.eta) return null;

    const lat = parseCoordinate(selected.latitude);
    const lng = parseCoordinate(selected.longitude);
    const date = parseFlightDate(flightDate);
    const alt = useAltitude && selectedFL ? flToMeters(selectedFL) : 0;

    const times = calculatePrayerTimes(lat, lng, date, alt);

    const etaUtcMins = etaToUtcMinutes(std, selected.eta);
    const windowStart = etaUtcMins - 60;
    const windowEnd = etaUtcMins + 7 * 60;

    const prayerEntries = [
      { name: "Fajr" as const, time: times.fajr },
      { name: "Dhuhr" as const, time: times.dhuhr },
      { name: "Asr" as const, time: times.asr },
      { name: "Maghrib" as const, time: times.maghrib },
      { name: "Isha" as const, time: times.isha },
    ];

    return prayerEntries.map((p) => {
      const pMins = p.time.getUTCHours() * 60 + p.time.getUTCMinutes();
      let inWindow = pMins >= windowStart && pMins <= windowEnd;
      // Handle day wrap
      if (windowEnd > 1440) {
        inWindow = pMins >= windowStart || pMins <= windowEnd - 1440;
      }
      if (windowStart < 0) {
        inWindow = pMins >= windowStart + 1440 || pMins <= windowEnd;
      }
      return { ...p, inWindow, utcStr: fmtUtc(p.time) };
    });
  }, [selected, flightDate, std, useAltitude, selectedFL]);

  if (eligibleWaypoints.length === 0) return null;

  return (
    <Section number={9} title="INFLIGHT SOLAT" defaultOpen={false}>
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          <label className="text-xs text-muted">Waypoint:</label>
          <select
            value={selectedIdx}
            onChange={(e) => setSelectedIdx(parseInt(e.target.value, 10))}
            className="bg-surface-2 border border-border rounded px-2 py-1 text-xs text-foreground min-w-48"
          >
            <option value={-1}>Select waypoint...</option>
            {eligibleWaypoints.map((w, i) => (
              <option key={i} value={i}>
                {w.name} (EET {w.eta})
              </option>
            ))}
          </select>

          {cruiseFlightLevels.length > 0 && (
            <>
              <label className="text-xs text-muted">FL:</label>
              <select
                value={selectedFL}
                onChange={(e) => setSelectedFL(e.target.value)}
                className="bg-surface-2 border border-border rounded px-2 py-1 text-xs text-foreground"
              >
                <option value="">Ground level</option>
                {cruiseFlightLevels.map((fl) => (
                  <option key={fl} value={fl}>
                    {fl}
                  </option>
                ))}
              </select>
            </>
          )}

          <label className="text-xs text-muted flex items-center gap-1 no-print">
            <input
              type="checkbox"
              checked={useAltitude}
              onChange={(e) => setUseAltitude(e.target.checked)}
              className="accent-accent-green"
            />
            Altitude adjust
          </label>
        </div>

        {selected && (
          <div className="text-xs text-muted">
            <span>
              {selected.latitude} / {selected.longitude}
            </span>
            {selected.eta && (
              <span className="ml-3">EET {selected.eta}</span>
            )}
            {selected.true_track != null && (
              <span className="ml-3">TRK {selected.true_track}°</span>
            )}
            {selected.tas != null && (
              <span className="ml-3">TAS {selected.tas}</span>
            )}
            {useAltitude && selectedFL && (
              <span className="ml-3">
                {selectedFL} ({Math.round(flToMeters(selectedFL))}m)
              </span>
            )}
          </div>
        )}

        {result && (
          <div className="border border-border rounded overflow-hidden">
            <div className="grid grid-cols-3 gap-0 text-xs font-bold text-muted bg-surface-2 px-3 py-1">
              <span>Prayer</span>
              <span className="text-center">UTC</span>
              <span className="text-right">Status</span>
            </div>
            {result.map((p) => (
              <div
                key={p.name}
                className={`grid grid-cols-3 gap-0 text-xs px-3 py-1.5 border-t border-border ${
                  p.inWindow ? "" : "opacity-40"
                }`}
              >
                <span
                  className={
                    p.inWindow ? "text-accent-green font-bold" : "text-muted"
                  }
                >
                  {p.name}
                </span>
                <span
                  className={`text-center tabular-nums ${
                    p.inWindow ? "text-foreground" : "text-muted"
                  }`}
                >
                  {p.utcStr}
                </span>
                <span className="text-right">
                  {p.inWindow ? (
                    <span className="text-accent-green">● In window</span>
                  ) : (
                    <span className="text-muted">—</span>
                  )}
                </span>
              </div>
            ))}
            <div className="text-xs text-muted px-3 py-1.5 border-t border-border bg-surface-2">
              Window: ETA−1h to ETA+7h | Umm Al-Qura · Shafi&apos;i
            </div>
          </div>
        )}
      </div>
    </Section>
  );
}
