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

import warnings
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
    # v2 (2026-10-14): self-relative channels, appended so v1 channel indices are unchanged.
    # Good readers differ in overall tempo by up to 1.8x and in overall pitch range, which
    # made the absolute envelopes too wide for local pace/monotone flaws (diagnosed on T1).
    # Relative to the reader's own median, the envelope is 2.7x narrower for rate. The
    # absolute channels stay, so a speaker who rushes the whole speech is still caught.
    ("rate_rel", +1, "pace"),
    ("rate_rel", -1, "pace"),
    ("pitch_range_rel", -1, "monotone"),
]
# v3 (2026-10-14): phrase-level channels, appended to keep v1/v2 channel indices unchanged.
# Phrase rate normalises each word's rate by the reader's median phrase rate; pitch spread
# normalises the phrase's p90–p10 pitch spread by the median over phrases.
CHANNELS += [("rate_phr", +1, "pace"), ("rate_phr", -1, "pace"), ("pitch_spread_phr", -1, "monotone")]
REL_FEATURES = {"rate_rel", "pitch_range_rel"}
PHRASE_FEATURES = {"rate_phr", "pitch_spread_phr"}
# v2: a reader "peaks" on a word only if the peak is perceptible. v1 counted any positive
# prominence, so 0.1-0.3 dB bumps made consensus "stress points" nobody hears, and missed
# emphasis became the most common false alarm. ~1.5 st is the usual threshold for a pitch
# movement to be heard as an accent ('t Hart, Collier & Cohen 1990); ~1 dB is the loudness JND.
STRESS_MIN = {"prom_pitch": 1.5, "prom_loud": 1.0}
FLAW_TYPES = ["pace", "missing_pause", "misplaced_pause", "monotone", "missed_emphasis", "volume_fade"]
ENV_FEATURES = sorted({c[0] for c in CHANNELS})
STRESS_FRACTION = 0.75

# Rate, pause and pitch range are compared as ratios (log scale): a 2x change
# matters about equally wherever it happens. Explanations stay in raw units.
TRANSFORM = {
    "rate": (lambda v: np.log2(np.maximum(v, 0.1)), lambda u: 2.0 ** u),
    "pitch_range": (lambda v: np.log2(np.maximum(v, 0) + 1.0), lambda u: 2.0 ** u - 1.0),
    "pause": (lambda v: np.log2(np.maximum(v, 0) + 0.1), lambda u: np.maximum(2.0 ** u - 0.1, 0)),
    "rate_rel": (lambda v: np.log2(np.maximum(v, 0.05)), lambda u: 2.0 ** u),
    "pitch_range_rel": (lambda v: np.log2(np.maximum(v, 0.05)), lambda u: 2.0 ** u),
}
TRANSFORM.update({"rate_phr": TRANSFORM["rate_rel"], "pitch_spread_phr": TRANSFORM["pitch_range_rel"]})


def add_derived(feats: dict) -> dict:
    """Self-relative features: each word's rate / pitch range over the reader's own median."""
    if "rate_rel" in feats and "pitch_range_rel" in feats:
        return feats
    out = dict(feats)
    with np.errstate(all="ignore"):
        r = np.asarray(feats["rate"], float)
        out["rate_rel"] = r / np.nanmedian(r)
        pr = np.asarray(feats["pitch_range"], float)
        out["pitch_range_rel"] = (pr + 1.0) / (np.nanmedian(pr) + 1.0)
    return out


def phrase_ids(pauses: np.ndarray) -> np.ndarray:
    """Per-word phrase index from a (K, W) pause matrix.

    Boundary after word i when >= STRESS_FRACTION of readers have pause[i] >= 0.05.
    The last word never starts a new phrase.
    """
    br = (np.nan_to_num(pauses) >= 0.05).mean(0) >= STRESS_FRACTION
    br[-1] = False
    return np.concatenate([[0], np.cumsum(br[:-1])]).astype(int)


def with_phrases(feats: dict, pid: np.ndarray) -> dict:
    """Add phrase-level rate and pitch-spread features, broadcast to each word.

    rate_phr: phrase articulation rate / reader's median phrase rate.
    pitch_spread_phr: (p90 - p10 of pitch in phrase + 1) / (median over phrases + 1).
    NaN where syl/dur are absent or pitch is all-NaN within a phrase.
    """
    out = dict(feats)
    W = len(pid)
    rate, spread = np.full(W, np.nan), np.full(W, np.nan)
    if "syl" in feats and "dur" in feats:
        for p in np.unique(pid):
            m = pid == p
            rate[m] = feats["syl"][m].sum() / feats["dur"][m].sum()
            v = feats["pitch"][m]
            v = v[np.isfinite(v)]
            if len(v) >= 2:
                spread[m] = np.percentile(v, 90) - np.percentile(v, 10)
    with np.errstate(all="ignore"):
        out["rate_phr"] = rate / np.nanmedian(rate) if np.isfinite(rate).any() else rate
        out["pitch_spread_phr"] = ((spread + 1) / (np.nanmedian(spread) + 1)
                                   if np.isfinite(spread).any() else spread)
    return out


