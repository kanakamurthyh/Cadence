"""Regions, type, severity, explanation and rubric scores (spec section 7, choices 5-8)."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from .envelope import CHANNELS, ENV_FEATURES, FLAW_TYPES, Envelope, by_type, deviations
from .features import UNITS

DIMENSION = {  # flaw type -> rubric dimension
    "pace": "pacing", "missing_pause": "pausing", "misplaced_pause": "fluency",
    "monotone": "pitch_variety", "missed_emphasis": "emphasis", "volume_fade": "volume",
}
DIMENSIONS = ["pacing", "pausing", "pitch_variety", "emphasis", "volume", "fluency"]
NUMBER_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
                7: "seven", 8: "eight", 9: "nine", 10: "ten"}


@dataclass
class Params:
    """Everything fitted on the calibration text (T1) and then frozen."""
    margin: dict = field(default_factory=lambda: {f: 0.0 for f in ENV_FEATURES})
    scale: dict = field(default_factory=lambda: {f: 1.0 for f in ENV_FEATURES})
    tau_high: float = 1.0
    tau_low: float = 0.5
    tau: dict = field(default_factory=dict)  # per flaw type tau_high (tau_low = tau/2); falls back to tau_high
    lam: dict = field(default_factory=lambda: {d: 20.0 for d in DIMENSIONS})
    sev_x: list = field(default_factory=lambda: [0.0, 1.0, 2.0, 4.0, 8.0])
    sev_y: list = field(default_factory=lambda: [1.0, 2.0, 3.0, 4.0, 5.0])
    sev_scale: str = "injected level 1-5 (provisional until the listening test)"
    fitted_on: str = "defaults"

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(asdict(self), indent=1, sort_keys=True))

    @classmethod
    def load(cls, path: str | Path) -> "Params":
        return cls(**json.loads(Path(path).read_text()))


def channel_span(ch: int, i: int, words: list[dict]) -> tuple[float, float]:
    f, side, _ = CHANNELS[ch]
    if f == "pause" and i + 1 < len(words):
        if side > 0:  # the silence itself
            return words[i]["end"], words[i + 1]["start"]
        return words[i]["start"], words[i + 1]["end"]  # the two words around the boundary
    return words[i]["start"], words[i]["end"]


def hysteresis(d: np.ndarray, hi: float, lo: float, merge_gap: int = 1) -> list[tuple[int, int]]:
    runs, start = [], None
    for i, v in enumerate(d):
        if start is None and v > hi:
            start = i
            while start > 0 and d[start - 1] > lo:  # grow left while above the low threshold
                start -= 1
        elif start is not None and v < lo:
            runs.append((start, i - 1))
            start = None
    if start is not None:
        runs.append((start, len(d) - 1))
    merged = []
    for r in runs:
        if merged and r[0] - merged[-1][1] - 1 <= merge_gap:
            merged[-1] = (merged[-1][0], r[1])
        else:
            merged.append(r)
    return merged


def detect(x: dict, words: list[dict], env: Envelope, p: Params, types=None) -> list[dict]:
    dev = deviations(x, env, p.margin, p.scale)
    typed = by_type(dev)
    regions = []
    for typ in types or FLAW_TYPES:
        d, ch = typed[typ]
        th = p.tau.get(typ, p.tau_high)
        tl = th / 2 if typ in p.tau else p.tau_low
        for a, b in hysteresis(d, th, tl):
            if d[a:b + 1].max() <= th:
                continue
            idx = [i for i in range(a, b + 1) if d[i] > 0] or list(range(a, b + 1))
            spans = [channel_span(ch[i], i, words) for i in idx]
            dom = int(np.bincount(ch[idx], weights=d[idx] + 1e-9).argmax())
            regions.append({
                "type": typ, "w0": idx[0], "w1": idx[-1],
                "start": min(s for s, _ in spans), "end": max(e for _, e in spans),
                "d_mean": float(d[idx].mean()), "d_max": float(d[idx].max()),
                "feature": CHANNELS[dom][0], "side": CHANNELS[dom][1], "channel": dom,
            })
    # overlapping regions of different types: the dominant feature names the flaw
    regions.sort(key=lambda r: -r["d_mean"])
    kept = []
    for r in regions:
        if all(r["end"] <= k["start"] or r["start"] >= k["end"] for k in kept):
            kept.append(r)
    kept.sort(key=lambda r: r["start"])
    for r in kept:
        r["severity"] = float(np.interp(r["d_mean"], p.sev_x, p.sev_y))
    return kept


def _fmt(v: float, f: str) -> str:
    return f"{v:.2f}" if UNITS[f] == "s" else f"{v:.1f}"


def explain(r: dict, x: dict, words: list[dict], env: Envelope) -> str:
    f, side = r["feature"], r["side"]
    idx = list(range(r["w0"], r["w1"] + 1))
    att = float(np.nanmean(x[f][idx]))
    refs = np.nanmean(env.ref_values[f][:, idx], axis=1)
    lo, hi = float(np.nanmin(refs)), float(np.nanmax(refs))
    k = NUMBER_WORDS.get(env.k, str(env.k))
    unit = {"st": "semitones", "dB": "dB", "s": "s", "syll/s": "syllables/s"}[UNITS[f]]
    w0, w1 = words[r["w0"]], words[r["w1"]]
    span = f"Word {r['w0'] + 1}" if r["w0"] == r["w1"] else f"Words {r['w0'] + 1}-{r['w1'] + 1}"
    head = f"{span} ({r['start']:.1f}-{r['end']:.1f} s): "
    pl = "" if env.k == 1 else "s"
    rng = (f"the good rendition{pl} spanned {_fmt(lo, f)}-{_fmt(hi, f)}" if env.k > 1
           else f"the reference had {_fmt(lo, f)}")
    typ = r["type"]
    if typ == "pace":
        tip = (f"Slow down from '{w0['word']}' to '{w1['word']}'." if side > 0
               else f"Pick up the pace from '{w0['word']}' to '{w1['word']}'.")
        what = "speaking rate"
    elif typ == "missing_pause":
        tip = f"Pause after '{w0['word']}'."
        what = f"pause after '{w0['word']}'"
    elif typ == "misplaced_pause":
        tip = f"Carry on through '{w0['word']} {words[min(r['w0'] + 1, len(words) - 1)]['word']}' without stopping."
        what = f"pause after '{w0['word']}'"
    elif typ == "monotone":
        peak = idx[int(np.nanargmax(np.nan_to_num(env.hi["pitch_range"][idx], nan=-1)))]
        tip = f"Lift pitch on '{words[peak]['word']}'."
        what = "pitch range"
    elif typ == "missed_emphasis":
        tip = f"Stress '{w0['word']}'."
        what = "pitch peak over neighbours" if f == "prom_pitch" else "loudness peak over neighbours"
    else:
        tip = f"Keep your volume up through '{w1['word']}'."
        what = "loudness re your median"
    return f"{head}{what} {_fmt(att, f)} {unit}; {rng}{'' if env.k == 1 else ' across ' + k}. {tip}"


def scores(regions: list[dict], words: list[dict], p: Params) -> dict:
    T = max(words[-1]["end"] - words[0]["start"], 1e-3)
    load = {d: 0.0 for d in DIMENSIONS}
    for r in regions:
        load[DIMENSION[r["type"]]] += r["d_mean"] * (r["end"] - r["start"]) / T
    return {d: round(10 * float(np.exp(-p.lam[d] * load[d])), 2) for d in DIMENSIONS}
