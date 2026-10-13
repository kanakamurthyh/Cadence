"""Dataset factory step 1: every LibriVox reading -> cropped, aligned, measured record.

Writes data/refs/<T>/<id>.wav|json and selection.json. The good set is chosen
from the human ranking in data/rankings/<T>.csv when it exists (spec: three
teammates rank all readers on a 20 s excerpt). Until then a PROVISIONAL ranking
by mean aligner confidence (clarity and fidelity to the text, independent of
the prosodic features we judge) is used and labelled as such.
"""
import argparse
import csv
import json
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

os.environ.setdefault("OMP_NUM_THREADS", "2")

from cadence import audio  # noqa: E402
from cadence.data.texts import TEXTS  # noqa: E402
from cadence.pipeline import REFS, measure, save_record  # noqa: E402

GOOD_K = 6


def _one(args):
    tid, src = args
    out = REFS / tid / src["id"]
    if out.with_suffix(".json").exists():
        return src["id"], "cached"
    import torch
    torch.set_num_threads(2)
    try:
        x = audio.preprocess(src["mp3"])
        rec = measure(x, TEXTS[tid]["text"], locate=True)
        conf = float(np.mean([w["score"] for w in rec["words"]]))
        save_record(rec, out, {"reader": src["reader"], "url": src["url"], "book_id": src["book_id"],
                               "align_conf": conf, "duration": len(rec["x"]) / audio.SR,
                               "licence": "Public domain (LibriVox)"})
        return src["id"], f"ok conf={conf:.3f}"
    except Exception as e:  # noqa: BLE001
        return src["id"], f"FAILED {e!r}"


def select(tid: str) -> dict:
    srcs = Path("data/raw") / tid / "sources.json"
    src = {r["id"]: r for r in json.loads(srcs.read_text())} if srcs.exists() else {}
    recs = []
    for p in sorted((REFS / tid).glob("lv*.json")):
        d = json.loads(p.read_text())
        m = d["meta"]
        if p.stem in src and m.get("reader") != src[p.stem]["reader"]:  # backfill metadata
            s = src[p.stem]
            m.update(reader=s["reader"], url=s["url"], book_id=s["book_id"])
            p.write_text(json.dumps(d, sort_keys=True))
        recs.append((p.stem, m))
    human = Path("data/rankings") / f"{tid}.csv"
    if human.exists():  # rows: id, rank_by_rater1, rank_by_rater2, rank_by_rater3
        rows = list(csv.DictReader(human.open()))
        mean_rank = {r["id"]: np.mean([float(v) for k, v in r.items() if k != "id" and v]) for r in rows}
        order = sorted(mean_rank, key=mean_rank.get)
        method = f"human ranking ({human})"
    else:
        order = [i for i, m in sorted(recs, key=lambda r: -r[1]["align_conf"])]
        method = "PROVISIONAL: mean aligner confidence; replace with the 3-teammate ranking"
    sel = {"good": order[:GOOD_K], "ranking": order, "method": method}
    (REFS / tid / "selection.json").write_text(json.dumps(sel, indent=1))
    return sel


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--texts", nargs="*", default=list(TEXTS))
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    jobs = []
    for tid in a.texts:
        (REFS / tid).mkdir(parents=True, exist_ok=True)
        srcs = Path("data/raw") / tid / "sources.json"
        if srcs.exists():
            rows = json.loads(srcs.read_text())
        else:  # fetch still running: use whatever is on disk
            rows = [{"id": p.stem, "mp3": str(p), "reader": p.stem, "url": "", "book_id": 0}
                    for p in sorted((Path("data/raw") / tid).glob("*.mp3"))]
        jobs += [(tid, r) for r in rows]
    with ProcessPoolExecutor(a.workers) as ex:
        for rid, status in ex.map(_one, jobs):
            print(rid, status, flush=True)
    for tid in a.texts:
        s = select(tid)
        print(tid, s["method"], s["good"])
