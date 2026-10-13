"""Flaw injector (spec section 8, synthetic ladders).

Every clip, including the clean control, goes through the same PSOLA
resynthesis, so clean and flawed audio share processing artifacts (null-edit
control). Edits run in three stages: PSOLA (pitch and duration), gain, then
silence cuts and inserts; labels are mapped through each stage's time warp.
"""
from __future__ import annotations

import numpy as np
import parselmouth
from parselmouth.praat import call

from .audio import SR
from .features import pitch_limits

SEVERITY = {
    "pace_rushed": [0.9, 0.8, 0.7, 0.62, 0.55],
    "pace_dragging": [1.1, 1.25, 1.4, 1.6, 1.8],
    "missing_pause": [0.2, 0.4, 0.6, 0.8, 1.0],      # fraction of silence removed
    "misplaced_pause": [0.3, 0.6, 1.0, 1.5, 2.0],    # seconds inserted mid-phrase
    "monotone": [0.8, 0.6, 0.4, 0.2, 0.1],           # fraction of pitch range kept
    "missed_emphasis": [0.8, 0.6, 0.4, 0.2, 0.0],    # fraction of the peak kept
    "volume_fade": [-3, -6, -10, -14, -18],          # dB
}
EPS = 0.001


def _taper(t, a, b, ramp=0.03):
    """1 inside [a, b], ramping to 0 over `ramp` s outside it."""
    return np.clip(np.minimum((t - a) / ramp + 1, (b - t) / ramp + 1), 0, 1)


class Clip:
    def __init__(self, x: np.ndarray, words: list[dict]):
        self.x = x
        self.words = words
        self.pitch_fns = []   # f(t, hz) -> hz
        self.dur_spans = []   # (a, b, factor)
        self.gains = []       # f(t) -> dB
        self.edits = []       # ("cut", a, b) or ("insert", t0, dur)
        self.labels = []

    # -- time maps --------------------------------------------------------
    def _m1(self, t):
        out = t
        for a, b, r in self.dur_spans:
            out = out + np.where(t <= a, 0, np.where(t >= b, (r - 1) * (b - a), (r - 1) * (t - a)))
        return out

    def _m2(self, t):
        """Cut/insert warp; `t` is already in PSOLA time, so edit positions are mapped too."""
        shift = 0.0
        for kind, a, b in sorted(self.edits, key=lambda e: e[1]):
            a = float(self._m1(np.asarray(a)))
            if kind == "cut":
                b = float(self._m1(np.asarray(b)))
            if kind == "cut" and t >= b:
                shift -= b - a
            elif kind == "cut" and t > a:
                shift -= t - a
            elif kind == "insert" and t >= a:
                shift += b
        return t + shift

    def tmap(self, t):
        return float(self._m2(float(self._m1(np.asarray(t)))))

    # -- render -----------------------------------------------------------
    def render(self) -> np.ndarray:
        snd = parselmouth.Sound(self.x.astype(np.float64), SR)
        lo, hi = pitch_limits(snd)
        manip = call(snd, "To Manipulation", 0.01, lo, hi)
        if self.pitch_fns:
            pt = call(manip, "Extract pitch tier")
            n = call(pt, "Get number of points")
            ts = np.array([call(pt, "Get time from index", i) for i in range(1, n + 1)])
            vs = np.array([call(pt, "Get value at index", i) for i in range(1, n + 1)])
            for fn in self.pitch_fns:
                vs = fn(ts, vs)
            new = call("Create PitchTier", "p", snd.xmin, snd.xmax)
            for t, v in zip(ts, vs):
                call(new, "Add point", float(t), float(v))
            call([new, manip], "Replace pitch tier")
        if self.dur_spans:
            dt = call("Create DurationTier", "d", snd.xmin, snd.xmax)
            for a, b, r in self.dur_spans:
                for t, v in ((a - EPS, 1.0), (a, r), (b, r), (b + EPS, 1.0)):
                    call(dt, "Add point", t, v)
            call([dt, manip], "Replace duration tier")
        y = call(manip, "Get resynthesis (overlap-add)").values[0].astype(np.float32)
        if self.gains:
            t = np.arange(len(y)) / SR
            db = sum(g(t) for g in self.gains)
            y = y * (10 ** (db / 20)).astype(np.float32)
        tone = room_tone(self.x)
        for kind, a, b in sorted(self.edits, key=lambda e: -e[1]):  # right to left keeps times valid
            a1 = float(self._m1(np.asarray(a)))
            i = int(a1 * SR)
            if kind == "cut":
                j = int(float(self._m1(np.asarray(b))) * SR)
                y = _crossfade_join(y[:i], y[j:])
            else:
                fill = np.resize(tone, int(b * SR))
                y = _crossfade_join(_crossfade_join(y[:i], fill), y[i:])
        return y


