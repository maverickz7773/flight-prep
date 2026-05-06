import { useState } from "react";
import type { ArrivalInfo, AerodromeBriefing, AirportWeather } from "@/lib/types";
import CompactAirportWeather from "../CompactAirportWeather";
import Section from "../Section";

export default function ArrivalSection({
  data,
  destinationWeather,
  destinationTime,
  destinationReferenceTime,
  flightDate,
  arrivalBriefing,
  arrivalNote,
}: {
  data: ArrivalInfo;
  destinationWeather: AirportWeather | null;
  destinationTime?: string;
  destinationReferenceTime?: string;
  flightDate: string;
  arrivalBriefing: AerodromeBriefing | null;
  arrivalNote: string | null;
}) {
  const [omcOpen, setOmcOpen] = useState(false);
  const sections: { label: string; content: string | null }[] = arrivalBriefing
    ? [
        { label: "GENERAL", content: arrivalBriefing.general },
        { label: "COMPANY POLICY", content: arrivalBriefing.company_policy },
        { label: "ATC", content: arrivalBriefing.atc },
        { label: "ARRIVAL PROCEDURES", content: arrivalBriefing.arrival_procedures },
        { label: "GROUND MANEUVERING", content: arrivalBriefing.ground_maneuvering },
        { label: "MISCELLANEOUS", content: arrivalBriefing.miscellaneous },
        { label: "DESTINATION ALTERNATES", content: arrivalBriefing.destination_alternates },
      ]
    : [];

  return (
    <Section number={6} title="ARRIVAL">
      <CompactAirportWeather
        label="DESTINATION"
        wx={destinationWeather}
        expectedTime={destinationTime}
        referenceTime={destinationReferenceTime}
        flightDate={flightDate}
      />

      <div className="flex gap-8 mb-2">
        <div className="flex">
          <span className="text-muted w-12">RWY</span>
          <span className="text-foreground font-bold">{data.runway || "N/A"}</span>
        </div>
        <div className="flex">
          <span className="text-muted w-12">STAR</span>
          <span className="text-foreground font-bold">{data.star || "N/A"}</span>
        </div>
      </div>

      {arrivalNote && (
        <div className="mb-2 rounded border border-accent-green/20 bg-accent-green/5 px-3 py-2">
          <p className="text-accent-green text-[11px] font-bold mb-1">OPS INFO</p>
          <p className="text-foreground text-xs whitespace-pre-line leading-relaxed">
            {arrivalNote}
          </p>
        </div>
      )}

      {arrivalBriefing && (
        <div className="mt-3 pt-3 border-t border-border">
          <button
            onClick={() => setOmcOpen(!omcOpen)}
            className="text-left w-full text-accent-green text-xs font-bold mb-2 hover:text-foreground transition-colors"
            type="button"
          >
            {omcOpen ? "▼" : "▶"} OM C — {arrivalBriefing.icao} ({arrivalBriefing.name})
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
