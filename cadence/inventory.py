"""`cadence inventory`: every recording, its source, licence and files, and dataset counts.

Writes data/inventory.csv (one row per recording) and data/inventory.json (counts,
alignment quality, good-set method, speaker overlap between texts).
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from itertools import combinations

import numpy as np

from .data.texts import MIN_GOOD, TEXTS
from .pipeline import REFS, ROOT

LADDERS = ROOT / "data" / "ladders"


def _speaker(reader: str) -> str:
    return " ".join(reader.lower().replace("(", " ").split()[:2])


def main() -> dict:
    rows, summary = [], {}
    speakers = defaultdict(set)
    for tid, t in TEXTS.items():
        sel_p = REFS / tid / "selection.json"
        if not sel_p.exists():
            continue
        sel = json.loads(sel_p.read_text())
        good = set(sel["good"])
        confs = []
        for p in sorted(q for q in (REFS / tid).glob("*.json") if q.stem != "selection"):
            d = json.loads(p.read_text())
            m = d["meta"]
            low = sum(w["score"] < 0.5 for w in d["words"])
            confs.append(m["align_conf"])
            speakers[tid].add(_speaker(m.get("reader", p.stem)))
            rows.append({
                "text_id": tid, "text_title": t["title"], "role": t["role"], "recording_id": p.stem,
                "speaker": m.get("reader"), "in_good_set": p.stem in good,
                "rank": sel["ranking"].index(p.stem) + 1 if p.stem in sel["ranking"] else None,
                "source_url": m.get("url"), "licence": m.get("licence"), "provenance": m.get("provenance"),
                "raw_file": m.get("source_file"), "cropped_wav": f"data/refs/{tid}/{p.stem}.wav",
                "offset_in_source_s": m.get("offset_in_source_s", d.get("offset")),
                "duration_s": round(m["duration"], 2), "align_conf": round(m["align_conf"], 4),
                "low_conf_words": low, "words": len(d["words"]),
            })
        man_p = LADDERS / tid / "manifest.json"
        kinds = defaultdict(int)
        if man_p.exists():
            for c in json.loads(man_p.read_text()):
                kinds[c["kind"]] += 1
        summary[tid] = {
            "title": t["title"], "role": t["role"], "recordings": len(confs), "speakers": len(speakers[tid]),
            "good_set": sel["good"], "good_set_method": sel["method"],
            "eligible_for_envelope": len(sel["good"]) >= MIN_GOOD,
            "align_conf_median": round(float(np.median(confs)), 3), "align_conf_min": round(float(min(confs)), 3),
            "synthetic_clips": dict(kinds),
        }
    overlap = {f"{a}-{b}": sorted(speakers[a] & speakers[b])
               for a, b in combinations(summary, 2) if speakers[a] & speakers[b]}
    # calibration uses only T1's good set (envelopes, LOO false alarms, ladder source)
    cal = {_speaker(r["speaker"] or "") for r in rows if r["text_id"] == "T1" and r["in_good_set"]}
    leak = {tid: sorted(cal & speakers[tid]) for tid, t in TEXTS.items()
            if t["role"].startswith("test") and tid in speakers}
    out = {"texts": summary, "speaker_overlap": overlap,
           "calibration_speakers_in_test_texts": leak,
           "totals": {"recordings": len(rows),
                      "synthetic_clips": sum(sum(s["synthetic_clips"].values()) for s in summary.values())}}
    with (ROOT / "data" / "inventory.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    (ROOT / "data" / "inventory.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    return out
