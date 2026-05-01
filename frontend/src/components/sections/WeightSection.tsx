import type { Weights } from "@/lib/types";
import Section from "../Section";

function WtRow({
  label,
  estimated,
  max,
  pct,
  absThreshold,
  absColor,
}: {
  label: string;
  estimated: number;
  max: number;
  pct: number | null;
  absThreshold?: number;
  absColor?: "amber" | "red";
}) {
  const pctWarning = pct !== null && pct > 95;
  const pctCaution = pct !== null && pct > 90 && pct <= 95;
  const absTriggered = absThreshold != null && estimated > absThreshold;

  let colorClass = "text-accent-green";
  let suffix = "";

  if (pctWarning || (absTriggered && absColor === "red")) {
    colorClass = "text-accent-red";
    suffix = " ⚠ CLOSE TO LIMIT";
  } else if (pctCaution || (absTriggered && absColor === "amber")) {
    colorClass = "text-accent-amber";
  }

  return (
    <div className="flex items-center">
      <span className="text-muted w-12 shrink-0">{label}</span>
      <span className="text-foreground w-24 text-right tabular-nums">
        {estimated.toLocaleString()}
      </span>
      <span className="text-muted mx-1">/</span>
      <span className="text-muted w-24 text-right tabular-nums">
        {max.toLocaleString()}
      </span>
      {pct !== null && (
        <span className={`ml-3 text-xs font-bold ${colorClass}`}>
          {pct.toFixed(1)}%{suffix}
        </span>
      )}
    </div>
  );
}

export default function WeightSection({ data }: { data: Weights }) {
  return (
    <Section number={3} title="WEIGHTS (KG)">
      <div className="space-y-0.5">
        <WtRow
          label="ZFW"
          estimated={data.ezfw}
          max={data.mzfw}
          pct={data.ezfw_pct}
          absThreshold={230000}
          absColor="amber"
        />
        <WtRow
          label="TOW"
          estimated={data.etow}
          max={data.mtow}
          pct={data.etow_pct}
          absThreshold={330000}
          absColor="red"
        />
        <WtRow
          label="LDW"
          estimated={data.elwt}
          max={data.mlwt}
          pct={data.elwt_pct}
          absThreshold={245000}
          absColor="red"
        />
      </div>
    </Section>
  );
}
