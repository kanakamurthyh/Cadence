"""Calibrate on T1, evaluate on every eligible held-out text, write results/results.json and results.md."""
from __future__ import annotations

import dataclasses
import json
import math

from . import evaluate as E
from .human import summarize_listening
from .metrics import spearman
from .pipeline import PARAMS, ROOT, _r

RESULTS = ROOT / "results"
# Module-level alias for the v3 config kept for any external reference; main() uses SHIP (the winner).
MAIN = E.Config(phrase=True)
STATUS_NOTE = (
    "**Detector v3 candidate vs v2** (dataset v3: emphasis targets at perceptible stress points). "
    "Thresholds fitted on T1 only; never retuned on T2/T3. "
    "T2–T6 are development texts (T6 was used once for v2, so it is no longer untouched). "
    "T3 and T4 are two passages read by the same 19 readers, so they are not independent; "
    "T3+T4 can jointly supply two of the required wins in the ship rule. "
    "T7 (Speech Accent Archive, Indian L1 speakers) and T8 (Tagore) added after detector v3 was "
    "designed and evaluated once; frozen v1 results in results/frozen_v1_2026-10-14/, "
    "frozen v2 results in results/frozen_v2_2026-10-14/. "
    "An automatic, pre-registered ship rule chooses between detector v3 (phrase channels) and v2."
)


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


def _ms(r: dict) -> float | None:
    """Extract matching score; return None for missing or non-finite values."""
    v = r["ladders"]["matching_score"]
    if v is None or (isinstance(v, float) and not math.isfinite(v)):
        return None
    return float(v)


def _fa(r: dict) -> float | None:
    """Extract FA/min good pairs; return None for missing or non-finite values."""
    v = r["fa_per_min_good_pairs"]
    if v is None or (isinstance(v, float) and not math.isfinite(v)):
        return None
    return float(v)


def ship_decision(v3: dict, v2: dict, fa_cap: float = 2.0) -> dict:
    """Decide whether to ship detector v3 or fall back to v2.

    Args:
        v3: {text_id: E.run() output} for the v3 detector (phrase=True).
        v2: {text_id: E.run() output} for the v2 detector (phrase=False).
             Must include "T1"; held-out texts are all keys other than "T1".
        fa_cap: maximum allowed FA/min on good pairs for held-out texts.

    Rule: ship v3 iff
      (1) v3 matching score > v2 on T1 (non-finite v3 MS counts as a loss),
      (2) v3 matching score > v2 on >= 2 held-out texts (non-finite v3 MS counts as a loss), AND
      (3) on every held-out text where v2 FA/min <= fa_cap, v3 FA/min <= fa_cap
          (non-finite v3 FA counts as a violation unless v2's is also non-finite).

    Returns:
        {"ship": "v3"|"v2", "t1": {...}, "wins": [...], "losses": [...],
         "fa_violations": [...], "per_text": {...}, "reason": str}
    """
    t1_v3 = _ms(v3["T1"])
    t1_v2 = _ms(v2["T1"])
    t1_wins = t1_v3 is not None and t1_v2 is not None and t1_v3 > t1_v2

    held_out = [t for t in v3 if t != "T1"]
    wins: list[str] = []
    losses: list[str] = []
    for t in held_out:
        ms3 = _ms(v3[t])
        ms2 = _ms(v2[t])
        if ms3 is not None and ms2 is not None and ms3 > ms2:
            wins.append(t)
        else:
            losses.append(t)

    # FA cap violated: v3 FA non-finite or > fa_cap on a text where v2 FA is finite and <= fa_cap
    fa_violations: list[str] = []
    for t in held_out:
        fa3 = _fa(v3[t])
        fa2 = _fa(v2[t])
        if fa2 is not None and fa2 <= fa_cap:
            if fa3 is None or fa3 > fa_cap:
                fa_violations.append(t)

    if t1_wins and len(wins) >= 2 and not fa_violations:
        ship = "v3"
        reason = (
            f"v3 beats v2 on T1 (MS {_f(t1_v3, True)} vs {_f(t1_v2, True)}) "
            f"and on {len(wins)} held-out text(s) with no FA cap violations"
        )
    else:
        ship = "v2"
        parts: list[str] = []
        if not t1_wins:
            parts.append(f"v3 does not beat v2 on T1 (MS {_f(t1_v3, True)} vs {_f(t1_v2, True)})")
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
        "per_text": {
            t: {
                "v3_ms": _ms(v3[t]), "v2_ms": _ms(v2[t]),
                "v3_fa": _fa(v3[t]), "v2_fa": _fa(v2[t]),
            }
            for t in held_out
        },
        "reason": reason,
    }


