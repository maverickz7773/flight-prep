from __future__ import annotations
import logging
import os
import tempfile

from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from parsers.ofp_parser import parse_ofp
from models.briefing import AirportNotes, BriefingData
from parsers.notes import (
    get_airport_notes,
    get_notes_data_path,
    notes_data_file_exists,
)

app = FastAPI(title="Flight Prep API")
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "operational_info_present": notes_data_file_exists(),
    }


@app.on_event("startup")
async def startup_checks():
    notes_path = get_notes_data_path()
    if notes_data_file_exists():
        logger.info("Operational info file loaded from %s", notes_path)
    else:
        logger.warning("Operational info file missing at startup: %s", notes_path)


@app.post("/api/parse", response_model=BriefingData)
async def parse_ofp_endpoint(file: UploadFile):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        briefing = parse_ofp(tmp_path)
        return briefing
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse OFP: {str(e)}")
    finally:
        os.unlink(tmp_path)


@app.get("/api/airport-notes", response_model=AirportNotes | None)
async def airport_notes_endpoint(departure: str, arrival: str):
    dep_raw = get_airport_notes(departure)
    arr_raw = get_airport_notes(arrival)

    departure_note = dep_raw.get("departure") if dep_raw else None
    arrival_note = arr_raw.get("arrival") if arr_raw else None

    if not departure_note and not arrival_note:
        return None

    return AirportNotes(
        departure=departure_note,
        arrival=arrival_note,
    )


frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend_build")
if os.path.isdir(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
