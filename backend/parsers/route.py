from __future__ import annotations
import re
from models.briefing import RouteSummary, Waypoint
from parsers.enroute_info import build_enroute_info_items


def parse_route(pages: list[str]) -> RouteSummary:
    route_string = ""
    for page in pages[:5]:
        m = re.search(
            r"\w{4}\s+\d{2}[LRC]?\s+((?:[A-Z][A-Z0-9]+\s+)+)\w{4}\s+\d{2}[LRC]?",
            page,
        )
        if m:
            route_string = m.group(1).strip()
            break

    waypoints: list[Waypoint] = []
    fir_sequence: list[str] = []
    current_fir_name: str | None = None
    current_fir_icao: str | None = None
    highest_mora: str | None = None

    current_fl: str | None = None
    current_true_track: int | None = None
    is_climbing = False
    past_toc = False
    past_tod = False
    cruise_fls: list[str] = []

    body_pages = []
    for i, page in enumerate(pages):
        if re.search(r"PAGE\s+\d+/\d+", page) and "AWY" in page and "WPT" in page:
            if "DESTINATION TO ALTERNATE" in page:
                continue
            body_pages.append(page)

    for page in body_pages:
        lines = page.split("\n")
        for line in lines:
            # --- Extract FL from AWY lines (first line of two-line entries) ---
            # AWY lines have WIND pattern (ddd/ddd) and end with .... ....
            # but NOT followed by a number (WPT lines end with RFOB value)
            awy_wind = re.search(r"(\d{3}/\d{3})", line)
            is_awy = (
                awy_wind
                and re.search(r"\.\.\.\.\s+\.\.\.\.\s*$", line)
                and not re.search(r"\.\.\.\.\s+\.\.\.\.\s+\d", line)
            )
            if is_awy:
                if " CLB " in line:
                    is_climbing = True
                elif " DSC " in line:
                    is_climbing = False
                else:
                    before_wind = line[: awy_wind.start()]
                    nums = re.findall(r"\b(\d{3})\b", before_wind)
                    fl = None
                    if len(nums) >= 2:
                        current_true_track = int(nums[0])
                        candidate = int(nums[-1])
                        if 100 <= candidate <= 450:
                            fl = f"FL{candidate}"
                    elif len(nums) == 1:
                        if is_climbing:
                            candidate = int(nums[0])
                            if 100 <= candidate <= 450:
                                fl = f"FL{candidate}"
                        else:
                            current_true_track = int(nums[0])
                    if fl:
                        current_fl = fl
                        is_climbing = False
                        if not past_tod and fl not in cruise_fls:
                            cruise_fls.append(fl)
            else:
                # Partial AWY line: bare FL + ISAD with no airway/WIND
                # e.g. "340 P13 15 .... ...."
                partial = re.match(
                    r"^\s*(\d{3})\s+[PM]\d+\s+\d+\s+\.\.\.\.", line
                )
                if partial:
                    candidate = int(partial.group(1))
                    if 100 <= candidate <= 450:
                        current_fl = f"FL{candidate}"
                        is_climbing = False
                        if not past_tod and current_fl not in cruise_fls:
                            cruise_fls.append(current_fl)

            fir_match = re.search(
                r"^([A-Z][A-Z\s]+?)\s+(?:FIR|UIR)\s+(?:\S+\s+)?(\w{4})\s*$",
                line.strip(),
            )
            if not fir_match:
                fir_match = re.search(
                    r"^([A-Z][A-Z\s]+?)\s+(?:FIR|UIR)\s+(\w{4})",
                    line.strip(),
                )
            if fir_match:
                current_fir_name = fir_match.group(1).strip()
                current_fir_icao = fir_match.group(2)
                if len(current_fir_icao) == 4 and current_fir_icao.isalpha():
                    fir_label = f"{current_fir_name} ({current_fir_icao})"
                    if fir_label not in fir_sequence:
                        fir_sequence.append(fir_label)
                continue

            if line.startswith("---"):
                continue

            if re.match(r"^(PAGE|PLAN|AWY|WPT|QTR|$)", line.strip()):
                continue

            toc_match = re.search(
                r"TOC\s+(\d+)\s+[\d.]+\s+\S+\s+(\d{4})\s+.*?([\d.]+)",
                line,
            )
            if toc_match:
                eta = toc_match.group(2)
                fuel_rem = _parse_fuel(toc_match.group(3))
                past_toc = True
                waypoints.append(Waypoint(
                    name="TOC",
                    flight_level=current_fl,
                    eta=eta,
                    fuel_remaining=fuel_rem,
                    is_toc=True,
                    fir_name=current_fir_name,
                    fir_icao=current_fir_icao,
                ))
                continue

            tod_match = re.search(
                r"TOD\s+(\d+)\s+[\d.]+\s+\S+\s+(\d{4})\s+.*?([\d.]+)",
                line,
            )
            if tod_match:
                eta = tod_match.group(2)
                fuel_rem = _parse_fuel(tod_match.group(3))
                past_tod = True
                waypoints.append(Waypoint(
                    name="TOD",
                    flight_level=current_fl,
                    eta=eta,
                    fuel_remaining=fuel_rem,
                    is_tod=True,
                    fir_name=current_fir_name,
                    fir_icao=current_fir_icao,
                ))
                continue

            wpt_match = re.search(
                r"^([A-Z]{2,6}(?:\s\d{2,3}\.\d{2})?)\s+(\d{3})\s+(\d+)\s+"
                r"(?:(\d{3})\s+)?(?:[\d.]+\s+)?(?:\S+\s+)?(\d{4})\s+.*?([\d.]+)\s*$",
                line.strip(),
            )
            if not wpt_match:
                wpt_match2 = re.search(
                    r"^([A-Z][A-Z0-9]{1,5})\s+(\d{3})\s+(\d+)\s+",
                    line.strip(),
                )
                if wpt_match2:
                    name = wpt_match2.group(1)
                    gs_m = re.search(r"\b(\d{3,4})/(\d{3,4})\b", line)
                    eta_m = re.search(r"(\d{4})\s+\.\.\.\.\s+\.\.\.\.\s+([\d.]+)", line)
                    if eta_m:
                        waypoints.append(Waypoint(
                            name=name,
                            true_track=current_true_track,
                            ground_speed=int(gs_m.group(1)) if gs_m else None,
                            tas=int(gs_m.group(2)) if gs_m else None,
                            eta=eta_m.group(1),
                            fuel_remaining=_parse_fuel(eta_m.group(2)),
                            flight_level=current_fl,
                            is_step_climb=is_climbing and past_toc,
                            fir_name=current_fir_name,
                            fir_icao=current_fir_icao,
                        ))
                continue

            if wpt_match:
                name = wpt_match.group(1).strip()
                gs_m = re.search(r"\b(\d{3,4})/(\d{3,4})\b", line)
                waypoints.append(Waypoint(
                    name=name,
                    true_track=current_true_track,
                    ground_speed=int(gs_m.group(1)) if gs_m else None,
                    tas=int(gs_m.group(2)) if gs_m else None,
                    eta=wpt_match.group(5),
                    fuel_remaining=_parse_fuel(wpt_match.group(6)),
                    flight_level=current_fl,
                    is_step_climb=is_climbing and past_toc,
                    fir_name=current_fir_name,
                    fir_icao=current_fir_icao,
                ))

    coords = _parse_coordinates(pages)
    for wpt in waypoints:
        if wpt.name in coords:
            wpt.latitude, wpt.longitude = coords[wpt.name]

    shear_rates = _parse_shear_rates(pages)
    for wpt in waypoints:
        if wpt.name in shear_rates:
            wpt.shear_rate = shear_rates[wpt.name]

    mora_match = re.search(r"HIGHEST\s+MORA\s+IS\s+(\d+)\s+AT\s+(\w+)", "\n".join(pages))
    if mora_match:
        highest_mora = f"{mora_match.group(1)} at {mora_match.group(2)}"

    return RouteSummary(
        route_string=route_string,
        waypoints=waypoints,
        fir_sequence=fir_sequence,
        enroute_info=build_enroute_info_items(fir_sequence),
        highest_mora=highest_mora,
        cruise_flight_levels=cruise_fls,
    )


