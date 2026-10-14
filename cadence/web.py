"""Cadence web app: the coach UI (cadence/web/) on top of the analysis pipeline.

Run with `cadence web` (http://localhost:8000). The microphone only works on localhost or HTTPS.
Recordings are analysed on this machine and kept in memory only for A/B playback.
"""
from __future__ import annotations

import io
import json
import shutil
import tempfile
import uuid
import wave
from collections import OrderedDict
from pathlib import Path

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from . import audio
from .align import TextNotFound, words_of
from .data.texts import CONTEXT, MIN_GOOD, SPEECHES, TEXTS, display_text
from .pipeline import REFS, ROOT, analyze, good_set, load_record

WEB = Path(__file__).parent / "web"
FIGURES = ROOT / "docs" / "figures"
DEMO_TID = "T3"
SESSIONS: OrderedDict[str, dict] = OrderedDict()  # recent analyses, for A/B clips only
MAX_SESSIONS = 20

app = FastAPI(title="Cadence", version="0.3.0")


def _analyzable(tid: str) -> bool:
    try:
        return len(good_set(tid)) >= MIN_GOOD
    except FileNotFoundError:
        return False


def _durations(tid: str) -> list[float]:
    out = []
    for g in good_set(tid):
        out.append(json.loads((REFS / tid / f"{g}.json").read_text())["meta"]["duration"])
    return out


@app.get("/api/texts")
def texts():
    """Passages that can be analysed: speeches first, then research texts."""
    out = []
    for tid, t in TEXTS.items():
        if not _analyzable(tid):
            continue
        d = _durations(tid)
        out.append({
            "id": tid, "title": t["title"], "author": t.get("author", ""), "context": CONTEXT.get(tid, ""),
            "display": display_text(tid), "words": len(words_of(t["text"])),
            "typical_s": float(np.median(d)), "range_s": [float(min(d)), float(max(d))],
            "group": "speech" if tid in SPEECHES else "research", "role": t["role"],
        })
    out.sort(key=lambda r: (r["group"] != "speech", r["id"]))
    return out


def _store(rep: dict, x: np.ndarray, tid: str) -> str:
    sid = uuid.uuid4().hex[:12]
    SESSIONS[sid] = {"rep": rep, "x": x, "tid": tid}
    while len(SESSIONS) > MAX_SESSIONS:
        SESSIONS.popitem(last=False)
    return sid


def _reader(tid: str, rid: str) -> str:
    try:
        return json.loads((REFS / tid / f"{rid}.json").read_text())["meta"].get("reader", rid)
    except FileNotFoundError:
        return rid


@app.post("/api/analyze")
def analyze_upload(file: UploadFile = File(...), text_id: str = Form(...), method: str = Form("envelope")):
    if text_id not in TEXTS or not _analyzable(text_id):
        raise HTTPException(404, f"Unknown or unavailable passage {text_id}.")
    suffix = Path(file.filename or "take.webm").suffix or ".webm"
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / f"take{suffix}"
        with p.open("wb") as fh:
            shutil.copyfileobj(file.file, fh)
        try:
            rep, rec = analyze(p, text_id, k=1 if method == "single" else None)
        except TextNotFound as e:
            raise HTTPException(422, str(e))
        except Exception as e:  # noqa: BLE001 - decode failures etc. reach the user as a message
            raise HTTPException(400, f"Could not analyse this recording: {e}")
    sid = _store(rep, rec["x"], text_id)
    return {"session": sid, "report": rep, "duration_s": len(rec["x"]) / audio.SR,
            "good_reader": _reader(text_id, rep["references"][0]), "text_title": TEXTS[text_id]["title"]}


