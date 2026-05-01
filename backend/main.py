from __future__ import annotations
import os
import tempfile

from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from parsers.ofp_parser import parse_ofp
from models.briefing import BriefingData

app = FastAPI(title="Flight Prep API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


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


frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend_build")
if os.path.isdir(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
