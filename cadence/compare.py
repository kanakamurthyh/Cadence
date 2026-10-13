"""Before/after comparison of two benchmark runs (e.g. before and after human data)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
B2 = "B2 envelope (K=all), ours"
B1 = "B1 single reference (K=1)"


def _pct(v):
    return "n/a" if v is None else f"{100 * v:.0f}%"


def _num(v):
    return "n/a" if v is None else f"{v:.2f}"


def rows(o: dict) -> dict:
    out = {}
    for t in [t for t in o["methods"][B2] if t != "T1"]:
        for name, key in ((B2, "B2"), (B1, "B1"), ("B0 generic norms", "B0")):
            r = o["methods"][name][t]
            out[f"{key} Matching Score {t}"] = (r["ladders"]["matching_score"], _pct)
            out[f"{key} pace {t}"] = (r["by_type"]["pace"], _pct)
            out[f"{key} monotone {t}"] = (r["by_type"]["monotone"], _pct)
            out[f"{key} FA/min good pairs {t}"] = (r["fa_per_min_good_pairs"], _num)
            out[f"{key} severity rho (vs injected) {t}"] = (r["severity_spearman"], _num)
    sv = o.get("listening_test", {}).get("severity_vs_listeners_T1", {})
    out["Severity rho vs listeners (T1)"] = (sv.get("spearman_system_vs_perceived"), _num)
    out["Severity scale"] = (o["params"]["K=all"].get("sev_scale"), str)
    out["Good set method T2"] = (o["natural_spectrum"]["T2"]["ranking_method"], str)
    for t in o["natural_spectrum"]:
        out[f"Natural spectrum Spearman {t}"] = (o["natural_spectrum"][t]["spearman_vs_ranking"], _num)
    nf = o.get("natural_flaws", {})
    for a, r in nf.get("system_vs_annotator", {}).items():
        out[f"Natural: Cadence vs {a} MS"] = (r["matching_score"], _pct)
    for pair, r in nf.get("annotator_vs_annotator", {}).items():
        out[f"Natural ceiling {pair} MS"] = (r["matching_score"], _pct)
    return out


def main(baseline: str) -> str:
    old = json.loads((ROOT / baseline / "results.json").read_text())
    new = json.loads((ROOT / "results" / "results.json").read_text())
    a, b = rows(old), rows(new)
    lines = [f"| Metric | Baseline ({baseline}) | Current |", "|---|---|---|"]
    for k in dict.fromkeys([*a, *b]):
        fa = a.get(k, (None, str))[1]
        fb = b.get(k, (None, str))[1]
        lines.append(f"| {k} | {fa(a[k][0]) if k in a else 'n/a'} | {fb(b[k][0]) if k in b else 'n/a'} |")
    md = "\n".join(lines) + "\n"
    (ROOT / "results" / "comparison.md").write_text(md)
    print(md)
    return md
