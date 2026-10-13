"""FastAPI core: POST an audio file, get the JSON report."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from .data.texts import TEXTS
from .pipeline import analyze

app = FastAPI(title="Cadence", version="0.2.0")


@app.get("/texts")
def texts():
    return {k: {"title": v["title"], "role": v["role"]} for k, v in TEXTS.items()}


@app.post("/analyze")
def analyze_upload(file: UploadFile = File(...), text_id: str = Form("T2"), k: int | None = Form(None)):
    if text_id not in TEXTS:
        raise HTTPException(404, f"unknown text {text_id}")
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / (file.filename or "upload.wav")
        with p.open("wb") as fh:
            shutil.copyfileobj(file.file, fh)
        rep, _ = analyze(p, text_id, k=k)
    return rep
