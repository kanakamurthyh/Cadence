"""Baselines (spec section 8).

B0: generic norms, as commercial coaching apps apply them: pace outside
    100-165 wpm (PowerPoint Speaker Coach's target), long pauses, narrow pitch range.
B1: single reference = the envelope with K = 1 (see envelope.py), not defined here.
"""
from __future__ import annotations

import numpy as np

WPM_LO, WPM_HI = 100.0, 165.0
LONG_PAUSE_S = 1.0
NARROW_RANGE_ST = 2.0
WINDOW = 8  # words


def generic_norms(feats: dict, words: list[dict]) -> list[dict]:
    W = len(words)
    flags = {"pace": np.zeros(W, bool), "misplaced_pause": np.zeros(W, bool), "monotone": np.zeros(W, bool)}
    for i in range(W):
        a, b = max(0, i - WINDOW // 2), min(W - 1, i + WINDOW // 2)
        span = words[b]["end"] - words[a]["start"]
        wpm = (b - a + 1) / span * 60 if span > 0 else 0
        flags["pace"][i] = wpm < WPM_LO or wpm > WPM_HI
    flags["misplaced_pause"] = feats["pause"] > LONG_PAUSE_S
    flags["monotone"] = np.nan_to_num(feats["pitch_range"], nan=99) < NARROW_RANGE_ST
    regions = []
    for typ, f in flags.items():
        i = 0
        while i < W:
            if f[i]:
                j = i
                while j + 1 < W and f[j + 1]:
                    j += 1
                if typ == "misplaced_pause":
                    s, e = words[i]["end"], words[min(i + 1, W - 1)]["start"]
                else:
                    s, e = words[i]["start"], words[j]["end"]
                regions.append({"type": typ, "w0": i, "w1": j, "start": s, "end": e,
                                "d_mean": 1.0, "severity": 3.0})
                i = j + 1
            else:
                i += 1
    return sorted(regions, key=lambda r: r["start"])
