"""`cadence status`: is each human-data step present and consistent?"""
from __future__ import annotations

import csv
import json
import runpy
import sys

from .data.texts import TEXTS
from .pipeline import PARAMS, REFS, ROOT

RANK = ROOT / "data" / "rankings"
NEED_RATERS, NEED_LISTENERS = 3, 5


def rankings() -> dict:
    out = {}
    for tid in TEXTS:
        readers = sorted(p.stem for p in (REFS / tid).glob("lv*.json"))
        f = RANK / f"{tid}_ratings.csv"
        rows = list(csv.DictReader(f.open())) if f.exists() else []
        raters = sorted({r["rater"] for r in rows})
        cover = {ra: len({r["id"] for r in rows if r["rater"] == ra}) for ra in raters}
        sel = json.loads((REFS / tid / "selection.json").read_text())
        out[tid] = {"readers": len(readers), "raters": raters, "readers_rated_per_rater": cover,
                    "complete": len(raters) >= NEED_RATERS and all(v == len(readers) for v in cover.values()),
                    "good_set_method": sel["method"], "good_set": sel["good"],
                    "selection_is_human": "human" in sel["method"]}
    return out


def ladders() -> dict:
    sys.argv = ["x"]
    m = runpy.run_path(str(ROOT / "scripts" / "build_ladders.py"), run_name="lib")
    out = {}
    for tid in TEXTS:
        plan = m["plan"](tid)
        stale = missing = 0
        for c in plan:
            p = ROOT / "data" / "ladders" / tid / f"{c['id']}.json"
            if not p.exists():
                missing += 1
            elif not m["_same_plan"](json.loads(p.read_text())["meta"], c):
                stale += 1
        man = ROOT / "data" / "ladders" / tid / "manifest.json"
        man_src = {c["source"] for c in json.loads(man.read_text()) if c["kind"] == "ladder"} if man.exists() else set()
        out[tid] = {"planned": len(plan), "missing": missing, "stale": stale,
                    "manifest_matches_plan": man_src == {c["source"] for c in plan if c["kind"] == "ladder"},
                    "consistent": missing == 0 and stale == 0}
    return out


def main() -> dict:
    from .human import listening_trials, responses, summarize_listening
    from .natural import check
    res = {"rankings": rankings(), "ladders": ladders()}
    lt = summarize_listening()
    res["listening"] = {"status": lt["status"], "complete_listeners": lt.get("complete_listeners", []),
                        "trials_per_listener": len(listening_trials()),
                        "rows_current": len(responses()), "rows_stale": len(responses(False)) - len(responses()),
                        "complete": len(lt.get("complete_listeners", [])) >= NEED_LISTENERS}
    res["natural"] = check()
    p = json.loads(PARAMS.read_text()) if PARAMS.exists() else {}
    res["params"] = {"severity_scale": p.get("sev_scale"), "fitted_on": p.get("fitted_on")}
    print(json.dumps(res, indent=1))
    steps = [
        ("1 rankings complete", all(r["complete"] for r in res["rankings"].values())),
        ("2 good set from human ranking", all(r["selection_is_human"] for r in res["rankings"].values())),
        ("2 ladders consistent with good set", all(l["consistent"] and l["manifest_matches_plan"]
                                                   for l in res["ladders"].values())),
        ("3 listening test (5 complete listeners)", res["listening"]["complete"]),
        ("4 takes + 2 annotators, no problems", res["natural"]["takes"] > 0 and not res["natural"]["problems"]),
        ("5 severity map on perceived scale", str(res["params"]["severity_scale"]).startswith("perceived")),
    ]
    print("\n".join(f"[{'x' if ok else ' '}] {name}" for name, ok in steps))
    return res
