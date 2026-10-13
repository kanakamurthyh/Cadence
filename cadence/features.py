"""Per-word delivery features (spec section 7, choice 2).

Level-only speaker normalization removes what biology and microphones change
and keeps what delivery changes:
  * pitch in semitones relative to the speaker's median F0; pitch *range* kept;
  * loudness in dB relative to the speaker's median; loudness dynamics kept;
  * rate, durations and pauses in absolute units, never z-scored.
`norm="zscore"` reproduces v1's bug (every feature z-scored per recording) and
`norm="off"` uses raw units; both exist only for the ablation.
"""
from __future__ import annotations

import re

import numpy as np
import parselmouth

from .audio import SR

FEATURES = ["rate", "pause", "pitch_range", "loud", "prom_pitch", "prom_loud", "pitch"]
UNITS = {"rate": "syll/s", "pause": "s", "pitch_range": "st", "loud": "dB",
         "rate_rel": "x", "pitch_range_rel": "x",
         "prom_pitch": "st", "prom_loud": "dB", "pitch": "st"}
F0_MIN, F0_MAX = 75.0, 500.0
MIN_PAUSE = 0.05  # gaps shorter than this are stop closures, not pauses


def syllables(word: str) -> int:
    w = word.lower()
    n = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and n > 1 and not w.endswith(("le", "ee", "ye")):
        n -= 1
    return max(1, n)


def pitch_limits(snd: parselmouth.Sound) -> tuple[float, float]:
    """Two-pass speaker-adaptive F0 limits (Hirst 2011): 0.75*q25 and 1.5*q75."""
    f0 = snd.to_pitch_ac(time_step=0.01, pitch_floor=F0_MIN, pitch_ceiling=F0_MAX).selected_array["frequency"]
    f0 = f0[f0 > 0]
    if len(f0) < 20:
        return F0_MIN, F0_MAX
    return max(50.0, 0.75 * np.percentile(f0, 25)), min(700.0, 1.5 * np.percentile(f0, 75))


def contours(x: np.ndarray) -> dict:
    snd = parselmouth.Sound(x.astype(np.float64), SR)
    lo, hi = pitch_limits(snd)
    pitch = snd.to_pitch_ac(time_step=0.01, pitch_floor=lo, pitch_ceiling=hi)
    f0 = pitch.selected_array["frequency"]
    inten = snd.to_intensity(minimum_pitch=F0_MIN, time_step=0.01)
    return {
        "f0_t": pitch.xs(), "f0": f0,
        "int_t": inten.xs(), "int": inten.values[0],
    }


def silence_threshold(c: dict) -> float:
    v = c["int"][np.isfinite(c["int"])]
    lo, hi = np.percentile(v, 5), np.percentile(v, 95)
    return float(lo + 0.3 * (hi - lo))


def refine_edges(words: list[dict], c: dict) -> list[dict]:
    """Snap aligner word edges to silence edges of the intensity contour."""
    t, v = c["int_t"], c["int"]
    thr = silence_threshold(c)
    dt = t[1] - t[0] if len(t) > 1 else 0.01
    loud = v >= thr

    def idx(time):
        return int(np.clip(round((time - t[0]) / dt), 0, len(t) - 1))

    out = [dict(w) for w in words]
    for i, w in enumerate(out):
        nxt = out[i + 1]["start"] if i + 1 < len(out) else t[-1]
        prv = out[i - 1]["end"] if i > 0 else 0.0
        e = idx(w["end"])
        if loud[e]:  # extend into the trailing sound
            lim = idx(min(nxt, w["end"] + 0.3))
            while e < lim and loud[e + 1]:
                e += 1
        else:  # pull back out of silence, at most 60 ms (quiet speech is still speech)
            lim = idx(max(w["start"] + 0.03, w["end"] - 0.06))
            while e > lim and not loud[e]:
                e -= 1
        s = idx(w["start"])
        if loud[s]:
            lim = idx(max(prv, w["start"] - 0.15))
            while s > lim and loud[s - 1]:
                s -= 1
        else:
            lim = idx(min(w["end"] - 0.03, w["start"] + 0.06))
            while s < min(lim, e) and not loud[s]:
                s += 1
        w["start"], w["end"] = float(t[s]), float(max(t[e], t[s] + 0.02))
    for i in range(len(out) - 1):  # no overlaps
        if out[i]["end"] > out[i + 1]["start"]:
            mid = (out[i]["end"] + out[i + 1]["start"]) / 2
            out[i]["end"], out[i + 1]["start"] = mid, mid
    return out


