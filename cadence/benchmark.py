"""Calibrate on T1, evaluate on T2/T3, write results/results.json and results.md."""
from __future__ import annotations

import json
import math

from . import evaluate as E
from .human import summarize_listening
from .metrics import spearman
from .pipeline import PARAMS, ROOT, _r

RESULTS = ROOT / "results"
MAIN = E.Config()
METHODS = {"B0 generic norms": E.Config(method="B0"), "B1 single reference (K=1)": E.Config(k=1),
           "B2 envelope (K=all), ours": MAIN}
ABLATIONS = {
    "K=1": E.Config(k=1), "K=2": E.Config(k=2), "K=4": E.Config(k=4), "K=all": MAIN,
    "norm off": E.Config(norm="off"), "norm z-score (v1)": E.Config(norm="zscore"),
    "no null-edit margin": E.Config(margin=False),
}
TEST = ["T2", "T3"]


def _f(v, pct=False, nd=2):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "n/a"
    return f"{100 * v:.0f}%" if pct else f"{v:.{nd}f}"


def main(ablations: bool = True) -> dict:
    RESULTS.mkdir(exist_ok=True)
    out = {"calibration_text": "T1", "methods": {}, "ablations": {}, "sweep": {}, "params": {}}
    params = {}
    for name, cfg in {**METHODS, **(ABLATIONS if ablations else {})}.items():
        if cfg not in params:
            print("calibrating", name, flush=True)
            params[cfg] = E.calibrate(cfg, full=(cfg == MAIN))
            out["params"][cfg.name] = params[cfg].__dict__
    params[MAIN].save(PARAMS)
    for name, cfg in METHODS.items():
        out["methods"][name] = {t: E.run(cfg, params[cfg], t) for t in ["T1", *TEST]}
    if ablations:
        for name, cfg in ABLATIONS.items():
            out["ablations"][name] = {t: E.run(cfg, params[cfg], t) for t in TEST}
    for t in TEST:
        out["sweep"][t] = {n: E.sweep(c, params[c], t) for n, c in
                           [("B1 single reference", E.Config(k=1)), ("B2 envelope", MAIN)]}
    # natural spectrum: Cadence score of readers not used as references vs human ranking
    out["natural_spectrum"] = {}
    for t in ["T2", "T3"]:
        sel = E.selection(t)
        sc = E.score_readers(MAIN, params[MAIN], t)
        human = "human" in sel["method"]
        rank = {rid: i for i, rid in enumerate(sel["ranking"])}
        out["natural_spectrum"][t] = {
            "scores": sc, "ranking_method": sel["method"],
            "spearman_vs_ranking": spearman([-rank[i] for i in sc], list(sc.values())) if human else None,
            "status": "ok" if human else "pending human ranking (data/rankings/<T>.csv)",
        }
    out["listening_test"] = summarize_listening()
    out["listening_test"]["severity_vs_listeners_T1"] = E.severity_vs_listeners(MAIN, params[MAIN])
    from .natural import evaluate as natural_eval
    out["natural_flaws"] = natural_eval()
    out = json.loads(json.dumps(_r(out)))  # same key types as a reader of results.json sees
    (RESULTS / "results.json").write_text(json.dumps(out, indent=1, sort_keys=True))
    (RESULTS / "results.md").write_text(markdown(out))
    print((RESULTS / "results.md").read_text())
    return out


