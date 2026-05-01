import type { OperationalInsight, CrewAlert } from "@/lib/types";
import Section from "../Section";

export default function InsightsSection({
  insights,
  alerts,
}: {
  insights: OperationalInsight[];
  alerts: CrewAlert[];
}) {
  return (
    <Section number={8} title="OPERATIONAL INSIGHTS">
      {insights.length > 0 && (
        <div className="space-y-1 mb-3">
          {insights.map((ins, i) => {
            const color =
              ins.severity === "CAUTION"
                ? "text-accent-amber"
                : ins.severity === "WARNING"
                  ? "text-accent-red"
                  : "text-accent-green";
            const icon =
              ins.severity === "CAUTION"
                ? "!"
                : ins.severity === "WARNING"
                  ? "!!"
                  : "*";

            return (
              <div key={i} className="flex items-start gap-2 text-xs">
                <span className={`${color} font-bold shrink-0`}>{icon}</span>
                <span className={color}>{ins.text}</span>
              </div>
            );
          })}
        </div>
      )}

      {alerts.length > 0 && (
        <div>
          <p className="text-xs font-bold text-muted mb-1">CREW ALERTS</p>
          {alerts.map((alert, i) => (
            <div key={i} className="text-xs mb-1">
              <span className="text-muted">{alert.reference}: </span>
              <span className="text-foreground">{alert.subject}</span>
            </div>
          ))}
        </div>
      )}

      {insights.length === 0 && alerts.length === 0 && (
        <p className="text-xs text-muted">No operational concerns identified.</p>
      )}
    </Section>
  );
}
