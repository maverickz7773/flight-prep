from __future__ import annotations
import re
from models.briefing import FuelSummary


def parse_fuel(pages: list[str]) -> FuelSummary:
    text = "\n".join(pages[:5])

    def parse_contingency() -> tuple[int, str | None, str | None]:
        for raw_line in text.splitlines():
            line = " ".join(raw_line.split())
            if not line.startswith("CONT "):
                continue
            if " AT DEP " in line:
                continue

            cont_segment = line.split(" BLK ", 1)[0].strip()
            tokens = cont_segment.split()
            if len(tokens) < 3:
                continue

            if len(tokens) >= 4 and tokens[-1].isdigit() and len(tokens[-1]) == 4 and tokens[-2].isdigit():
                return int(tokens[-2]), " ".join(tokens[1:-2]).strip() or None, tokens[-1]

            if tokens[-1].isdigit():
                return int(tokens[-1]), " ".join(tokens[1:-1]).strip() or None, None

        return 0, None, None

    def find_fuel(pattern: str) -> int:
        m = re.search(pattern, text)
        return int(m.group(1)) if m else 0

    taxi_match = re.search(r"TAXI\s+(\d+)\s+(\d{4})", text)
    taxi = int(taxi_match.group(1)) if taxi_match else find_fuel(r"TAXI\s+(\d+)")
    taxi_time = taxi_match.group(2) if taxi_match else None

    trip_match = re.search(r"TRIP\s+(\d+)\s+(\d{4})", text)
    trip = int(trip_match.group(1)) if trip_match else find_fuel(r"TRIP\s+(\d+)")
    trip_time = trip_match.group(2) if trip_match else None

    contingency, cont_type, cont_time = parse_contingency()

    altn_match = re.search(r"ALTN\s+(\w{4})\s+(\d+)\s+(\d{4})", text)
    if not altn_match:
        altn_match = re.search(r"ALTN\s+(\w{4})\s+(\d+)", text)
    alternate = int(altn_match.group(2)) if altn_match else 0
    altn_airport = altn_match.group(1) if altn_match else None
    altn_time = None
    if altn_match and altn_match.lastindex and altn_match.lastindex >= 3:
        altn_time = altn_match.group(3)

    finl_match = re.search(r"FINL\s+(\d+)\s+(\d{4})", text)
    final_reserve = int(finl_match.group(1)) if finl_match else find_fuel(r"FINL\s+(\d+)")
    finl_time = finl_match.group(2) if finl_match else None

    extra_match = re.search(r"EXTRA\s+\S+\s+(\d+)\s+(\d{4})", text)
    if not extra_match:
        extra_match = re.search(r"EXTRA\s+\S+\s+(\d+)", text)
    extra = int(extra_match.group(1)) if extra_match else 0
    extra_time = None
    if extra_match and extra_match.lastindex and extra_match.lastindex >= 2:
        extra_time = extra_match.group(2)

    ramp_match = re.search(r"RAMP\s+FUEL\s+(\d+)\s+(\d{4})", text)
    if not ramp_match:
        ramp_match = re.search(r"RAMP\s+FUEL\s+(\d+)", text)
    ramp = int(ramp_match.group(1)) if ramp_match else 0
    ramp_time = None
    if ramp_match and ramp_match.lastindex and ramp_match.lastindex >= 2:
        ramp_time = ramp_match.group(2)

    to_match = re.search(r"T/O\s+(\d+)", text)
    takeoff = int(to_match.group(1)) if to_match else None

    min_match = re.search(r"MIN\s+FUEL\s+REQ\s+(\d+)\s+(\d{4})", text)
    min_req = int(min_match.group(1)) if min_match else find_fuel(r"MIN\s+FUEL\s+REQ\s+(\d+)")
    min_time = min_match.group(2) if min_match else None

    expected_landing = ramp - taxi - trip if ramp and taxi and trip else None

    plan_req: float | None = None
    plan_rem: float | None = None
    plan_margin: float | None = None

    all_text = "\n".join(pages)
    pr_match = re.search(r"PLAN\s+REQ\s+([\d.]+)", all_text)
    if pr_match:
        plan_req = float(pr_match.group(1))

    prem_match = re.search(r"PLAN\s+REM\s+([\d.]+)", all_text)
    if prem_match:
        plan_rem = float(prem_match.group(1))

    if plan_rem is not None and plan_req is not None:
        plan_margin = round(plan_rem - plan_req, 1)

    return FuelSummary(
        taxi=taxi,
        taxi_time=taxi_time,
        trip=trip,
        trip_time=trip_time,
        contingency=contingency,
        contingency_type=cont_type,
        contingency_time=cont_time,
        alternate=alternate,
        alternate_airport=altn_airport,
        alternate_time=altn_time,
        final_reserve=final_reserve,
        final_reserve_time=finl_time,
        extra=extra,
        extra_time=extra_time,
        ramp=ramp,
        ramp_time=ramp_time,
        takeoff=takeoff,
        min_fuel_required=min_req if min_req else None,
        min_fuel_time=min_time,
        expected_landing=expected_landing,
        plan_req=plan_req,
        plan_rem=plan_rem,
        plan_margin=plan_margin,
    )
