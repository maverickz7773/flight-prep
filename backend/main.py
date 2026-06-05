from __future__ import annotations
import asyncio
import logging
import os
import tempfile
import time
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from parsers.ofp_parser import parse_ofp
from models.briefing import (
    AirportFeedback,
    AirportFeedbackCreate,
    AirportFeedbackEntry,
    AirportNotes,
    BriefingData,
    DeleteStatus,
    FIRFeedbackCreate,
    FIRFeedbackEntry,
    ParseJobStart,
    ParseJobStatus,
)
from parsers.notes import (
    get_airport_notes,
    get_notes_data_path,
    notes_data_file_exists,
)
from services.airport_feedback import (
    airport_feedback_enabled,
    create_airport_feedback,
    create_fir_feedback,
    delete_airport_feedback,
    delete_fir_feedback,
    get_airport_feedback,
    get_fir_feedback,
    get_airport_feedback_db_path,
)

app = FastAPI(title="Flight Prep API")
logger = logging.getLogger(__name__)
_PARSE_JOB_TTL_SECONDS = 10 * 60
_parse_jobs: dict[str, dict[str, object | None]] = {}
_APP_RELEASE = "2026-05-19-nats-v2"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def disable_html_caching(request: Request, call_next):
    response = await call_next(request)

    content_type = response.headers.get("content-type", "")
    if request.url.path.startswith("/api/"):
        return response
    if "text/html" not in content_type:
        return response

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "operational_info_present": notes_data_file_exists(),
        "airport_feedback_enabled": airport_feedback_enabled(),
        "release": _APP_RELEASE,
    }


@app.on_event("startup")
async def startup_checks():
    notes_path = get_notes_data_path()
    if notes_data_file_exists():
        logger.info("Operational info file loaded from %s", notes_path)
    else:
        logger.warning("Operational info file missing at startup: %s", notes_path)

    if airport_feedback_enabled():
        logger.info("Airport feedback enabled using %s", get_airport_feedback_db_path())
    else:
        logger.info("Airport feedback disabled")


def _cleanup_old_jobs() -> None:
    now = time.time()
    expired_ids = [
        job_id
        for job_id, job in _parse_jobs.items()
        if now - float(job.get("updated_at", now)) > _PARSE_JOB_TTL_SECONDS
    ]
    for job_id in expired_ids:
        _parse_jobs.pop(job_id, None)


async def _run_parse_job(job_id: str, pdf_path: str) -> None:
    _parse_jobs[job_id]["status"] = "processing"
    _parse_jobs[job_id]["updated_at"] = time.time()

    try:
        result = await asyncio.to_thread(parse_ofp, pdf_path)
        _parse_jobs[job_id]["status"] = "completed"
        _parse_jobs[job_id]["result"] = result
        _parse_jobs[job_id]["error"] = None
    except Exception as exc:
        logger.exception("Failed to parse OFP for job %s", job_id)
        _parse_jobs[job_id]["status"] = "failed"
        _parse_jobs[job_id]["result"] = None
        _parse_jobs[job_id]["error"] = f"Failed to parse OFP: {exc}"
    finally:
        _parse_jobs[job_id]["updated_at"] = time.time()
        try:
            Path(pdf_path).unlink(missing_ok=True)
        except OSError:
            logger.warning("Failed to delete temp PDF for job %s: %s", job_id, pdf_path)


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


@app.post("/api/parse-jobs", response_model=ParseJobStart)
async def create_parse_job(file: UploadFile):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    _cleanup_old_jobs()
    job_id = uuid4().hex
    _parse_jobs[job_id] = {
        "status": "queued",
        "result": None,
        "error": None,
        "updated_at": time.time(),
    }
    asyncio.create_task(_run_parse_job(job_id, tmp_path))

    return ParseJobStart(job_id=job_id, status="queued")


@app.get("/api/parse-jobs/{job_id}", response_model=ParseJobStatus)
async def get_parse_job(job_id: str):
    job = _parse_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Parse job not found")

    return ParseJobStatus(
        job_id=job_id,
        status=str(job["status"]),
        result=job.get("result"),
        error=job.get("error"),
    )


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


@app.get("/api/airport-feedback", response_model=AirportFeedback | None)
async def airport_feedback_endpoint(departure: str, arrival: str):
    return get_airport_feedback(departure, arrival)


@app.post("/api/airport-feedback", response_model=AirportFeedbackEntry)
async def create_airport_feedback_endpoint(payload: AirportFeedbackCreate):
    if not airport_feedback_enabled():
        raise HTTPException(status_code=403, detail="Airport feedback feature is disabled")

    try:
        return create_airport_feedback(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.delete("/api/airport-feedback/{entry_id}", response_model=DeleteStatus)
async def delete_airport_feedback_endpoint(entry_id: int):
    if not airport_feedback_enabled():
        raise HTTPException(status_code=403, detail="Airport feedback feature is disabled")

    deleted = delete_airport_feedback(entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Airport feedback entry not found")

    return DeleteStatus(deleted=True)


@app.get("/api/fir-feedback", response_model=dict[str, list[FIRFeedbackEntry]] | None)
async def fir_feedback_endpoint(firs: str):
    fir_list = [item.strip().upper() for item in firs.split(",") if item.strip()]
    return get_fir_feedback(fir_list)


@app.post("/api/fir-feedback", response_model=FIRFeedbackEntry)
async def create_fir_feedback_endpoint(payload: FIRFeedbackCreate):
    if not airport_feedback_enabled():
        raise HTTPException(status_code=403, detail="Airport feedback feature is disabled")

    try:
        return create_fir_feedback(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.delete("/api/fir-feedback/{entry_id}", response_model=DeleteStatus)
async def delete_fir_feedback_endpoint(entry_id: int):
    if not airport_feedback_enabled():
        raise HTTPException(status_code=403, detail="Airport feedback feature is disabled")

    deleted = delete_fir_feedback(entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="FIR feedback entry not found")

    return DeleteStatus(deleted=True)


frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend_build")
if os.path.isdir(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
