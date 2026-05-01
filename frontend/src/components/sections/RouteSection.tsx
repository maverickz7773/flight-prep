import type { RouteSummary, ETOPSInfo } from "@/lib/types";
import Section from "../Section";

export default function RouteSection({
  route,
  etops,
}: {
  route: RouteSummary;
  etops: ETOPSInfo | null;
}) {
  const keyWaypoints = route.waypoints.filter(
    (w) => w.is_toc || w.is_tod || w.is_step_climb || w.fir_icao
  );

  const displayWaypoints =
    keyWaypoints.length > 0
      ? keyWaypoints
      : route.waypoints.filter((_, i) => i % 5 === 0);

  return (
    <Section number={5} title="ROUTE">
      <p className="text-foreground text-xs mb-2 leading-relaxed break-all">
        {route.route_string}
      </p>

      {displayWaypoints.length > 0 && (
        <div className="mb-2">
          <div className="text-muted text-xs flex mb-0.5">
            <span className="w-20">WPT</span>
            <span className="w-14 text-right">FL</span>
            <span className="w-16 text-right">ETA</span>
            <span className="w-16 text-right">FUEL</span>
            <span className="ml-2">NOTE</span>
          </div>
          {displayWaypoints.map((w, i) => (
            <div
              key={i}
              className={`flex text-xs ${
                w.is_toc || w.is_tod
                  ? "text-accent-green"
                  : w.is_step_climb
                    ? "text-accent-amber"
                    : "text-foreground"
              }`}
            >
              <span className="w-20 font-bold">{w.name}</span>
              <span className="w-14 text-right tabular-nums">
                {w.flight_level || ""}
              </span>
              <span className="w-16 text-right tabular-nums">
                {w.eta || ""}
              </span>
              <span className="w-16 text-right tabular-nums">
                {w.fuel_remaining ? `${w.fuel_remaining}t` : ""}
              </span>
              <span className="ml-2 text-muted">
                {w.is_toc
                  ? "TOP OF CLIMB"
                  : w.is_tod
                    ? "TOP OF DESCENT"
                    : w.is_step_climb
                      ? "STEP CLIMB"
                      : ""}
              </span>
            </div>
          ))}
        </div>
      )}

      <div className="text-xs text-muted">
        <span className="font-bold text-foreground">FIR: </span>
        {route.fir_sequence.map((f, i) => (
          <span key={i}>
            {i > 0 && <span className="text-accent-green"> → </span>}
            {f}
          </span>
        ))}
      </div>

      {route.highest_mora && (
        <p className="text-xs text-muted mt-1">
          MORA: {route.highest_mora}
        </p>
      )}

      {etops && (
        <div className="mt-2 pt-2 border-t border-border">
          <p className="text-accent-amber text-xs font-bold mb-1">
            ETOPS SECTOR
          </p>
          <div className="text-xs space-y-0.5">
            {etops.entry && (
              <p>
                ENTRY: EET {etops.entry.eet} — ALT: {etops.entry.alternate_icao}
                {etops.entry.fuel_remaining &&
                  ` (${etops.entry.fuel_remaining}t)`}
              </p>
            )}
            {etops.etp_points.map((etp, i) => (
              <p key={i}>
                ETP: EET {etp.eet} — ALT: {etp.alternate_icao}
                {etp.alternate_icao_2 && `/${etp.alternate_icao_2}`}
              </p>
            ))}
            {etops.exit && (
              <p>
                EXIT: EET {etops.exit.eet} — ALT: {etops.exit.alternate_icao}
                {etops.exit.fuel_remaining &&
                  ` (${etops.exit.fuel_remaining}t)`}
              </p>
            )}
            {etops.suitable_alternates.length > 0 && (
              <p className="text-muted">
                Suitable alternates:{" "}
                {etops.suitable_alternates
                  .map((a) => `${a.icao} ${a.runway || ""}`)
                  .join(", ")}
              </p>
            )}
          </div>
        </div>
      )}
    </Section>
  );
}
