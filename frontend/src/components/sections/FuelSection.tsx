import type { FuelSummary } from "@/lib/types";
import Section from "../Section";

function fmtTime(t: string | null | undefined): string | undefined {
  if (!t || t.length !== 4) return undefined;
  return `${t.slice(0, 2)}:${t.slice(2)}`;
}

function FuelRow({
  label,
  value,
  time,
  note,
}: {
  label: string;
  value: number;
  time?: string | null;
  note?: string;
}) {
  const formattedTime = fmtTime(time);
  return (
    <div className="flex">
      <span className="text-muted w-20 shrink-0">{label}</span>
      <span className="text-foreground w-24 text-right tabular-nums">
        {value.toLocaleString()}
      </span>
      {formattedTime && (
        <span className="text-muted ml-1 text-xs tabular-nums">({formattedTime})</span>
      )}
      {note && <span className="text-muted ml-2 text-xs">{note}</span>}
    </div>
  );
}

export default function FuelSection({ data }: { data: FuelSummary }) {
  return (
    <Section number={2} title="FUEL (KG)">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-0.5">
        <FuelRow label="TAXI" value={data.taxi} time={data.taxi_time} />
        <FuelRow label="TRIP" value={data.trip} time={data.trip_time} />
        <FuelRow
          label="CONT"
          value={data.contingency}
          time={data.contingency_time}
          note={data.contingency_type ?? undefined}
        />
        <FuelRow
          label="ALTN"
          value={data.alternate}
          time={data.alternate_time}
          note={data.alternate_airport ?? undefined}
        />
        <FuelRow
          label="FINL"
          value={data.final_reserve}
          time={data.final_reserve_time}
        />
        <FuelRow
          label="MIN FUEL"
          value={data.min_fuel_required ?? 0}
          time={data.min_fuel_time}
        />
        <FuelRow label="EXTRA" value={data.extra} time={data.extra_time} />
        <FuelRow label="RAMP" value={data.ramp} time={data.ramp_time} />
      </div>
      {data.takeoff != null && (
        <div className="mt-2 pt-2 border-t border-border flex">
          <span className="text-muted w-20 shrink-0">T/O</span>
          <span className="text-foreground w-24 text-right tabular-nums">
            {data.takeoff.toLocaleString()}
          </span>
        </div>
      )}
      {data.expected_landing && (
        <div className="mt-2 pt-2 border-t border-border flex">
          <span className="text-accent-green font-bold w-20">LANDING</span>
          <span className="text-accent-green font-bold w-24 text-right tabular-nums">
            {data.expected_landing.toLocaleString()}
          </span>
          <span className="text-muted ml-2 text-xs">(estimated)</span>
        </div>
      )}
      {data.plan_req != null && (
        <div className="mt-2 pt-2 border-t border-border flex items-center">
          <span className="text-muted w-20 shrink-0">P.R</span>
          <span className="text-foreground w-24 text-right tabular-nums">
            {data.plan_req.toFixed(1)}
          </span>
          {data.plan_margin != null && (
            <span
              className={`ml-2 text-xs font-bold ${
                data.plan_margin >= 0 ? "text-accent-green" : "text-accent-red"
              }`}
            >
              ({data.plan_margin >= 0 ? "+" : ""}
              {data.plan_margin.toFixed(1)})
            </span>
          )}
          <span className="text-muted ml-2 text-xs">
            REM {data.plan_rem?.toFixed(1) ?? "N/A"}
          </span>
        </div>
      )}
    </Section>
  );
}
