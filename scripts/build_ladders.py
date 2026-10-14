"""Dataset factory step 2: synthetic ladders and null-edit controls (spec section 8).

For each text: 6 flaw types x 2 word spans x 5 severities injected into the
top-ranked good rendition (fixed seed), a null-edit copy of every good
rendition, and compound clips (two flaws each). Every clip is then measured
(aligned with the known transcript, features extracted) and cached.

Writes data/ladders/<T>/<clip>.wav|json and data/ladders/<T>/manifest.json.
"""
import argparse
import json
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

os.environ.setdefault("OMP_NUM_THREADS", "2")

from cadence import inject  # noqa: E402
from cadence.data.texts import TEXTS  # noqa: E402
from cadence.envelope import build  # noqa: E402
from cadence.pipeline import REFS, ROOT, _r, good_set, load_record, load_refs, measure, save_record  # noqa: E402

LADDERS = ROOT / "data" / "ladders"
SEED = 20261013
COMPOUND = {"T1": 2, "T2": 4, "T3": 4}  # other texts: 4
SINGLE_TYPES = ["pace_rushed", "pace_dragging", "missing_pause", "misplaced_pause",
                "monotone", "missed_emphasis", "volume_fade"]


def plan(tid: str, dataset: int = 3) -> list[dict]:
    """The full list of clips for one text (deterministic).

    dataset=3 (default): emphasis targets perceptible consensus stress points
    (stress_rule=2, perceptible mask).  dataset=2: legacy behaviour (any
    positive prominence, stress_rule=1) — labels and audio reproduce (manifests
    now also carry dataset_version).
    """
    good = good_set(tid)
    top = good[0]
    ref = load_record(REFS / tid / top)
    others = load_refs(tid, exclude=(top,))
    env = build([r["feats"] for r in others])
    rng = np.random.default_rng(SEED + int(tid[1:]))
    if dataset >= 3:
        stress_mask = env.stress_pitch_p | env.stress_loud_p
        stress_rule = 2
    else:
        stress_mask = env.stress_pitch | env.stress_loud
        stress_rule = 1
    spans = inject.choose_spans(ref["words"], ref["feats"], stress_mask, rng,
                                others_pause=np.stack([r["feats"]["pause"] for r in others]),
                                rule=TEXTS[tid].get("span_rule", 1),
                                stress_rule=stress_rule)
    clips = []
    for g in good:
        clips.append({"id": f"{tid}_null_{g}", "source": g, "flaws": [], "kind": "null",
                      "dataset_version": dataset})
    for typ in SINGLE_TYPES:
        for si, (w0, w1) in enumerate(spans[typ]):
            for lvl in range(1, 6):
                name = typ.replace("pace_", "pace-")
                sidx = si if not typ.startswith("pace") else (0 if typ.endswith("rushed") else 1)
                clips.append({"id": f"{tid}_{name}_s{sidx}_L{lvl}", "source": top, "kind": "ladder",
                              "flaws": [[typ, lvl, w0, w1]], "dataset_version": dataset})
    # compound: two different flaw types on non-overlapping spans, severity 4
    pool = [(t, s) for t in SINGLE_TYPES for s in spans[t]]
    made = 0
    for _ in range(200):
        if made >= COMPOUND.get(tid, 4):
            break
        i, j = rng.choice(len(pool), 2, replace=False)
        (t1, s1), (t2, s2) = pool[i], pool[j]
        if t1.split("_")[0] == t2.split("_")[0] or not (s1[1] + 2 < s2[0] or s2[1] + 2 < s1[0]):
            continue
        clips.append({"id": f"{tid}_compound_{made}", "source": top, "kind": "compound",
                      "flaws": [[t1, 4, *s1], [t2, 4, *s2]], "dataset_version": dataset})
        made += 1
    return clips


def _same_plan(meta: dict, c: dict) -> bool:
    """A cached clip is reusable only if made from the same rendition with the same flaws."""
    if meta.get("source") != c["source"]:
        return False
    if "flaws" in meta:
        return meta["flaws"] == c["flaws"]
    # clips cached before "flaws" was stored: compare labels against the plan
    labs = meta.get("labels", [])
    return len(labs) == len(c["flaws"]) and all(
        l["w0"] == f[2] and l["severity"] == f[1] for l, f in zip(labs, c["flaws"]))


def _render(args):
    tid, c = args
    out = LADDERS / tid / c["id"]
    if out.with_suffix(".json").exists():
        meta = json.loads(out.with_suffix(".json").read_text())["meta"]
        if _same_plan(meta, c):
            return c["id"], meta["labels"]
        # the good set or spans changed (e.g. after a human ranking): re-render, never reuse
    import torch
    torch.set_num_threads(2)
    ref = load_record(REFS / tid / c["source"])
    clip = inject.Clip(ref["x"], ref["words"])
    for typ, lvl, w0, w1 in c["flaws"]:
        extra = {"loud_excess": inject.loud_excess(ref["x"], ref["words"], w0)} if typ == "missed_emphasis" else None
        inject.add_flaw(clip, typ, lvl, w0, w1, extra)
    y = clip.render()
    labels = inject.finalize_labels(clip)
    rec = measure(y, TEXTS[tid]["text"])
    save_record(rec, out, {"labels": labels, "source": c["source"], "kind": c["kind"], "flaws": c["flaws"],
                           "duration": len(y) / 16000})
    return c["id"], labels


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--texts", nargs="*", default=list(TEXTS))
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--dataset", type=int, choices=[2, 3], default=3,
                    help="Dataset version: 3 (default) targets perceptible consensus stress points; "
                         "2 reproduces the legacy labels and audio (manifests now also carry dataset_version).")
    a = ap.parse_args()
    jobs = []
    from cadence.data.texts import MIN_GOOD
    for tid in list(a.texts):
        if len(good_set(tid)) < MIN_GOOD:
            print(tid, f"skipped: fewer than {MIN_GOOD} good renditions (add teammate takes)", flush=True)
            a.texts.remove(tid)
            continue
        (LADDERS / tid).mkdir(parents=True, exist_ok=True)
        clips = plan(tid, dataset=a.dataset)
        jobs += [(tid, c) for c in clips]
        print(tid, len(clips), "clips planned", flush=True)
    labels = {}
    with ProcessPoolExecutor(a.workers) as ex:
        for cid, lab in ex.map(_render, jobs):
            labels[cid] = lab
    for tid in a.texts:
        man = [{**c, "labels": labels[c["id"]]} for t, c in jobs if t == tid]
        (LADDERS / tid / "manifest.json").write_text(json.dumps(_r(man), indent=1))
        print(tid, "manifest written:", len(man), "clips")
