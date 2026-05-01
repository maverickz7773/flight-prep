import type { TakeoffData } from "@/lib/types";
import Section from "../Section";

export default function TakeoffSection({ data }: { data: TakeoffData }) {
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
    </Section>
  );
}