def report_configs(ship: E.Config, other: E.Config) -> tuple[dict, dict]:
    """Return (METHODS, ABLATIONS) derived from the shipped config.

    Pure function — no I/O, no calibration. Used by main() and tested directly.

    METHODS: B0, B1 = replace(ship, k=1), B2 = ship.

    ABLATIONS (TEST only; no "K=all" row — B2 already shows it):
      K=1..4; norm off/zscore; no margin; without relative channels; without stress floor;
      v1 detector (phrase off + no relative/stress); plus "other candidate" row for `other`.
    """
    b1 = dataclasses.replace(ship, k=1)
    other_label = (
        "other candidate: v2 detector (no phrase channels)"
        if ship.phrase
        else "other candidate: v3 detector (phrase channels)"
    )
    methods = {
        "B0 generic norms": E.Config(method="B0"),
        "B1 single reference (K=1)": b1,
        "B2 envelope (K=all), ours": ship,
    }
    ablations = {
        "K=1": dataclasses.replace(ship, k=1),
        "K=2": dataclasses.replace(ship, k=2),
        "K=4": dataclasses.replace(ship, k=4),
        "norm off": dataclasses.replace(ship, norm="off"),
        "norm z-score (v1)": dataclasses.replace(ship, norm="zscore"),
        "no null-edit margin": dataclasses.replace(ship, margin=False),
        "without relative channels": dataclasses.replace(ship, relative=False),
        "without stress floor": dataclasses.replace(ship, stress_floor=False),
        "v1 detector (frozen design)": dataclasses.replace(
            ship, relative=False, stress_floor=False, phrase=False
        ),
        other_label: other,
    }
    return methods, ablations


