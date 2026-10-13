"""Reproducible demo case, chosen from computed results (spec section 9).

`cadence demo` scans the flawed ladder clips of one speech text, runs B0, B1 and B2 on each
(with the calibrated parameters in results/results.json), and picks the case to show:
rushed pace if B2 truly matches it (type correct, IoU >= 0.5), otherwise the best genuinely
detected flaw, preferring cases where the baselines miss or mislocate it. Nothing is
hard-coded: the choice, the numbers and the verification are written to
data/demo/demo_<T>.json, which the dashboard's Demo tab reads.
"""
from __future__ import annotations

import json

from . import evaluate as E
from .detect import Params
from .metrics import iou
from .pipeline import REFS, ROOT

DEMO = ROOT / "data" / "demo"
PREFERENCE = ["pace", "monotone", "missed_emphasis", "misplaced_pause", "missing_pause", "volume_fade"]
METHODS = {"B0 generic norms": E.Config(method="B0"), "B1 single reference (K=1)": E.Config(k=1),
           "B2 consensus envelope (K=all)": E.Config()}


def _params() -> dict[str, Params]:
    res = json.loads((ROOT / "results" / "results.json").read_text())["params"]
    return {"B0 generic norms": Params(**res.get("B0 generic norms", {})),
            "B1 single reference (K=1)": Params(**res["K=1"]),
            "B2 consensus envelope (K=all)": Params(**res["K=all"])}


def _best(lab: dict, preds: list[dict]) -> dict:
    same = [(iou(lab, p), p) for p in preds if p["type"] == lab["type"]]
    v, p = max(same, key=lambda s: s[0]) if same else (0.0, None)
    any_overlap = [q["type"] for q in preds if min(q["end"], lab["end"]) > max(q["start"], lab["start"])]
    return {"matched": v >= 0.5, "iou": round(v, 3),
            "region": None if p is None else {k: p[k] for k in ("type", "start", "end", "w0", "w1", "d_mean")},
            "types_overlapping_label": any_overlap, "n_flags": len(preds)}


def choose(tid: str = "T3") -> dict:
    params = _params()
    cands = []
    for c in E.clip_items(tid):
        lab = c["labels"][0]
        if lab["severity"] < 4:
            continue
        res = {}
        for name, cfg in METHODS.items():
            preds, _ = E.predict(cfg, params[name], "clip", tid, c["id"], c["source"])
            res[name] = _best(lab, preds)
        b2 = res["B2 consensus envelope (K=all)"]
        if not b2["matched"]:
            continue
        baseline_ok = sum(res[n]["matched"] for n in ("B0 generic norms", "B1 single reference (K=1)"))
        sub = lab.get("subtype", "")
        rank = (PREFERENCE.index(lab["type"]) if not (lab["type"] == "pace" and sub == "rushed") else -1,
                baseline_ok, -b2["iou"], -lab["severity"])
        cands.append((rank, c, res))
    if not cands:
        raise SystemExit(f"No {tid} clip at severity >= 4 is matched by B2; no demo case to show.")
    cands.sort(key=lambda x: x[0])
    _, c, res = cands[0]
    lab = c["labels"][0]
    words, _, _ = E.record("clip", tid, c["id"])
    src_flags, _ = E.predict(METHODS["B2 consensus envelope (K=all)"], params["B2 consensus envelope (K=all)"],
                             "clip", tid, f"{tid}_null_{c['source']}", c["source"])
    meta = json.loads((REFS / tid / f"{c['source']}.json").read_text())["meta"]
    out = {
        "text_id": tid, "clip_id": c["id"], "flawed_wav": f"data/ladders/{tid}/{c['id']}.wav",
        "source_id": c["source"], "source_wav": f"data/refs/{tid}/{c['source']}.wav",
        "source_speaker": meta.get("reader"), "source_licence": meta.get("licence"),
        "label": lab, "label_words": " ".join(w["word"] for w in words[lab["w0"]:lab["w1"] + 1]),
        "methods": res,
        "b2_flags_on_untouched_source": [{k: q[k] for k in ("type", "w0", "w1", "start", "end")} for q in src_flags],
        "candidates_considered": len(cands),
        "selection_rule": "rushed pace if B2 matches it; else first of " + ", ".join(PREFERENCE)
                          + "; prefer cases the baselines miss; then higher IoU",
    }
    DEMO.mkdir(parents=True, exist_ok=True)
    # copy both recordings into data/demo/ (tracked in git) so the Demo tab plays from a clone
    import shutil
    for key, name in (("source_wav", "reference"), ("flawed_wav", "flawed")):
        dst = DEMO / f"demo_{tid}_{name}.wav"
        shutil.copyfile(ROOT / out[key], dst)
        out[key] = str(dst.relative_to(ROOT))
    (DEMO / f"demo_{tid}.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps({k: out[k] for k in ("clip_id", "label", "methods")}, indent=1, default=float))
    return out
