import type { ArrivalInfo } from "@/lib/types";
import Section from "../Section";

export default function ArrivalSection({ data }: { data: ArrivalInfo }) {
  return (
    <Section number={6} title="ARRIVAL">
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

      {data.alternates.length > 0 && (
        <div>
          <p className="text-muted text-xs font-bold mb-0.5">ALTERNATES</p>
          <div className="text-xs">
            <div className="text-muted flex mb-0.5">
              <span className="w-12">ICAO</span>
              <span className="w-8">RWY</span>
              <span className="w-14 text-right">DIST</span>
              <span className="w-14 text-right">FL</span>
              <span className="w-14 text-right">TIME</span>
              <span className="w-18 text-right">FUEL</span>
              <span className="ml-2">ROUTE</span>
            </div>
            {data.alternates.map((alt, i) => (
              <div key={i} className="flex text-foreground">
                <span className="w-12 font-bold">{alt.icao}</span>
                <span className="w-8">{alt.runway || ""}</span>
                <span className="w-14 text-right tabular-nums">
                  {alt.distance ? `${alt.distance}nm` : ""}
                </span>
                <span className="w-14 text-right tabular-nums">
                  {alt.flight_level || ""}
                </span>
                <span className="w-14 text-right tabular-nums">
                  {alt.time || ""}
                </span>
                <span className="w-18 text-right tabular-nums">
                  {alt.fuel ? `${alt.fuel.toLocaleString()}` : ""}
                </span>
                <span className="ml-2 text-muted truncate">
                  {alt.route || ""}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </Section>
  );
}
