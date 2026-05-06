"use client";

import type { AirportWeather } from "@/lib/types";
import TafText from "./TafText";

export default function CompactAirportWeather({
  label,
  wx,
  expectedTime,
  referenceTime,
  flightDate,
}: {
  label: string;
  wx: AirportWeather | null;
  expectedTime?: string;
  referenceTime?: string;
  flightDate?: string;
}) {
  if (!wx) return null;

  return (
    <div className="mb-3 border-b border-border pb-2">
      <p className="text-[13px] font-bold uppercase tracking-[0.08em] leading-none">
        <span className="text-muted">{label}: </span>
        <span className="text-accent-green">{wx.icao}</span>
        {wx.name && (
          <span className="text-muted font-normal ml-1 uppercase tracking-[0.04em]">
            {wx.name}
          </span>
        )}
        {expectedTime && (
          <span className="text-muted font-normal ml-2 tabular-nums lowercase">
            {expectedTime}
          </span>
        )}
      </p>

      {wx.metar && (
        <p className="mt-1 text-[13px] leading-tight text-foreground break-all">
          <span className="text-muted uppercase tracking-[0.08em]">METAR: </span>
          {wx.metar}
        </p>
      )}

      {wx.taf && (
        <p className="mt-1 text-[13px] leading-tight text-foreground break-all">
          <span className="text-muted uppercase tracking-[0.08em]">TAF: </span>
          <TafText
            text={wx.taf}
            referenceTime={referenceTime}
            flightDate={flightDate}
          />
        </p>
      )}
    </div>
  );
}
