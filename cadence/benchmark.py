"""Calibrate on T1, evaluate on every eligible held-out text, write results/results.json and results.md."""
from __future__ import annotations

import json
import math

from . import evaluate as E
from .human import summarize_listening
from .metrics import spearman
from .pipeline import PARAMS, ROOT, _r

RESULTS = ROOT / "results"
MAIN = E.Config()
STATUS_NOTE = ("**Detector v2** (2026-10-14: self-relative pace/monotone channels, perceptible stress points). "
               "Thresholds fitted on T1 only. The v2 changes were partly motivated by inspecting T3/T4, so "
               "**T2-T4 are development feedback**; **T6 is the untouched final test** (added after v2 was "
               "frozen, evaluated once). T3 and T4 are two passages read by the same 19 readers, so they are "
               "not independent. The frozen v1 results are in results/frozen_v1_2026-10-14/.")
METHODS = {"B0 generic norms": E.Config(method="B0"), "B1 single reference (K=1)": E.Config(k=1),
           "B2 envelope (K=all), ours": MAIN}
ABLATIONS = {
    "v1 detector (frozen design)": E.Config(relative=False, stress_floor=False),
    "v2 without relative channels": E.Config(relative=False),
    "v2 without stress floor": E.Config(stress_floor=False),
    "K=1": E.Config(k=1), "K=2": E.Config(k=2), "K=4": E.Config(k=4), "K=all": MAIN,
    "norm off": E.Config(norm="off"), "norm z-score (v1)": E.Config(norm="zscore"),
    "no null-edit margin": E.Config(margin=False),
}
def ms_at_fa(pts: list[dict], budget: float):
    """Best Matching Score among sweep points with false alarms/min <= budget (step, no extrapolation)."""
    ok = [p["matching_score"] for p in pts if p["fa_per_min"] <= budget + 1e-9]
    return max(ok) if ok else None


def eligible_tests() -> list[str]:
    """Held-out texts with a ladder manifest (>= MIN_GOOD good renditions)."""
    from .data.texts import test_texts
    return [t for t in test_texts() if (E.LADDERS / t / "manifest.json").exists()]


TEST = eligible_tests()


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
    b1 = params[E.Config(k=1)]
    b1.lam = dict(params[MAIN].lam)  # same rubric scale as B2, so fallback scores are comparable
    b1.save(PARAMS.with_name("params_B1.json"))  # single-reference fallback
    for name, cfg in METHODS.items():
        out["methods"][name] = {t: E.run(cfg, params[cfg], t) for t in ["T1", *TEST]}
    if ablations:
        for name, cfg in ABLATIONS.items():
            out["ablations"][name] = {t: E.run(cfg, params[cfg], t) for t in TEST}
    for t in TEST:
        out["sweep"][t] = {n: E.sweep(c, params[c], t) for n, c in
                           [("B1 single reference", E.Config(k=1)), ("B2 envelope", MAIN)]}
    # equal false-alarm comparison: Matching Score interpolated on each method's sweep curve
    out["equal_fa"] = {t: {n: {str(b): ms_at_fa(pts, b) for b in (0.25, 0.5, 1.0, 2.0)}
                           for n, pts in out["sweep"][t].items()} for t in TEST}
    # natural spectrum: Cadence score of readers not used as references vs human ranking
    out["natural_spectrum"] = {}
    for t in TEST:
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
    out["status_note"] = STATUS_NOTE
    out = json.loads(json.dumps(_r(out)))  # same key types as a reader of results.json sees
    (RESULTS / "results.json").write_text(json.dumps(out, indent=1, sort_keys=True))
    (RESULTS / "results.md").write_text(markdown(out))
    print((RESULTS / "results.md").read_text())
    return out


