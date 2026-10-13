"""Natural flaws: teammate takes with independent human annotations (spec section 8).

Layout
  data/takes/<T>/<take_id>.<wav|mp3|m4a|flac|ogg>   one reading of text T (any ffmpeg format)
  data/takes/<T>/<take_id>.txt                      optional: the words actually read, only if
                                                    the take departs from the canonical text
  data/annotations/<annotator>/<take_id>.txt        Audacity label export, one flaw per line:
                                                    start_s<TAB>end_s<TAB>flaw_type

take_id convention: <speaker>_<T>_take<n>, e.g. priya_T2_take1. Times are seconds from
the start of the take file as recorded. flaw_type is one of FLAW_TYPES. An empty label
file means "listened, found no flaw". Annotators work independently and before seeing
any Cadence output.

Metrics: Cadence against each annotator (Matching Score and time F1), and annotator
against annotator (the same metrics plus mean IoU of matched spans), which is the ceiling.
"""
from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import numpy as np

from .data.texts import TEXTS
from .envelope import FLAW_TYPES
from .metrics import aggregate, best_match, overlaps, score_clip

ROOT = Path(__file__).resolve().parent.parent
TAKES = ROOT / "data" / "takes"
ANN = ROOT / "data" / "annotations"
AUDIO_EXT = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}


def takes() -> list[dict]:
    out = []
    for tid in TEXTS:
        for p in sorted((TAKES / tid).glob("*")):
            if p.suffix.lower() in AUDIO_EXT:
                tr = p.with_suffix(".txt")
                out.append({"take": p.stem, "text_id": tid, "path": p,
                            "transcript": tr.read_text().strip() if tr.exists() else TEXTS[tid]["text"]})
    return out


def annotators() -> list[str]:
    return sorted(d.name for d in ANN.glob("*") if d.is_dir()) if ANN.exists() else []


def read_labels(path: Path) -> list[dict]:
    """Parse an Audacity label file. Raises ValueError on malformed lines."""
    labels = []
    for n, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip() or line.startswith("\\"):  # skip blanks and spectral-selection lines
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            raise ValueError(f"{path}:{n}: expected start<TAB>end<TAB>type")
        s, e, typ = float(parts[0]), float(parts[1]), parts[2].strip().lower().replace(" ", "_")
        if typ not in FLAW_TYPES:
            raise ValueError(f"{path}:{n}: unknown flaw type '{parts[2].strip()}' (use one of {FLAW_TYPES})")
        if e <= s:
            raise ValueError(f"{path}:{n}: end must be after start (point labels are not allowed)")
        labels.append({"type": typ, "start": s, "end": e})
    return labels


def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def check() -> dict:
    """What is present, what is missing, and any format errors."""
    tk, anns = takes(), annotators()
    problems = []
    if len(anns) < 2:
        problems.append(f"need 2 independent annotators, found {len(anns)}: {anns}")
    for t in tk:
        for a in anns:
            f = ANN / a / f"{t['take']}.txt"
            if not f.exists():
                problems.append(f"missing annotation: {_rel(f)}")
                continue
            try:
                read_labels(f)
            except ValueError as e:
                problems.append(str(e))
    known = {t["take"] for t in tk}
    for a in anns:
        for f in (ANN / a).glob("*.txt"):
            if f.stem not in known:
                problems.append(f"annotation without a take: {_rel(f)}")
    per_text = {tid: sum(t["text_id"] == tid for t in tk) for tid in TEXTS}
    return {"takes": len(tk), "per_text": per_text, "annotators": anns, "problems": problems}


def predict_take(t: dict) -> tuple[list[dict], float]:
    """Cadence regions in take-file time, and the analysed duration in minutes."""
    from .pipeline import analyze
    rep, rec = analyze(t["path"], t["text_id"], transcript=t["transcript"])
    off = rec["offset"]
    regions = [{**r, "start": r["start"] + off, "end": r["end"] + off} for r in rep["regions"]]
    w = rep["words"]
    return regions, (w[-1]["end"] - w[0]["start"]) / 60


def _iou_matched(a: list[dict], b: list[dict]) -> list[float]:
    out = []
    for lab in a:
        p, v = best_match(lab, b)
        if p is not None and v > 0:
            out.append(v)
    return out


def evaluate() -> dict:
    st = check()
    if st["takes"] == 0:
        return {"status": "pending: no takes in data/takes/<T>/", **st}
    anns = st["annotators"]
    preds, minutes, labels = {}, {}, {a: {} for a in anns}
    for t in takes():
        preds[t["take"]], minutes[t["take"]] = predict_take(t)
        for a in anns:
            f = ANN / a / f"{t['take']}.txt"
            if f.exists():
                labels[a][t["take"]] = read_labels(f)
    out = {"status": "ok" if not st["problems"] else "ok with problems", "check": st,
           "system_vs_annotator": {}, "annotator_vs_annotator": {}}
    for a in anns:
        rows = [score_clip(labels[a][k], preds[k]) for k in labels[a]]
        out["system_vs_annotator"][a] = aggregate(rows) | {"takes": len(rows)}
    for a, b in combinations(anns, 2):
        common = sorted(set(labels[a]) & set(labels[b]))
        rows = [score_clip(labels[a][k], labels[b][k]) for k in common]
        ious = [v for k in common for v in _iou_matched(labels[a][k], labels[b][k])]
        out["annotator_vs_annotator"][f"{a} vs {b}"] = aggregate(rows) | {
            "takes": len(common), "mean_iou_matched": float(np.mean(ious)) if ious else float("nan")}
    # system flags that no annotator marked, per minute of take
    fa = sum(1 for k, ps in preds.items() for p in ps
             if not any(overlaps(p, l) for a in anns for l in labels[a].get(k, [])))
    out["unannotated_flags_per_min"] = fa / max(sum(minutes.values()), 1e-9)
    out["per_take"] = {k: {"flags": [(p["type"], round(p["start"], 2), round(p["end"], 2)) for p in v],
                           "minutes": round(minutes[k], 3)} for k, v in preds.items()}
    return out


def main() -> dict:
    st = check()
    print(json.dumps(st, indent=1))
    if st["takes"] == 0:
        return st
    res = evaluate()
    path = ROOT / "results" / "natural.json"
    path.write_text(json.dumps(res, indent=1, sort_keys=True, default=float))
    print(json.dumps({k: res[k] for k in ("system_vs_annotator", "annotator_vs_annotator",
                                           "unannotated_flags_per_min")}, indent=1, default=float))
    print("written", path)
    return res