def _crossfade_join(a: np.ndarray, b: np.ndarray, n: int = 160) -> np.ndarray:
    n = min(n, len(a), len(b))
    if n == 0:
        return np.concatenate([a, b])
    w = np.linspace(0, 1, n, dtype=np.float32)
    return np.concatenate([a[:-n], a[-n:] * (1 - w) + b[:n] * w, b[n:]])


def room_tone(x: np.ndarray, win: float = 0.2) -> np.ndarray:
    n = int(win * SR)
    frames = np.lib.stride_tricks.sliding_window_view(x[SR // 10: -SR // 10], n)[::160]
    k = int(np.argmin((frames ** 2).mean(1)))
    return frames[k].copy()


# -- flaw edits ------------------------------------------------------------

def add_flaw(clip: Clip, typ: str, level: int, w0: int, w1: int, stress_ref: dict | None = None) -> None:
    """Queue one flaw at severity `level` (1-5) on words w0..w1."""
    W = clip.words
    a, b = W[w0]["start"], W[w1]["end"]
    lab = {"type": typ, "severity": level, "w0": w0, "w1": w1}
    if typ in ("pace_rushed", "pace_dragging"):
        r = SEVERITY[typ][level - 1]
        clip.dur_spans.append((a, b, r))
        lab.update(type="pace", subtype=typ.split("_")[1], param=r, _span=(a, b))
    elif typ == "monotone":
        keep = SEVERITY[typ][level - 1]

        def fn(t, hz, a=a, b=b, keep=keep):
            m = (t >= a) & (t <= b)
            if m.sum() < 3:
                return hz
            med = np.median(hz[m])
            alpha = 1 - (1 - keep) * _taper(t, a, b)
            return med * (hz / med) ** alpha
        clip.pitch_fns.append(fn)
        lab.update(param=keep, _span=(a, b))
    elif typ == "missed_emphasis":
        keep = SEVERITY[typ][level - 1]
        nb = [j for j in (w0 - 2, w0 - 1, w0 + 1, w0 + 2) if 0 <= j < len(W)]

        def fn(t, hz, a=a, b=b, keep=keep):  # peak measured over the neighbours' median level
            ref = [np.median(hz[(t >= W[j]["start"]) & (t <= W[j]["end"])])
                   for j in nb if ((t >= W[j]["start"]) & (t <= W[j]["end"])).sum() >= 2]
            if not ref:
                return hz
            r = float(np.mean(ref))
            m = _taper(t, a, b, 0.02) * (hz > r)
            return np.where(m > 0, r * (np.maximum(hz, 1) / r) ** (keep + (1 - keep) * (1 - m)), hz)
        clip.pitch_fns.append(fn)
        excess = stress_ref.get("loud_excess", 0.0) if stress_ref else 0.0
        if excess > 0:
            clip.gains.append(lambda t, a=a, b=b, g=-(1 - keep) * excess: g * _taper(t, a, b, 0.02))
        lab.update(param=keep, _span=(a, b))
    elif typ == "volume_fade":
        g = SEVERITY[typ][level - 1]
        ramp = max(0.05, 0.25 * (b - a))
        clip.gains.append(lambda t, a=a, b=b, g=g, ramp=ramp:
                          g * np.clip(np.minimum((t - a) / ramp, (b + 0.08 - t) / 0.08), 0, 1))
        lab.update(param=g, _span=(a, b))
    elif typ == "missing_pause":
        p = SEVERITY[typ][level - 1]
        s, e = W[w0]["end"], W[w0 + 1]["start"]
        keep = max(0.01, (1 - p) * (e - s))
        clip.edits.append(("cut", s + keep / 2, e - keep / 2))
        lab.update(w1=w0 + 1, param=p, _span=(W[w0]["start"], W[w0 + 1]["end"]))
    elif typ == "misplaced_pause":
        dur = SEVERITY[typ][level - 1]
        t0 = (W[w0]["end"] + W[w0 + 1]["start"]) / 2
        clip.edits.append(("insert", t0, dur))
        lab.update(w1=w0, param=dur, _span=None, _insert=(t0, dur))
    else:
        raise ValueError(typ)
    clip.labels.append(lab)


def finalize_labels(clip: Clip) -> list[dict]:
    out = []
    for lab in clip.labels:
        lab = dict(lab)
        if lab.get("_insert"):
            t0, dur = lab.pop("_insert")
            s = clip.tmap(t0 - 1e-6)
            lab["start"], lab["end"] = s, s + dur
        else:
            a, b = lab["_span"]
            lab["start"], lab["end"] = clip.tmap(a), clip.tmap(b)
        lab.pop("_span", None)
        lab["start"], lab["end"] = round(lab["start"], 4), round(lab["end"], 4)
        out.append(lab)
    return out


def null_edit(x: np.ndarray, words: list[dict]) -> np.ndarray:
    return Clip(x, words).render()


# -- span selection --------------------------------------------------------

def choose_spans(words, feats, stress, rng, n=2, others_pause=None, rule: int = 1, stress_rule: int = 1) -> dict[str, list[tuple[int, int]]]:
    """Random word spans per flaw type from a fixed-seed generator.

    rule 1 (T1-T3, frozen): as first released. rule 2 (newer texts): a misplaced pause
    is inserted only between two words each >= 0.15 s long, because gapless boundaries
    next to very short words are where the source alignment is least reliable.

    `others_pause` (K, W) holds the other good renditions' pauses. A missing pause is
    injected only where every good reader pauses, and a misplaced pause only where
    none does; otherwise the "flaw" would be a stylistic choice by our own definition.
    """
    W = len(words)
    pause = feats["pause"]
    if others_pause is None:
        others_pause = pause[None]
    op_min, op_max = np.min(others_pause, 0), np.max(others_pause, 0)
    inner = range(2, W - 3)

    def phrase_spans(lo=4, hi=7):
        cands = []
        for i in inner:
            for L in range(lo, hi + 1):
                j = i + L - 1
                if j < W - 2 and not (pause[i:j] >= 0.25).any():
                    cands.append((i, j))
        return cands

    def pick(cands, k, min_gap=3):
        cands = list(cands)
        rng.shuffle(cands)
        out = []
        for c in cands:
            if all(c[0] > o[1] + min_gap or c[1] < o[0] - min_gap for o in out):
                out.append(c)
            if len(out) == k:
                break
        return out

    ph = phrase_spans()
    own = (np.nan_to_num(feats["prom_pitch"]) > 1.0) | (np.nan_to_num(feats["prom_loud"]) > 1.5)
    stress_c = [(i, i) for i in inner if stress[i] and own[i]]
    if stress_rule < 2 and len(pick(list(stress_c), n)) < n:  # v1/v2: allow any consensus stress point
        stress_c += [(i, i) for i in inner if stress[i] and not own[i]]
    return {
        "pace_rushed": pick(ph, 1),
        "pace_dragging": pick(ph, 1),
        "monotone": pick(ph, n),
        "volume_fade": pick(ph, n),
        "missing_pause": pick([(i, i + 1) for i in inner if pause[i] >= 0.3 and op_min[i] >= 0.15], n),
        "misplaced_pause": pick([(i, i) for i in inner if pause[i] == 0 and op_max[i] == 0 and pause[i - 1] == 0
                                 and (rule < 2 or min(words[i]["end"] - words[i]["start"],
                                                      words[i + 1]["end"] - words[i + 1]["start"]) >= 0.15)
                                 and pause[i + 1] == 0], n),
        "missed_emphasis": pick(stress_c, n),  # drawn last: earlier spans do not depend on it
    }


def loud_excess(x: np.ndarray, words: list[dict], i: int) -> float:
    """Peak loudness of word i over the mean loudness of its two neighbours each side (dB)."""
    from .features import contours
    c = contours(x)
    t, v = c["int_t"], c["int"]

    def seg(j):
        m = (t >= words[j]["start"]) & (t <= words[j]["end"])
        return v[m] if m.any() else np.array([np.nan])
    nb = [np.nanmean(seg(j)) for j in (i - 2, i - 1, i + 1, i + 2) if 0 <= j < len(words)]
    return float(max(0.0, np.nanmax(seg(i)) - np.nanmean(nb)))
