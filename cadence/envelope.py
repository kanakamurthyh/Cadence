"""Consensus envelope (spec section 7, choices 3-4).

For word w and feature f with K good renditions:
    L = min_k x_k - m_f,  U = max_k x_k + m_f
    d = max(0, L - x, x - U) / s_f
m_f is the measurement margin (95th percentile of |reference - null-edited
reference|) and s_f the median envelope width of f across words; both are
fitted once on the calibration text and frozen, so with K = 1 the envelope
reduces exactly to the single-reference baseline.

Each flaw type reads one side of one feature ("channel"); missed emphasis is
read only at consensus stress points.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# (feature, side, flaw type): side -1 flags values below L, +1 above U
CHANNELS = [
    ("rate", +1, "pace"),
    ("rate", -1, "pace"),
    ("pause", -1, "missing_pause"),
    ("pause", +1, "misplaced_pause"),
    ("pitch_range", -1, "monotone"),
    ("loud", -1, "volume_fade"),
    ("prom_pitch", -1, "missed_emphasis"),
    ("prom_loud", -1, "missed_emphasis"),
]
FLAW_TYPES = ["pace", "missing_pause", "misplaced_pause", "monotone", "missed_emphasis", "volume_fade"]
ENV_FEATURES = sorted({c[0] for c in CHANNELS})
STRESS_FRACTION = 0.75

# Rate, pause and pitch range are compared as ratios (log scale): a 2x change
# matters about equally wherever it happens. Explanations stay in raw units.
TRANSFORM = {
    "rate": (lambda v: np.log2(np.maximum(v, 0.1)), lambda u: 2.0 ** u),
    "pitch_range": (lambda v: np.log2(np.maximum(v, 0) + 1.0), lambda u: 2.0 ** u - 1.0),
    "pause": (lambda v: np.log2(np.maximum(v, 0) + 0.1), lambda u: np.maximum(2.0 ** u - 0.1, 0)),
}


def fwd(f, v):
    return TRANSFORM[f][0](v) if f in TRANSFORM else v


def inv(f, u):
    return TRANSFORM[f][1](u) if f in TRANSFORM else u


@dataclass
class Envelope:
    lo: dict[str, np.ndarray]          # per-word min over references (comparison domain, no margin)
    hi: dict[str, np.ndarray]          # per-word max over references (comparison domain)
    stress_pitch: np.ndarray           # bool per word
    stress_loud: np.ndarray
    k: int
    ref_values: dict[str, np.ndarray] = field(repr=False, default_factory=dict)  # raw units, (K, W)

    def band(self, f, margin=0.0):
        """Envelope in raw units, margin included, for display."""
        return inv(f, self.lo[f] - margin), inv(f, self.hi[f] + margin)


def build(ref_feats: list[dict[str, np.ndarray]]) -> Envelope:
    k = len(ref_feats)
    vals = {f: np.stack([r[f] for r in ref_feats]) for f in ENV_FEATURES}
    with np.errstate(all="ignore"):
        lo = {f: np.nanmin(fwd(f, v), 0) for f, v in vals.items()}
        hi = {f: np.nanmax(fwd(f, v), 0) for f, v in vals.items()}

    def stress(f):
        peaks = np.nan_to_num(vals[f], nan=-1.0) > 0
        return peaks.mean(0) >= STRESS_FRACTION

    return Envelope(lo, hi, stress("prom_pitch"), stress("prom_loud"), k, vals)


def widths(env: Envelope) -> dict[str, float]:
    """Median envelope width per feature (s_f), used once at calibration."""
    out = {}
    for f in ENV_FEATURES:
        w = env.hi[f] - env.lo[f]
        w = w[np.isfinite(w) & (w > 0)]
        out[f] = float(np.median(w)) if len(w) else 1.0
    return out


def deviations(x: dict[str, np.ndarray], env: Envelope, margin: dict, scale: dict) -> dict:
    """Per-channel, per-word d values (0 inside the envelope)."""
    out = {}
    for f, side, typ in CHANNELS:
        L = env.lo[f] - margin[f]
        U = env.hi[f] + margin[f]
        xv = fwd(f, x[f])
        gap = (L - xv) if side < 0 else (xv - U)
        d = np.nan_to_num(np.maximum(gap, 0) / scale[f], nan=0.0)
        if f == "pause" and side < 0:  # a missing pause only where every good reader paused
            d[~(inv(f, L) > 0.05)] = 0.0
        if f == "prom_pitch":
            d[~env.stress_pitch] = 0.0
        if f == "prom_loud":
            d[~env.stress_loud] = 0.0
        out[(f, side)] = d
    # missed emphasis: average over the modalities the consensus peaks in
    both = env.stress_pitch & env.stress_loud
    pe, le = out[("prom_pitch", -1)], out[("prom_loud", -1)]
    out[("prom_pitch", -1)] = np.where(both, (pe + le) / 2, pe)
    out[("prom_loud", -1)] = np.where(both, 0.0, le)
    return out


def by_type(dev: dict) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Collapse channels to flaw types: (max d per word, index of winning channel)."""
    out = {}
    for typ in FLAW_TYPES:
        chans = [i for i, c in enumerate(CHANNELS) if c[2] == typ]
        m = np.stack([dev[CHANNELS[i][:2]] for i in chans])
        out[typ] = (m.max(0), np.array(chans)[m.argmax(0)])
    return out