def markdown(o: dict) -> str:
    L = ["## Results (all numbers as measured; thresholds fitted on T1 only)\n"]
    if o.get("status_note"):
        L.append(o["status_note"] + "\n")
    hdr = ("| Method | Text | Matching Score | Time F1 | Onset err (ms) | Offset err (ms) | "
           "FA/min good pairs | FA/min null-edit | FA/min on ladders, edit-attributable | Severity rho |")
    L += [hdr, "|" + "---|" * 10]
    for name, per in o["methods"].items():
        for t, r in per.items():
            a = r["ladders"]
            L.append(f"| {name} | {t}{' (calib)' if t == 'T1' else ''} | {_f(a['matching_score'], True)} | "
                     f"{_f(a['time_f1'])} | {_f(a['onset_ms_median'], nd=0)} | {_f(a['offset_ms_median'], nd=0)} | "
                     f"{_f(r['fa_per_min_good_pairs'])} | {_f(r['fa_per_min_null_edit'])} | "
                     f"{_f(r.get('fa_per_min_ladder_edit_attributable'))} | {_f(r['severity_spearman'])} |")
    tests = [t for t in next(iter(o["methods"].values())) if t != "T1"]
    tt = " / ".join(tests)

    def sl(per, fn):
        return " / ".join(fn(per[t]) for t in tests if t in per)

    types = list(next(iter(o["methods"].values()))[tests[0]]["by_type"])
    L += [f"\n### Matching Score by flaw type ({tt})\n", "| Method | " + " | ".join(types) + " |",
          "|---|" + "---|" * len(types)]
    for name, per in o["methods"].items():
        L.append(f"| {name} | " + " | ".join(sl(per, lambda r, t=t: _f(r["by_type"][t], True)) for t in types) + " |")
    L += [f"\n### Per-flaw precision / recall, B2 ({tt}): recall = Matching Score (type + IoU >= 0.5); "
          "precision = share of flags overlapping a label of the same type (raw, then excluding flags the "
          "untouched source also gets)\n", "| Type | " + " | ".join(f"{t} R / P raw / P edit" for t in tests) + " |",
          "|---|" + "---|" * len(tests)]
    b2 = o["methods"][[m for m in o["methods"] if m.startswith("B2")][0]]
    for typ in types:
        cells = []
        for t in tests:
            pt = b2[t].get("per_type", {}).get(typ)
            cells.append("n/a" if not pt else f"{_f(pt['recall_matching'], True)} / {_f(pt['precision_time'], True)} / "
                                              f"{_f(pt['precision_edit'], True)} (n={pt['predictions']})")
        L.append(f"| {typ} | " + " | ".join(cells) + " |")
    if o.get("equal_fa"):
        L += [f"\n### Matching Score at equal false-alarm budgets (best sweep point at or below the budget)\n",
              "| Text | Method | <= 0.25/min | <= 0.5/min | <= 1/min | <= 2/min |", "|---|---|---|---|---|---|"]
        for t, per in o["equal_fa"].items():
            for n, v in per.items():
                L.append(f"| {t} | {n} | " + " | ".join(_f(v[b], True) for b in ("0.25", "0.5", "1.0", "2.0")) + " |")
    L += [f"\n### Matching Score by injected severity ({tt})\n", "| Method | 1 | 2 | 3 | 4 | 5 |",
          "|---|---|---|---|---|---|"]
    for name, per in o["methods"].items():
        L.append(f"| {name} | " + " | ".join(
            sl(per, lambda r, lv=lv: _f(r["by_level"][str(lv)], True)) for lv in range(1, 6)) + " |")
    if o["ablations"]:
        L += [f"\n### Ablations ({tt})\n", "| Variant | Matching Score | FA/min good pairs | FA/min null-edit |",
              "|---|---|---|---|"]
        for name, per in o["ablations"].items():
            L.append(f"| {name} | {sl(per, lambda r: _f(r['ladders']['matching_score'], True))} | "
                     f"{sl(per, lambda r: _f(r['fa_per_min_good_pairs']))} | "
                     f"{sl(per, lambda r: _f(r['fa_per_min_null_edit']))} |")
    L += [f"\n### Compound clips ({tt})\n"]
    for name, per in o["methods"].items():
        L.append(f"- {name}: Matching Score "
                 + sl(per, lambda r: _f(r["compound"]["matching_score"] if r["compound"] else None, True)))
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
    for f in sorted(RESULTS.glob("robustness_*.json")):
        rb = json.loads(f.read_text())
        L += [f"\n### Robustness ({f.stem.split('_')[1]} ladders, severities 3 and 5, envelope K=all)\n",
              "| Condition | Matching Score | Time F1 | Onset err (ms) |", "|---|---|---|---|"]
        L += [f"| {k} | {_f(a['matching_score'], True)} | {_f(a['time_f1'])} | {_f(a['onset_ms_median'], nd=0)} |"
              for k, a in rb.items()]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
