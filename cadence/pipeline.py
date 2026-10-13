"""Per-upload pipeline: preprocess -> align -> features -> envelope -> regions -> report."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from . import align, audio, features
from .detect import Params, detect, explain, scores
from .envelope import Envelope, build

ROOT = Path(__file__).resolve().parent.parent
REFS = ROOT / "data" / "refs"
PARAMS = ROOT / "data" / "params.json"
LANES = ["rate", "pause", "pitch_range", "loud"]


def _r(v, n=4):
    if isinstance(v, dict):
        return {k: _r(x, n) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_r(x, n) for x in v]
    if isinstance(v, np.ndarray):
        return _r(v.tolist(), n)
    if isinstance(v, (float, np.floating)):
        return None if not np.isfinite(v) else round(float(v), n)
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, np.bool_):
        return bool(v)
    return v


def measure(x: np.ndarray, transcript: str, locate: bool = False, norm: str = "level") -> dict:
    """Audio (16 kHz, loudness-normalized) -> words + per-word features."""
    offset = 0.0
    if locate:
        a, b = align.locate_text(x, transcript)
        x, offset = x[int(a * audio.SR): int(b * audio.SR)], a
    words = align.align(x, transcript)
    words, feats = features.extract(x, words, norm)
    return {"x": x, "offset": offset, "words": words, "feats": feats}


def save_record(rec: dict, path: Path, meta: dict | None = None) -> None:
    audio.save(path.with_suffix(".wav"), rec["x"])
    path.with_suffix(".json").write_text(json.dumps(_r({
        "words": rec["words"], "feats": rec["feats"], "offset": rec.get("offset", 0.0),
        "meta": meta or {}}), sort_keys=True))


def load_record(path: Path, with_audio: bool = True) -> dict:
    d = json.loads(path.with_suffix(".json").read_text())
    from .envelope import add_derived
    d["feats"] = add_derived({k: np.array([np.nan if v is None else v for v in vals], float)
                              for k, vals in d["feats"].items()})
    d["id"] = path.stem
    if with_audio:
        d["x"] = audio.read_wav(path.with_suffix(".wav"))
    return d


def good_set(text_id: str) -> list[str]:
    sel = json.loads((REFS / text_id / "selection.json").read_text())
    return sel["good"]


def load_refs(text_id: str, ids: list[str] | None = None, exclude: tuple = ()) -> list[dict]:
    ids = ids if ids is not None else good_set(text_id)
    return [load_record(REFS / text_id / i, with_audio=False) for i in ids if i not in exclude]


def load_params(single_reference: bool = False) -> Params:
    """B2 (envelope) parameters, or the separately calibrated B1 (single reference) fallback."""
    f = PARAMS.with_name("params_B1.json") if single_reference else PARAMS
    return Params.load(f) if f.exists() else Params()


def report(rec: dict, env: Envelope, p: Params, ref_ids: list[str], text_id: str | None = None) -> dict:
    regions = detect(rec["feats"], rec["words"], env, p)
    for r in regions:
        r["explanation"] = explain(r, rec["feats"], rec["words"], env)
    lanes = {f: dict(zip(("lo", "hi"), env.band(f, p.margin[f])), value=rec["feats"][f]) for f in LANES}
    out = _r({
        "text_id": text_id,
        "references": ref_ids,
        "k": env.k,
        "words": [{"word": w["word"], "start": w["start"], "end": w["end"]} for w in rec["words"]],
        "stress_points": [int(i) for i in np.flatnonzero(np.logical_or(*env.stress(p.stress_floor)))],
        "regions": regions,
        "scores": scores(regions, rec["words"], p),
        "lanes": lanes,
        "severity_scale": p.sev_scale,
        "params_fitted_on": p.fitted_on,
    })
    out["hash"] = hashlib.sha256(json.dumps(out, sort_keys=True).encode()).hexdigest()[:16]
    return out


def analyze(audio_path: str | Path, text_id: str, transcript: str | None = None,
            k: int | None = None, locate: bool = True, exclude: tuple = ()) -> tuple[dict, dict]:
    """Full analysis of one upload against a text's good renditions.

    `exclude` removes renditions from the envelope, e.g. the reading a demo clip was made from.
    """
    from .data.texts import TEXTS
    transcript = transcript or TEXTS[text_id]["text"]
    x = audio.preprocess(audio_path)
    rec = measure(x, transcript, locate=locate)
    ids = [g for g in good_set(text_id) if g not in exclude][: k or None]
    refs = load_refs(text_id, ids)
    env = build([r["feats"] for r in refs])
    return report(rec, env, load_params(single_reference=len(ids) == 1), ids, text_id), rec
