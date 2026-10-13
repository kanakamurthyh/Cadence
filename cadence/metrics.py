"""Evaluation metrics (spec section 8)."""
from __future__ import annotations

import numpy as np
from scipy.stats import spearmanr


def iou(a: dict, b: dict) -> float:
    inter = max(0.0, min(a["end"], b["end"]) - max(a["start"], b["start"]))
    union = max(a["end"], b["end"]) - min(a["start"], b["start"])
    return inter / union if union > 0 else 0.0


def overlaps(a: dict, b: dict) -> bool:
    return min(a["end"], b["end"]) > max(a["start"], b["start"])


def best_match(lab: dict, preds: list[dict], same_type: bool = True) -> tuple[dict | None, float]:
    cands = [p for p in preds if not same_type or p["type"] == lab["type"]]
    if not cands:
        return None, 0.0
    scored = [(iou(lab, p), p) for p in cands]
    v, p = max(scored, key=lambda s: s[0])
    return p, v


def score_clip(labels: list[dict], preds: list[dict]) -> dict:
    """Per-clip counts: SSDM Matching Score hits (type correct and IoU >= 0.5),
    lenient time hits (same type, any overlap), edge errors, unmatched predictions."""
    out = {"n_labels": len(labels), "n_preds": len(preds), "match": 0, "lenient": 0,
           "onset_ms": [], "offset_ms": [], "pred_hits": 0}
    for lab in labels:
        p, v = best_match(lab, preds)
        if p is not None and v >= 0.5:
            out["match"] += 1
            out["onset_ms"].append(abs(p["start"] - lab["start"]) * 1000)
            out["offset_ms"].append(abs(p["end"] - lab["end"]) * 1000)
        if any(overlaps(lab, q) and q["type"] == lab["type"] for q in preds):
            out["lenient"] += 1
    out["pred_hits"] = sum(any(overlaps(p, l) and p["type"] == l["type"] for l in labels) for p in preds)
    return out


def aggregate(rows: list[dict]) -> dict:
    nl = sum(r["n_labels"] for r in rows)
    npred = sum(r["n_preds"] for r in rows)
    m = sum(r["match"] for r in rows)
    le = sum(r["lenient"] for r in rows)
    ph = sum(r["pred_hits"] for r in rows)
    on = [x for r in rows for x in r["onset_ms"]]
    off = [x for r in rows for x in r["offset_ms"]]
    rec = le / nl if nl else float("nan")
    prec = ph / npred if npred else float("nan")
    return {
        "labels": nl,
        "matching_score": m / nl if nl else float("nan"),
        "time_recall": rec,
        "time_precision": prec,
        "time_f1": 2 * rec * prec / (rec + prec) if npred and nl and rec + prec > 0 else 0.0,
        "onset_ms_median": float(np.median(on)) if on else float("nan"),
        "offset_ms_median": float(np.median(off)) if off else float("nan"),
    }


def false_alarms_per_min(preds_per_clip: list[list[dict]], minutes: list[float]) -> float:
    total = sum(minutes)
    return sum(len(p) for p in preds_per_clip) / total if total else float("nan")


def spearman(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 3 or np.all(a == a[0]) or np.all(b == b[0]):
        return float("nan")
    return float(spearmanr(a, b).statistic)