def markdown(o: dict) -> str:
    L = ["## Results (all numbers as measured; thresholds fitted on T1 only)\n"]
    hdr = ("| Method | Text | Matching Score | Time F1 | Onset err (ms) | Offset err (ms) | "
           "FA/min good pairs | FA/min null-edit | Severity rho |")
    L += [hdr, "|" + "---|" * 9]
    for name, per in o["methods"].items():
        for t, r in per.items():
            a = r["ladders"]
            L.append(f"| {name} | {t}{' (calib)' if t == 'T1' else ''} | {_f(a['matching_score'], True)} | "
                     f"{_f(a['time_f1'])} | {_f(a['onset_ms_median'], nd=0)} | {_f(a['offset_ms_median'], nd=0)} | "
                     f"{_f(r['fa_per_min_good_pairs'])} | {_f(r['fa_per_min_null_edit'])} | "
                     f"{_f(r['severity_spearman'])} |")
    L += ["\n### Matching Score by flaw type (T2 / T3)\n",
          "| Method | " + " | ".join(o["methods"][next(iter(o["methods"]))]["T2"]["by_type"]) + " |",
          "|---|" + "---|" * 6]
    for name, per in o["methods"].items():
        L.append(f"| {name} | " + " | ".join(
            f"{_f(per['T2']['by_type'][t], True)} / {_f(per['T3']['by_type'][t], True)}"
            for t in per["T2"]["by_type"]) + " |")
    L += ["\n### Matching Score by injected severity (T2 / T3)\n", "| Method | 1 | 2 | 3 | 4 | 5 |", "|---|---|---|---|---|---|"]
    for name, per in o["methods"].items():
        L.append(f"| {name} | " + " | ".join(
            f"{_f(per['T2']['by_level'][str(lv)], True)} / {_f(per['T3']['by_level'][str(lv)], True)}"
            for lv in range(1, 6)) + " |")
    if o["ablations"]:
        L += ["\n### Ablations (T2 / T3)\n", "| Variant | Matching Score | FA/min good pairs | FA/min null-edit |",
              "|---|---|---|---|"]
        for name, per in o["ablations"].items():
            L.append(f"| {name} | {_f(per['T2']['ladders']['matching_score'], True)} / "
                     f"{_f(per['T3']['ladders']['matching_score'], True)} | "
                     f"{_f(per['T2']['fa_per_min_good_pairs'])} / {_f(per['T3']['fa_per_min_good_pairs'])} | "
                     f"{_f(per['T2']['fa_per_min_null_edit'])} / {_f(per['T3']['fa_per_min_null_edit'])} |")
    L += ["\n### Compound clips\n"]
    for name, per in o["methods"].items():
        c = per["T2"]["compound"], per["T3"]["compound"]
        L.append(f"- {name}: Matching Score {_f(c[0]['matching_score'] if c[0] else None, True)} (T2), "
                 f"{_f(c[1]['matching_score'] if c[1] else None, True)} (T3)")
    L += ["\n### Natural spectrum and listening test\n"]
    for t, ns in o["natural_spectrum"].items():
        L.append(f"- {t}: {ns['status']}; Spearman = {_f(ns['spearman_vs_ranking'])}")
    lt = o["listening_test"]
    L.append(f"- Listening test: {lt.get('status', 'see results.json')}")
    sv = lt.get("severity_vs_listeners_T1", {})
    if sv.get("status") == "ok":
        L.append(f"- System severity vs listener rating (T1 listening clips, n={sv['n_clips']}): "
                 f"Spearman = {_f(sv['spearman_system_vs_perceived'])}")
    for typ, v in lt.get("by_type", {}).items():
        L.append(f"  - {typ}: lowest audible level {v['lowest_audible_level']}, "
                 f"injected vs perceived Spearman {_f(v['spearman_injected_vs_perceived'])}")
    nf = o.get("natural_flaws", {})
    L += ["\n### Natural flaws (teammate takes)\n", f"- Status: {nf.get('status', 'n/a')}"]
    for a, r in nf.get("system_vs_annotator", {}).items():
        L.append(f"- Cadence vs {a}: Matching Score {_f(r['matching_score'], True)}, time F1 {_f(r['time_f1'])} "
                 f"({r['takes']} takes)")
    for pair, r in nf.get("annotator_vs_annotator", {}).items():
        L.append(f"- Ceiling, {pair}: Matching Score {_f(r['matching_score'], True)}, time F1 {_f(r['time_f1'])}, "
                 f"mean IoU {_f(r['mean_iou_matched'])}")
    if "unannotated_flags_per_min" in nf:
        L.append(f"- Cadence flags no annotator marked: {_f(nf['unannotated_flags_per_min'])} per minute")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
