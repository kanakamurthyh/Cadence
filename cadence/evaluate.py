"""Calibration (T1 only) and evaluation (T2, T3) of every method and ablation.

A *config* names one detector variant:
  method: "B0" generic norms | "env" consensus envelope (K=1 is baseline B1)
  k:      number of good renditions in the envelope (None = all available)
  norm:   "level" (ours) | "zscore" (v1 bug) | "off"
  margin: True = null-edit measurement margin m_f, False = m_f = 0
Leakage rule: the rendition a clip was made from is never in its envelope.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from sklearn.isotonic import IsotonicRegression

from . import features
from .audio import read_wav
from .baselines import generic_norms
from .detect import DIMENSION, DIMENSIONS, Params, detect, scores
from .envelope import ENV_FEATURES, FLAW_TYPES, add_derived, build, fwd, widths
from .metrics import aggregate, false_alarms_per_min, score_clip, spearman
from .pipeline import REFS, ROOT

LADDERS = ROOT / "data" / "ladders"
FA_BUDGET = 1.0  # false alarms per minute of good delivery we accept
TAU_GRID = [round(x, 2) for x in np.arange(0.2, 4.01, 0.1)]


@dataclass(frozen=True)
class Config:
    method: str = "env"
    k: int | None = None
    norm: str = "level"
    margin: bool = True
    relative: bool = True       # v2 self-relative pace/monotone channels
    stress_floor: bool = True   # v2 perceptible stress points

    @property
    def name(self) -> str:
        if self.method == "B0":
            return "B0 generic norms"
        k = "all" if self.k is None else self.k
        s = f"K={k}"
        if self.norm != "level":
            s += f", norm={self.norm}"
        if not self.margin:
            s += ", no margin"
        if not self.relative and not self.stress_floor:
            s += ", v1 detector"
        elif not self.relative:
            s += ", no relative channels"
        elif not self.stress_floor:
            s += ", no stress floor"
        return s


# -- data ---------------------------------------------------------------------

@lru_cache(maxsize=None)
def selection(tid):
    return json.loads((REFS / tid / "selection.json").read_text())


@lru_cache(maxsize=None)
def manifest(tid):
    return json.loads((LADDERS / tid / "manifest.json").read_text())


@lru_cache(maxsize=None)
def _record(path_str: str):
    from pathlib import Path
    d = json.loads(Path(path_str).read_text())
    feats = {k: np.array([np.nan if v is None else v for v in vals], float) for k, vals in d["feats"].items()}
    return d["words"], add_derived(feats), d["meta"]


@lru_cache(maxsize=None)
def record(kind: str, tid: str, rid: str, norm: str = "level"):
    """(words, feats, meta) for a reference or ladder clip, under a normalization."""
    base = (REFS if kind == "ref" else LADDERS) / tid / rid
    words, feats, meta = _record(str(base.with_suffix(".json")))
    if norm != "level":
        c = features.contours(read_wav(base.with_suffix(".wav")))
        feats = features.word_features(words, c, norm)
    return words, feats, meta


def refs_for(tid: str, exclude: str, k: int | None) -> list[str]:
    ids = [g for g in selection(tid)["good"] if g != exclude]
    return ids if k is None else ids[:k]


@lru_cache(maxsize=None)
def envelope_for(tid: str, exclude: str, k, norm: str):
    return build([record("ref", tid, r, norm)[1] for r in refs_for(tid, exclude, k)])


def duration_min(words) -> float:
    return (words[-1]["end"] - words[0]["start"]) / 60


# -- calibration ----------------------------------------------------------------

def fit_margin_scale(cfg: Config, tid: str = "T1") -> tuple[dict, dict]:
    margin = {f: 0.0 for f in ENV_FEATURES}
    if cfg.margin:
        diffs = {f: [] for f in ENV_FEATURES}
        for g in selection(tid)["good"]:
            _, fr, _ = record("ref", tid, g, cfg.norm)
            _, fn, _ = record("clip", tid, f"{tid}_null_{g}", cfg.norm)
            for f in ENV_FEATURES:
                d = np.abs(fwd(f, fr[f]) - fwd(f, fn[f]))
                diffs[f] += list(d[np.isfinite(d)])
        margin = {f: float(np.percentile(v, 95)) if v else 0.0 for f, v in diffs.items()}
    env = build([record("ref", tid, g, cfg.norm)[1] for g in selection(tid)["good"]])
    return margin, widths(env)


def predict(cfg: Config, p: Params, kind: str, tid: str, rid: str, exclude: str) -> tuple[list, list]:
    words, feats, _ = record(kind, tid, rid, cfg.norm)
    if cfg.method == "B0":
        return generic_norms(feats, words), words
    env = envelope_for(tid, exclude, cfg.k, cfg.norm)
    return detect(feats, words, env, p), words


def clip_items(tid: str, kinds=("ladder",)):
    return [c for c in manifest(tid) if c["kind"] in kinds]


def run(cfg: Config, p: Params, tid: str) -> dict:
    """Everything measured for one config on one text."""
    lad, by_type, by_level, sev_pairs = [], {t: [] for t in FLAW_TYPES}, {lv: [] for lv in range(1, 6)}, []
    outside, outside_edit = [], []
    pred_n, pred_hit = {t: 0 for t in FLAW_TYPES}, {t: 0 for t in FLAW_TYPES}
    pred_n_edit = {t: 0 for t in FLAW_TYPES}  # excluding flags the untouched source also gets
    null_cache = {}
    for c in clip_items(tid):
        preds, words = predict(cfg, p, "clip", tid, c["id"], c["source"])
        if c["source"] not in null_cache:  # what the detector says about the untouched source
            null_cache[c["source"]] = predict(cfg, p, "clip", tid, f"{tid}_null_{c['source']}", c["source"])[0]
        for q in preds:
            hit = any(q["type"] == l["type"] and min(q["end"], l["end"]) > max(q["start"], l["start"])
                      for l in c["labels"])
            source_style = any(q["type"] == n["type"] and q["w0"] <= n["w1"] + 1 and n["w0"] <= q["w1"] + 1
                               for n in null_cache[c["source"]])
            pred_n[q["type"]] += 1
            pred_hit[q["type"]] += hit
            pred_n_edit[q["type"]] += hit or not source_style
        row = score_clip(c["labels"], preds)
        lad.append(row)
        lab = c["labels"][0]
        by_type[lab["type"]].append(row)
        by_level[lab["severity"]].append(row)
        same = [q for q in preds if q["type"] == lab["type"]
                and min(q["end"], lab["end"]) > max(q["start"], lab["start"])]
        sev_pairs.append((lab["severity"], max([q.get("severity", 0) for q in same], default=0.0)))
        out_q = [q for q in preds if not any(
            min(q["end"], l["end"]) > max(q["start"], l["start"]) for l in c["labels"])]
        outside.append((out_q, duration_min(words)))
        # flags that the null-edit copy of the same source also gets are the source's own style,
        # already counted once in the good-pair false alarms; don't count them again per clip
        outside_edit.append(([q for q in out_q if not any(
            q["type"] == n["type"] and q["w0"] <= n["w1"] + 1 and n["w0"] <= q["w1"] + 1  # same words
            for n in null_cache[c["source"]])], duration_min(words)))
    comp = [score_clip(c["labels"], predict(cfg, p, "clip", tid, c["id"], c["source"])[0])
            for c in clip_items(tid, ("compound",))]
    # good-vs-good, leave one out: every good rendition judged against the others
    loo_preds, loo_min = [], []
    for g in selection(tid)["good"]:
        preds, words = predict(cfg, p, "ref", tid, g, g)
        loo_preds.append(preds)
        loo_min.append(duration_min(words))
    null_preds, null_min = [], []
    for c in clip_items(tid, ("null",)):
        preds, words = predict(cfg, p, "clip", tid, c["id"], c["source"])
        null_preds.append(preds)
        null_min.append(duration_min(words))
    return {
        "config": cfg.name,
        "ladders": aggregate(lad),
        "by_type": {t: aggregate(r)["matching_score"] for t, r in by_type.items()},
        "by_level": {lv: aggregate(r)["matching_score"] for lv, r in by_level.items()},
        "compound": aggregate(comp) if comp else None,
        "fa_per_min_good_pairs": false_alarms_per_min(loo_preds, loo_min),
        "fa_per_min_null_edit": false_alarms_per_min(null_preds, null_min),
        "fa_per_min_ladder_outside_labels": false_alarms_per_min([o[0] for o in outside], [o[1] for o in outside]),
        "fa_per_min_ladder_edit_attributable": false_alarms_per_min([o[0] for o in outside_edit],
                                                                    [o[1] for o in outside_edit]),
        "per_type": {t: {"recall_matching": aggregate(by_type[t])["matching_score"],
                         "recall_time": aggregate(by_type[t])["time_recall"],
                         "precision_time": (pred_hit[t] / pred_n[t]) if pred_n[t] else float("nan"),
                         "precision_edit": (pred_hit[t] / pred_n_edit[t]) if pred_n_edit[t] else float("nan"),
                         "predictions": pred_n[t]} for t in FLAW_TYPES},
        "severity_spearman": spearman(*zip(*sev_pairs)) if sev_pairs else float("nan"),
    }


def objective(r: dict) -> float:
    """Calibration target on T1: matched flaws against everything that went wrong."""
    lad = r["ladders"]
    return lad["matching_score"] - 0.1 * r["fa_per_min_good_pairs"] - 0.1 * r["fa_per_min_ladder_outside_labels"]


def calibrate(cfg: Config, tid: str = "T1", full: bool = True) -> Params:
    margin, scale = fit_margin_scale(cfg, tid)
    p = Params(margin=margin, scale=scale, fitted_on=f"{tid} ({cfg.name})",
               relative_channels=cfg.relative, stress_floor=cfg.stress_floor)
    if cfg.method == "B0":
        return p
    # one threshold per flaw type, by coordinate ascent: maximize T1 Matching Score
    # subject to at most FA_BUDGET false alarms/min on good-vs-good pairs (all types active)
    OFF = 1e9
    p.tau = {t: OFF for t in FLAW_TYPES}
    best_ms = 0.0
    for _ in range(2):
        for typ in FLAW_TYPES:
            keep = p.tau[typ]
            choice = (best_ms, keep)
            for tau in reversed(TAU_GRID):  # ties keep the stricter threshold
                p.tau[typ] = tau
                r = run(cfg, p, tid)
                ms = r["ladders"]["matching_score"]
                if r["fa_per_min_good_pairs"] <= FA_BUDGET and ms > choice[0] + 1e-9:
                    choice = (ms, tau)
            best_ms, p.tau[typ] = choice
    p.tau = {t: (v if v < OFF else max(TAU_GRID)) for t, v in p.tau.items()}
    if full:
        _fit_severity_and_lambda(cfg, p, tid)
    return p


def _fit_severity_and_lambda(cfg: Config, p: Params, tid: str) -> None:
    """Severity map d -> severity, fitted on the calibration text only.

    With listening-test data (spec section 7, choice 6) the target is the mean perceived
    severity (0-4) of each (flaw type, injected level); without it, the injected level (1-5).
    """
    from .human import perceived_by_level, summarize_listening
    perceived = perceived_by_level() if tid == "T1" else {}
    xs, ys, loads = [], [], {d: [] for d in DIMENSIONS}
    for c in clip_items(tid):
        lab = c["labels"][0]
        preds, words = predict(cfg, p, "clip", tid, c["id"], c["source"])
        same = [q for q in preds if q["type"] == lab["type"]
                and min(q["end"], lab["end"]) > max(q["start"], lab["start"])]
        target = perceived.get((lab["type"], lab["severity"])) if perceived else lab["severity"]
        if same and target is not None:
            xs.append(max(q["d_mean"] for q in same))
            ys.append(target)
        if lab["severity"] == 3:
            T = max(words[-1]["end"] - words[0]["start"], 1e-3)
            loads[DIMENSION[lab["type"]]].append(
                sum(q["d_mean"] * (q["end"] - q["start"]) / T for q in same))
    lo, hi = (0, 4) if perceived else (1, 5)
    if len(xs) >= 3:
        iso = IsotonicRegression(y_min=lo, y_max=hi, out_of_bounds="clip").fit(xs, ys)
        p.sev_x = [float(v) for v in iso.X_thresholds_]
        p.sev_y = [float(v) for v in iso.y_thresholds_]
    if perceived:
        n = len(summarize_listening().get("complete_listeners", []))
        p.sev_scale = f"perceived 0-4 (listening test on T1, {n} complete listeners)"
    # lambda: a median severity-3 flaw halves its dimension's score. One value pooled over all
    # dimensions (d is already normalized per feature): per-dimension fits from a handful of
    # tiny detections exploded (pacing 68, emphasis 86-172) while undetected dimensions kept an
    # arbitrary default of 20, so one 1 s deviation cost 7 points in one dimension and 3 in another.
    pooled = [x for v in loads.values() for x in v if x > 0]
    if pooled:
        lam = float(np.log(2) / np.median(pooled))
        p.lam = {d: lam for d in DIMENSIONS}


def score_readers(cfg: Config, p: Params, tid: str) -> dict:
    """Cadence overall score for every reader not used as a reference (natural spectrum)."""
    good = set(selection(tid)["good"])
    out = {}
    for rid in selection(tid)["ranking"]:
        if rid in good:
            continue
        preds, words = predict(cfg, p, "ref", tid, rid, "")
        out[rid] = float(np.mean(list(scores(preds, words, p).values())))
    return out


def sweep(cfg: Config, p: Params, tid: str, taus=None) -> list[dict]:
    """Matching Score vs false alarms on good pairs, scaling every calibrated threshold."""
    out = []
    for tau in taus or [0.25, 0.4, 0.6, 0.8, 1.0, 1.25, 1.6, 2.0, 3.0]:
        q = Params(**{**p.__dict__, "tau": {t: v * tau for t, v in p.tau.items()}})
        r = run(cfg, q, tid)
        out.append({"tau": tau, "matching_score": r["ladders"]["matching_score"],
                    "fa_per_min": r["fa_per_min_good_pairs"]})
    return out


def severity_vs_listeners(cfg: Config, p: Params, tid: str = "T1") -> dict:
    """Spec metric "system severity vs listener rating", on the listening-test clips (T1).

    The severity map is fitted on these same clips, but Spearman is unchanged by any
    monotone map, so this measures whether d orders the clips as listeners do.
    """
    from .human import listening_trials, perceived_by_level
    perceived = perceived_by_level()
    if not perceived:
        return {"status": "pending: no listening-test responses on the current ladders"}
    man = {c["id"]: c for c in manifest(tid)}
    sys_sev, heard = [], []
    for t in listening_trials():
        if t["level"] == 0 or (t["type"], t["level"]) not in perceived:
            continue
        c = man[t["clip"]]
        lab = c["labels"][0]
        preds, _ = predict(cfg, p, "clip", tid, c["id"], c["source"])
        same = [q["d_mean"] for q in preds if q["type"] == lab["type"]
                and min(q["end"], lab["end"]) > max(q["start"], lab["start"])]
        sys_sev.append(max(same, default=0.0))
        heard.append(perceived[(t["type"], t["level"])])
    return {"status": "ok", "n_clips": len(heard), "spearman_system_vs_perceived": spearman(sys_sev, heard)}