def _frames(tt, vv, a, b):
    m = (tt >= a) & (tt <= b)
    return vv[m]


def word_features(words: list[dict], c: dict, norm: str = "level") -> dict[str, np.ndarray]:
    """Return {feature: array over words}. NaN where a feature is undefined."""
    W = len(words)
    f0t, f0 = c["f0_t"], c["f0"]
    voiced = f0 > 0
    it, iv = c["int_t"], c["int"]
    thr = silence_threshold(c)

    if norm == "off":
        st = np.where(voiced, 12 * np.log2(np.maximum(f0, 1) / 100.0), np.nan)
        db = iv.copy()
    else:  # level-only: subtract the speaker's median level, keep range/dynamics
        med_f0 = np.median(f0[voiced]) if voiced.any() else 100.0
        st = np.where(voiced, 12 * np.log2(np.maximum(f0, 1) / med_f0), np.nan)
        db = iv - np.median(iv[iv >= thr]) if (iv >= thr).any() else iv - np.median(iv)

    starts = np.array([w["start"] for w in words])
    ends = np.array([w["end"] for w in words])
    dur = np.maximum(ends - starts, 0.02)
    syl = np.array([syllables(w["word"]) for w in words], float)

    rate = np.empty(W)  # articulation rate over a 5-word window (pauses excluded)
    for i in range(W):
        a, b = max(0, i - 2), min(W, i + 3)
        rate[i] = syl[a:b].sum() / dur[a:b].sum()

    pause = np.zeros(W)
    pause[:-1] = np.maximum(starts[1:] - ends[:-1], 0)
    pause[pause < MIN_PAUSE] = 0.0

    pitch_med = np.full(W, np.nan)
    pitch_max = np.full(W, np.nan)
    loud = np.full(W, np.nan)
    loud_max = np.full(W, np.nan)
    for i in range(W):
        p = _frames(f0t, st, starts[i], ends[i])
        p = p[np.isfinite(p)]
        if len(p) >= 3:
            pitch_med[i] = np.median(p)
            pitch_max[i] = np.percentile(p, 90)
        d = _frames(it, db, starts[i], ends[i])
        if len(d):
            loud[i] = np.mean(d)
            loud_max[i] = np.max(d)

    pitch_range = np.full(W, np.nan)
    for i in range(W):
        a, b = max(0, i - 1), min(W - 1, i + 1)
        p = _frames(f0t, st, starts[a], ends[b])
        p = p[np.isfinite(p)]
        if len(p) >= 8:
            pitch_range[i] = np.percentile(p, 90) - np.percentile(p, 10)

    def prominence(v):
        out = np.full(W, np.nan)
        for i in range(W):
            nb = [v[j] for j in (i - 2, i - 1, i + 1, i + 2) if 0 <= j < W and np.isfinite(v[j])]
            if np.isfinite(v[i]) and nb:
                out[i] = v[i] - max(nb)
        return out

    loud3 = np.full(W, np.nan)  # duration-weighted loudness over a 3-word window
    for i in range(W):
        a, b = max(0, i - 1), min(W, i + 2)
        ok = np.isfinite(loud[a:b])
        if ok.any():
            loud3[i] = np.average(loud[a:b][ok], weights=dur[a:b][ok])

    feats = {
        "rate": rate, "pause": pause, "pitch_range": pitch_range, "loud": loud3,
        "prom_pitch": prominence(pitch_max), "prom_loud": prominence(loud_max),
        "pitch": pitch_med,
    }
    from .envelope import add_derived
    feats = add_derived(feats)
    if norm == "zscore":  # v1's bug, kept for the ablation only
        for k, v in feats.items():
            sd = np.nanstd(v)
            feats[k] = (v - np.nanmean(v)) / (sd if sd > 0 else 1.0)
    return feats


def extract(x: np.ndarray, words: list[dict], norm: str = "level") -> tuple[list[dict], dict]:
    """Snap edges, then measure. Returns (refined words, features)."""
    c = contours(x)
    words = refine_edges(words, c)
    return words, word_features(words, c, norm)
