import { useState } from "react";
import type { TakeoffData, AerodromeBriefing, AirportWeather } from "@/lib/types";
import CompactAirportWeather from "../CompactAirportWeather";
import Section from "../Section";

export default function TakeoffSection({
  data,
  departureWeather,
  departureTime,
  departureReferenceTime,
  flightDate,
  departureBriefing,
  departureNote,
}: {
  data: TakeoffData;
  departureWeather: AirportWeather | null;
  departureTime?: string;
  departureReferenceTime?: string;
  flightDate: string;
  departureBriefing: AerodromeBriefing | null;
  departureNote: string | null;
}) {
  const [omcOpen, setOmcOpen] = useState(false);
  const sections: { label: string; content: string | null }[] = departureBriefing
    ? [
        { label: "GENERAL", content: departureBriefing.general },
        { label: "COMPANY POLICY", content: departureBriefing.company_policy },
        { label: "ATC", content: departureBriefing.atc },
        { label: "DEPARTURE PROCEDURES", content: departureBriefing.departure_procedures },
        { label: "MISCELLANEOUS", content: departureBriefing.miscellaneous },
      ]
    : [];

  return (
    <Section number={4} title="TAKEOFF">
      <CompactAirportWeather
        label="DEPARTURE"
        wx={departureWeather}
        expectedTime={departureTime}
        referenceTime={departureReferenceTime}
        flightDate={flightDate}
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-0.5">
        <div className="flex">
          <span className="text-muted w-20 shrink-0">RWY</span>
          <span className="text-foreground font-bold">{data.runway || "N/A"}</span>
        </div>
        <div className="flex">
          <span className="text-muted w-20 shrink-0">SID</span>
          <span className="text-foreground font-bold">{data.sid || "N/A"}</span>
        </div>
      </div>

      {departureNote && (
        <div className="mt-2 rounded border border-accent-green/20 bg-accent-green/5 px-3 py-2">
          <p className="text-accent-green text-[11px] font-bold mb-1">OPS INFO</p>
          <p className="text-foreground text-xs whitespace-pre-line leading-relaxed">
            {departureNote}
          </p>
        </div>
      )}

      {data.v1 && data.v1.startsWith("Not") && (
        <p className="text-muted text-xs mt-2 italic">
          V-speeds and flap setting: use EFB/OPT
        </p>
      )}

      {departureBriefing && (
        <div className="mt-3 pt-3 border-t border-border">
          <button
            onClick={() => setOmcOpen(!omcOpen)}
            className="text-left w-full text-accent-green text-xs font-bold mb-2 hover:text-foreground transition-colors"
            type="button"
          >
            {omcOpen ? "▼" : "▶"} OM C — {departureBriefing.icao} ({departureBriefing.name})
          </button>
          {omcOpen && (
            <div className="space-y-2">
              {sections.map(
                (s) =>
                  s.content && (
                    <div key={s.label}>
                      <p className="text-accent-amber text-xs font-bold">{s.label}</p>
                      <p className="text-foreground text-xs whitespace-pre-line leading-relaxed">
                        {s.content}
                      </p>
                    </div>
                  ),
              )}
            </div>
          )}
        </div>
      )}
    </Section>
  );
}
