import type { RouteSummary } from "@/lib/types";
import Section from "../Section";

export default function RouteSection({
  route,
  ezfw,
}: {
  route: RouteSummary;
  ezfw: number;
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
            <span className="w-16 text-right">GW</span>
            <span className="w-10 text-right">SR</span>
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
                {w.fuel_remaining != null ? `${(ezfw / 1000 + w.fuel_remaining).toFixed(1)}t` : ""}
              </span>
              <span className={`w-10 text-right tabular-nums ${w.shear_rate != null && w.shear_rate > 5 ? "text-accent-amber font-bold" : ""}`}>
                {w.shear_rate != null ? w.shear_rate : ""}
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

    </Section>
  );
}