def _parse_coordinates(pages: list[str]) -> dict[str, tuple[str, str]]:
    coords: dict[str, tuple[str, str]] = {}
    for page in pages:
        if "LAT/LONG" not in page or "WAYPT" not in page or "ITT" not in page:
            continue
        for m in re.finditer(
            r"([NS]\d{4}\.\d)/([EW]\d{4,5}\.\d)\s+(\w+)",
            page,
        ):
            lat_raw, lon_raw, name = m.group(1), m.group(2), m.group(3)
            coords[name] = (lat_raw, lon_raw)
    return coords


def _parse_shear_rates(pages: list[str]) -> dict[str, int]:
    shear_rates: dict[str, int] = {}
    cruise_col_idx: int | None = None

    for page in pages:
        if "LAT/LONG" not in page or "WAYPT" not in page or "ITT" not in page:
            continue
        for line in page.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue
            dash_match = re.search(r"-(\d{3})-", stripped)
            if dash_match and re.match(r"^[\d\s\-]+$", stripped):
                tokens = stripped.split()
                for idx, tok in enumerate(tokens):
                    if tok.startswith("-") and tok.endswith("-"):
                        cruise_col_idx = idx
                        break
                continue
            wpt_match = re.match(
                r"[NS]\d{4}\.\d/[EW]\d{4,5}\.\d\s+(\w+)\s+\d+\s+\d+\s+[PM]\d+\s+(.*)",
                stripped,
            )
            if wpt_match and cruise_col_idx is not None:
                name = wpt_match.group(1)
                wind_part = wpt_match.group(2).strip()
                if wind_part:
                    entries = re.findall(r"\d{5}/(\d+)", wind_part)
                    if len(entries) > cruise_col_idx:
                        shear_rates[name] = int(entries[cruise_col_idx])
    return shear_rates


def _parse_fuel(s: str) -> float | None:
    try:
        return float(s)
    except (ValueError, TypeError):
        return None