def _wav(x: np.ndarray) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(audio.SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
    return buf.getvalue()


def _segment(x: np.ndarray, a: float, b: float, pad: float = 0.4) -> np.ndarray:
    return x[max(0, int((a - pad) * audio.SR)): min(len(x), int((b + pad) * audio.SR))]


@app.get("/api/clip/{sid}/{idx}/{who}")
def clip(sid: str, idx: int, who: str):
    """Region `idx` of an analysis: `you` = the user's audio, `good` = the same words by a good reader."""
    s = SESSIONS.get(sid)
    if not s or idx < 0 or idx >= len(s["rep"]["regions"]) or who not in ("you", "good"):
        raise HTTPException(404, "Clip not available (sessions are kept in memory only).")
    r = s["rep"]["regions"][idx]
    if who == "you":
        seg = _segment(s["x"], r["start"], r["end"])
    else:
        ref = load_record(REFS / s["tid"] / s["rep"]["references"][0])
        w1 = min(r["w1"] + 1, len(ref["words"]) - 1) if "pause" in r["type"] else r["w1"]
        seg = _segment(ref["x"], ref["words"][r["w0"]]["start"], ref["words"][w1]["end"])
    return Response(_wav(seg), media_type="audio/wav")


@app.get("/api/recording/{sid}")
def recording(sid: str):
    s = SESSIONS.get(sid)
    if not s:
        raise HTTPException(404, "Recording not available (sessions are kept in memory only).")
    return Response(_wav(s["x"]), media_type="audio/wav")


@app.post("/api/demo")
def demo():
    """Re-run the judge demo live: a known, labelled edit on a good reading of the same text."""
    f = ROOT / "data" / "demo" / f"demo_{DEMO_TID}.json"
    if not f.exists():
        raise HTTPException(404, "No demo case yet: run `cadence demo`.")
    d = json.loads(f.read_text())
    rep, rec = analyze(ROOT / d["flawed_wav"], d["text_id"], locate=False, exclude=(d["source_id"],))
    from .metrics import iou
    lab = d["label"]
    same = [(iou(lab, r), i) for i, r in enumerate(rep["regions"]) if r["type"] == lab["type"]]
    best = max(same) if same else (0.0, None)
    sid = _store(rep, rec["x"], d["text_id"])
    return {"session": sid, "report": rep, "duration_s": len(rec["x"]) / audio.SR,
            "good_reader": _reader(d["text_id"], rep["references"][0]), "text_title": TEXTS[d["text_id"]]["title"],
            "demo": {"label": lab, "label_words": d["label_words"], "source_speaker": d["source_speaker"],
                     "iou": round(best[0], 3), "matched_region": best[1],
                     "baselines": {k: {"matched": v["matched"], "iou": v["iou"], "n_flags": v["n_flags"]}
                                   for k, v in d["methods"].items()}}}


@app.get("/api/evidence")
def evidence():
    res = json.loads((ROOT / "results" / "results.json").read_text())
    rows = []
    for name, per in res["methods"].items():
        for t, r in per.items():
            rows.append({"method": name, "text": t, "matching_score": r["ladders"]["matching_score"],
                         "fa_per_min": r["fa_per_min_good_pairs"]})
    figs = sorted(p.name for p in FIGURES.glob("*.png")) if FIGURES.exists() else []
    inv = json.loads((ROOT / "data" / "inventory.json").read_text())
    return {"rows": rows, "figures": figs, "ship_decision": res.get("ship_decision", {}).get("reason"),
            "inventory": {k: {kk: v.get(kk) for kk in ("title", "role", "recordings", "speakers", "synthetic_clips")}
                          for k, v in inv.get("texts", {}).items()},
            "dataset_url": "https://huggingface.co/datasets/Vedant1605/cadence-contrastive-speech"}


@app.get("/figures/{name}")
def figure(name: str):
    p = FIGURES / Path(name).name
    if p.suffix != ".png" or not p.exists():
        raise HTTPException(404)
    return FileResponse(p)


@app.get("/")
def index():
    return FileResponse(WEB / "index.html")


app.mount("/static", StaticFiles(directory=WEB), name="static")
