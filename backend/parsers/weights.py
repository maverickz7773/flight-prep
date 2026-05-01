from __future__ import annotations
import re
from models.briefing import Weights


def parse_weights(pages: list[str]) -> Weights:
    text = "\n".join(pages[:5])

    def find_int(pattern: str) -> int:
        m = re.search(pattern, text)
        return int(m.group(1)) if m else 0

    mzfw = find_int(r"MZFW\s+(\d+)")
    ezfw = find_int(r"EZFW\s+(\d+)")
    mtow = find_int(r"MTOW\s+(\d+)")
    etow = find_int(r"ETOW\s+(\d+)")
    mlwt = find_int(r"MLWT\s+(\d+)")
    elwt = find_int(r"ELWT\s+(\d+)")

    ezfw_pct = round(ezfw / mzfw * 100, 1) if mzfw else None
    etow_pct = round(etow / mtow * 100, 1) if mtow else None
    elwt_pct = round(elwt / mlwt * 100, 1) if mlwt else None

    return Weights(
        mzfw=mzfw,
        ezfw=ezfw,
        mtow=mtow,
        etow=etow,
        mlwt=mlwt,
        elwt=elwt,
        ezfw_pct=ezfw_pct,
        etow_pct=etow_pct,
        elwt_pct=elwt_pct,
    )
