"""Calibrate on T1, evaluate on every eligible held-out text, write results/results.json and results.md."""
from __future__ import annotations

import json
import math

from . import evaluate as E
from .human import summarize_listening
from .metrics import spearman
from .pipeline import PARAMS, ROOT, _r

RESULTS = ROOT / "results"
MAIN = E.Config(phrase=True)
STATUS_NOTE = (
    "**Detector v3 candidate vs v2** (dataset v3: emphasis targets at perceptible stress points). "
    "Thresholds fitted on T1 only; never retuned on T2/T3. "
    "T2–T6 are development texts (T6 was used once for v2, so it is no longer untouched). "
    "T7 (Speech Accent Archive, Indian L1 speakers) and T8 (Tagore) added after detector v3 was "
    "designed and evaluated once; frozen v1 results in results/frozen_v1_2026-10-14/, "
    "frozen v2 results in results/frozen_v2_2026-10-14/. "
    "An automatic, pre-registered ship rule chooses between detector v3 (phrase channels) and v2."
)
METHODS = {"B0 generic norms": E.Config(method="B0"), "B1 single reference (K=1)": E.Config(k=1),
           "B2 envelope (K=all), ours": MAIN}
ABLATIONS = {
    "v1 detector (frozen design)": E.Config(relative=False, stress_floor=False),
    "v2 without relative channels": E.Config(relative=False),
    "v2 without stress floor": E.Config(stress_floor=False),
    "K=1": E.Config(k=1), "K=2": E.Config(k=2), "K=4": E.Config(k=4), "K=all": MAIN,
    "norm off": E.Config(norm="off"), "norm z-score (v1)": E.Config(norm="zscore"),
    "no null-edit margin": E.Config(margin=False),
    "v2 detector (no phrase channels)": E.Config(),
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


def ship_decision(v3: dict, v2: dict, fa_cap: float = 2.0) -> dict:
    """Decide whether to ship detector v3 or fall back to v2.

    Args:
        v3: {text_id: E.run() output} for the v3 detector (phrase=True).
        v2: {text_id: E.run() output} for the v2 detector (phrase=False).
             Must include "T1"; held-out texts are all keys other than "T1".
        fa_cap: maximum allowed FA/min on good pairs for held-out texts.

    Rule: ship v3 iff
      (1) v3 matching score > v2 on T1,
      (2) v3 matching score > v2 on >= 2 held-out texts, AND
      (3) on every held-out text where v2 FA/min <= fa_cap, v3 FA/min <= fa_cap.

    Returns:
        {"ship": "v3"|"v2", "t1": {...}, "wins": [...], "losses": [...],
         "fa_violations": [...], "reason": str}
    """
    t1_v3 = v3["T1"]["ladders"]["matching_score"]
    t1_v2 = v2["T1"]["ladders"]["matching_score"]
    t1_wins = t1_v3 > t1_v2

    held_out = [t for t in v3 if t != "T1"]
    wins = [t for t in held_out if v3[t]["ladders"]["matching_score"] > v2[t]["ladders"]["matching_score"]]
    losses = [t for t in held_out if t not in wins]

    # FA cap violated on a held-out text where v2 is within the cap
    fa_violations = [
        t for t in held_out
        if v2[t]["fa_per_min_good_pairs"] <= fa_cap and v3[t]["fa_per_min_good_pairs"] > fa_cap
    ]

    if t1_wins and len(wins) >= 2 and not fa_violations:
        ship = "v3"
        reason = (
            f"v3 beats v2 on T1 (MS {t1_v3:.3f} vs {t1_v2:.3f}) "
            f"and on {len(wins)} held-out text(s) with no FA cap violations"
        )
    else:
        ship = "v2"
        parts = []
        if not t1_wins:
            parts.append(f"v3 does not beat v2 on T1 (MS {t1_v3:.3f} vs {t1_v2:.3f})")
        if len(wins) < 2:
            parts.append(f"v3 beats v2 on only {len(wins)} held-out text(s) (need >= 2)")
        if fa_violations:
            parts.append(f"FA cap exceeded on {fa_violations}")
        reason = "; ".join(parts) if parts else "unknown"

    return {
        "ship": ship,
        "t1": {"v3_ms": t1_v3, "v2_ms": t1_v2, "v3_wins": t1_wins},
        "wins": wins,
        "losses": losses,
        "fa_violations": fa_violations,
        "reason": reason,
    }


def main(ablations: bool = True) -> dict:
    RESULTS.mkdir(exist_ok=True)
    out = {"calibration_text": "T1", "methods": {}, "ablations": {}, "sweep": {}, "params": {}}
    params = {}
    for name, cfg in {**METHODS, **(ABLATIONS if ablations else {})}.items():
        if cfg not in params:
            print("calibrating", name, flush=True)
            params[cfg] = E.calibrate(cfg, full=(cfg == MAIN))
            out["params"][cfg.name] = params[cfg].__dict__
    # params[MAIN].save(PARAMS) moved to after ship decision (saves the winner)
    for name, cfg in METHODS.items():
        out["methods"][name] = {t: E.run(cfg, params[cfg], t) for t in ["T1", *TEST]}
    if ablations:
        # Run ablations on T1 as well (cheap: reuse calibrated params; needed for ship_decision)
        for name, cfg in ABLATIONS.items():
            out["ablations"][name] = {t: E.run(cfg, params[cfg], t) for t in ["T1", *TEST]}

    # -- Ship decision: v3 (MAIN, phrase=True) vs v2 (phrase=False) ----------
    v2_cfg = E.Config()
    v3_results = out["methods"]["B2 envelope (K=all), ours"]
    if ablations:
        v2_results = out["ablations"]["v2 detector (no phrase channels)"]
    else:
        if v2_cfg not in params:
            params[v2_cfg] = E.calibrate(v2_cfg)
        v2_results = {t: E.run(v2_cfg, params[v2_cfg], t) for t in ["T1", *TEST]}
    decision = ship_decision(v3_results, v2_results)
    out["ship_decision"] = decision

    # Save the WINNER's params; b1.lam from the same winner
    winner_cfg = MAIN if decision["ship"] == "v3" else v2_cfg
    params[winner_cfg].save(PARAMS)
    b1 = params[E.Config(k=1)]
    b1.lam = dict(params[winner_cfg].lam)  # same rubric scale as B2, so fallback scores are comparable
    b1.save(PARAMS.with_name("params_B1.json"))  # single-reference fallback

    # If v2 ships: update headline table to show v2; stash v3 under ablations
    if decision["ship"] == "v2":
        v3_stash = {t: v3_results[t] for t in TEST if t in v3_results}
        out["ablations"]["v3 detector (phrase channels)"] = v3_stash
        out["methods"]["B2 envelope (K=all), ours"] = {
            t: E.run(v2_cfg, params[v2_cfg], t) for t in ["T1", *TEST]
        }

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
    if o.get("ship_decision"):
        sd = o["ship_decision"]
        L += ["\n### Ship decision (v3 vs v2, dataset v3)\n"]
        t1d = sd["t1"]
        L.append(f"- **Shipped: detector {sd['ship']}**")
        L.append(f"- T1: v3 MS = {_f(t1d['v3_ms'], True)}, v2 MS = {_f(t1d['v2_ms'], True)}, "
                 f"v3 wins T1: {t1d['v3_wins']}")
        L.append(f"- Held-out wins: {sd['wins'] or 'none'}")
        L.append(f"- Held-out losses: {sd['losses'] or 'none'}")
        L.append(f"- FA cap violations: {sd['fa_violations'] or 'none'}")
        L.append(f"- Reason: {sd['reason']}")
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
