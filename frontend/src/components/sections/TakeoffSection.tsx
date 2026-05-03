import type { TakeoffData, AerodromeBriefing } from "@/lib/types";
import Section from "../Section";

export default function TakeoffSection({
  data,
  departureBriefing,
}: {
  data: TakeoffData;
  departureBriefing: AerodromeBriefing | null;
}) {
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
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-0.5">
        <div className="flex">
          <span className="text-muted w-20 shrink-0">RWY</span>
          <span className="text-foreground font-bold">{data.runway || "N/A"}</span>
        </div>
        <div className="flex">
          <span className="text-muted w-20 shrink-0">SID</span>
          <span className="text-foreground font-bold">{data.sid || "N/A"}</span>
        </div>
        <div className="flex">
          <span className="text-muted w-20 shrink-0">TOC TEMP</span>
          <span className="text-foreground">{data.toc_temperature || "N/A"}</span>
        </div>
        <div className="flex">
          <span className="text-muted w-20 shrink-0">WIND</span>
          <span className="text-foreground">{data.wind_at_departure || "N/A"}</span>
        </div>
      </div>
      {data.v1 && data.v1.startsWith("Not") && (
        <p className="text-muted text-xs mt-2 italic">
          V-speeds and flap setting: use EFB/OPT
        </p>
      )}

      {departureBriefing && (
        <div className="mt-3 pt-3 border-t border-border">
          <p className="text-accent-green text-xs font-bold mb-2">
            OM C — {departureBriefing.icao} ({departureBriefing.name})
          </p>
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
        </div>
      )}
    </Section>
  );
}
