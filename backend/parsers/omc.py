from __future__ import annotations
import json
from pathlib import Path

from models.briefing import AerodromeBriefing

_DATA_PATH = Path(__file__).parent.parent / "data" / "omc_briefings.json"
_cache: dict[str, AerodromeBriefing] | None = None


def get_aerodrome_briefing(icao: str) -> AerodromeBriefing | None:
    global _cache
    if _cache is None:
        with open(_DATA_PATH) as f:
            raw = json.load(f)
        _cache = {k: AerodromeBriefing(icao=k, **v) for k, v in raw.items()}
    return _cache.get(icao)