def fwd(f, v):
    return TRANSFORM[f][0](v) if f in TRANSFORM else v


def inv(f, u):
    return TRANSFORM[f][1](u) if f in TRANSFORM else u


@dataclass
class Envelope:
    lo: dict[str, np.ndarray]          # per-word min over references (comparison domain, no margin)
    hi: dict[str, np.ndarray]          # per-word max over references (comparison domain)
    stress_pitch: np.ndarray           # bool per word (v1: any positive prominence)
    stress_loud: np.ndarray
    k: int
    ref_values: dict[str, np.ndarray] = field(repr=False, default_factory=dict)  # raw units, (K, W)
    stress_pitch_p: np.ndarray | None = None  # v2: perceptible peaks only (STRESS_MIN)
    stress_loud_p: np.ndarray | None = None
    phrase_id: np.ndarray | None = None  # v3: per-word phrase index (from phrase_ids)

    def stress(self, perceptual: bool) -> tuple[np.ndarray, np.ndarray]:
        return (self.stress_pitch_p, self.stress_loud_p) if perceptual else (self.stress_pitch, self.stress_loud)

    def band(self, f, margin=0.0):
        """Envelope in raw units, margin included, for display."""
        return inv(f, self.lo[f] - margin), inv(f, self.hi[f] + margin)


def build(ref_feats: list[dict[str, np.ndarray]]) -> Envelope:
    k = len(ref_feats)
    ref_feats = [add_derived(r) for r in ref_feats]
    pid = phrase_ids(np.stack([r["pause"] for r in ref_feats]))
    ref_feats = [with_phrases(r, pid) for r in ref_feats]
    vals = {f: np.stack([r[f] for r in ref_feats]) for f in ENV_FEATURES}
    with np.errstate(all="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        lo = {f: np.nanmin(fwd(f, v), 0) for f, v in vals.items()}
        hi = {f: np.nanmax(fwd(f, v), 0) for f, v in vals.items()}

    def stress(f, floor=0.0):
        peaks = np.nan_to_num(vals[f], nan=-1.0) > floor
        return peaks.mean(0) >= STRESS_FRACTION

    return Envelope(lo, hi, stress("prom_pitch"), stress("prom_loud"), k, vals,
                    stress("prom_pitch", STRESS_MIN["prom_pitch"]), stress("prom_loud", STRESS_MIN["prom_loud"]),
                    phrase_id=pid)


def widths(env: Envelope) -> dict[str, float]:
    """Median envelope width per feature (s_f), used once at calibration."""
    out = {}
    for f in ENV_FEATURES:
        w = env.hi[f] - env.lo[f]
        w = w[np.isfinite(w) & (w > 0)]
        out[f] = float(np.median(w)) if len(w) else 1.0
    return out


def deviations(x: dict[str, np.ndarray], env: Envelope, margin: dict, scale: dict,
               relative: bool = False, stress_floor: bool = False, phrase: bool = False) -> dict:
    """Per-channel, per-word d values (0 inside the envelope).

    relative=False and stress_floor=False reproduce the v1 detector exactly.
    phrase=True activates phrase-level channels (rate_phr, pitch_spread_phr) and zeros
    word-level REL_FEATURES channels (phrase replaces them). When phrase=False, phrase
    channels give zeros and v1/v2 output is byte-identical to before.
    """
    x = add_derived(x)
    if env.phrase_id is not None:
        x = with_phrases(x, env.phrase_id)
    sp, sl = env.stress(stress_floor)
    out = {}
    W = len(x["rate"])
    for f, side, typ in CHANNELS:
        if f in REL_FEATURES and (not relative or phrase):
            out[(f, side)] = np.zeros(W)
            continue
        if f in PHRASE_FEATURES and not phrase:
            out[(f, side)] = np.zeros(W)
            continue
        if f in PHRASE_FEATURES and env.phrase_id is None:
            out[(f, side)] = np.zeros(W)
            continue
        L = env.lo[f] - margin.get(f, 0.0)
        U = env.hi[f] + margin.get(f, 0.0)
        xv = fwd(f, x[f])
        gap = (L - xv) if side < 0 else (xv - U)
        d = np.nan_to_num(np.maximum(gap, 0) / scale.get(f, 1.0), nan=0.0)
        if f == "pause" and side < 0:  # a missing pause only where every good reader paused
            d[~(inv(f, L) > 0.05)] = 0.0
        if f == "prom_pitch":
            d[~sp] = 0.0
        if f == "prom_loud":
            d[~sl] = 0.0
        out[(f, side)] = d
    # missed emphasis: average over the modalities the consensus peaks in
    both = sp & sl
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