def main(ablations: bool = True) -> dict:
    RESULTS.mkdir(exist_ok=True)
    out: dict = {"calibration_text": "T1", "methods": {}, "ablations": {}, "sweep": {}, "params": {}}
    params: dict = {}

    # ── Phase 1: decide which detector to ship ────────────────────────────────
    v3_cfg = E.Config(phrase=True)
    v2_cfg = E.Config()
    for cfg in (v3_cfg, v2_cfg):
        if cfg not in params:
            print("calibrating (phase 1)", cfg.name, flush=True)
            params[cfg] = E.calibrate(cfg, full=True)
            out["params"][cfg.name] = params[cfg].__dict__
    phase1_runs: dict = {
        v3_cfg: {t: E.run(v3_cfg, params[v3_cfg], t) for t in ["T1", *TEST]},
        v2_cfg: {t: E.run(v2_cfg, params[v2_cfg], t) for t in ["T1", *TEST]},
    }
    decision = ship_decision(phase1_runs[v3_cfg], phase1_runs[v2_cfg])
    out["ship_decision"] = decision
    SHIP = v3_cfg if decision["ship"] == "v3" else v2_cfg
    OTHER = v2_cfg if decision["ship"] == "v3" else v3_cfg

    # ── Phase 2: report everything relative to SHIP ───────────────────────────
    methods, abl_cfgs = report_configs(SHIP, OTHER)

    # Calibrate any configs not yet in params; reuse existing ones
    for name, cfg in {**methods, **(abl_cfgs if ablations else {})}.items():
        if cfg not in params:
            print("calibrating (phase 2)", name, flush=True)
            params[cfg] = E.calibrate(cfg, full=(cfg == SHIP))
            out["params"][cfg.name] = params[cfg].__dict__

    # Save the WINNER's params immediately — before any long downstream work that could crash
    b1_cfg = dataclasses.replace(SHIP, k=1)
    params[SHIP].save(PARAMS)
    b1_params = params[b1_cfg]
    b1_params.lam = dict(params[SHIP].lam)
    b1_params.save(PARAMS.with_name("params_B1.json"))

    # Run methods on ["T1", *TEST]; reuse phase-1 runs where config matches
    for name, cfg in methods.items():
        if cfg in phase1_runs:
            out["methods"][name] = phase1_runs[cfg]
        else:
            out["methods"][name] = {t: E.run(cfg, params[cfg], t) for t in ["T1", *TEST]}

    # Run ablations on TEST only; reuse phase-1 runs for OTHER
    if ablations:
        for name, cfg in abl_cfgs.items():
            if cfg in phase1_runs:
                out["ablations"][name] = {t: phase1_runs[cfg][t] for t in TEST if t in phase1_runs[cfg]}
            else:
                out["ablations"][name] = {t: E.run(cfg, params[cfg], t) for t in TEST}

    for t in TEST:
        out["sweep"][t] = {n: E.sweep(c, params[c], t) for n, c in
                           [("B1 single reference", b1_cfg), ("B2 envelope", SHIP)]}
    out["equal_fa"] = {t: {n: {str(b): ms_at_fa(pts, b) for b in (0.25, 0.5, 1.0, 2.0)}
                            for n, pts in out["sweep"][t].items()} for t in TEST}
    out["natural_spectrum"] = {}
    for t in TEST:
        sel = E.selection(t)
        sc = E.score_readers(SHIP, params[SHIP], t)
        human = "human" in sel["method"]
        rank = {rid: i for i, rid in enumerate(sel["ranking"])}
        out["natural_spectrum"][t] = {
            "scores": sc, "ranking_method": sel["method"],
            "spearman_vs_ranking": spearman([-rank[i] for i in sc], list(sc.values())) if human else None,
            "status": "ok" if human else "pending human ranking (data/rankings/<T>.csv)",
        }
    out["listening_test"] = summarize_listening()
    out["listening_test"]["severity_vs_listeners_T1"] = E.severity_vs_listeners(SHIP, params[SHIP])
    from .natural import evaluate as natural_eval
    out["natural_flaws"] = natural_eval()
    out["status_note"] = STATUS_NOTE

    out = json.loads(json.dumps(_r(out)))
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
        L += ["\n### Matching Score at equal false-alarm budgets (best sweep point at or below the budget)\n",
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
        t1d = sd["t1"]
        L += ["\n### Ship decision (v3 vs v2, dataset v3)\n"]
        L.append(f"- **Shipped: detector {sd['ship']}**")
        L.append(f"- T1: v3 MS = {_f(t1d['v3_ms'], True)}, v2 MS = {_f(t1d['v2_ms'], True)}, "
                 f"v3 wins T1: {t1d['v3_wins']}")
        L.append(f"- Reason: {sd['reason']}")
        if sd.get("per_text"):
            L += ["\n| Text | v3 MS | v2 MS | v3 FA/min | v2 FA/min | Outcome |",
                  "|---|---|---|---|---|---|"]
            for t, row in sd["per_text"].items():
                fa_viol = t in sd["fa_violations"]
                ms_win = t in sd["wins"]
                if fa_viol and ms_win:
                    outcome = "v3 wins MS, FA cap violated"
                elif fa_viol:
                    outcome = "FA cap violated"
                elif ms_win:
                    outcome = "v3 wins"
                else:
                    outcome = "v2 wins"
                L.append(f"| {t} | {_f(row['v3_ms'], True)} | {_f(row['v2_ms'], True)} | "
                         f"{_f(row['v3_fa'])} | {_f(row['v2_fa'])} | {outcome} |")
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
