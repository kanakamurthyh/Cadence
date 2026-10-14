"""Severity-gradient evidence figures for the Cadence Track C report.

Run: uv run --extra report python scripts/gradient_figures.py

Outputs
-------
docs/figures/gradient_matching_by_severity.png
docs/figures/gradient_by_type.png
docs/figures/false_alarms_null_edit.png
docs/figures/label_timing_error.png
results/gradient.json
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

# ---------------------------------------------------------------------------
# Palette (from dataviz skill reference palette, 3 categorical slots validated)
# B0=blue, B1=orange, B2=aqua;  all-pairs validated in both modes
# WARN on aqua contrast: relief provided by direct endpoint labels
# ---------------------------------------------------------------------------
_LIGHT_SURFACE = "#fcfcfb"
_SERIES_COLORS = {
    "B0 generic norms":         "#2a78d6",   # slot 1 blue
    "B1 single reference (K=1)": "#eb6834",  # slot 2 orange
    "B2 envelope (K=all), ours": "#1baf7a",  # slot 3 aqua
}
# Short display labels, stable
_METHOD_DISPLAY = {
    "B0 generic norms":         "B0",
    "B1 single reference (K=1)": "B1",
    "B2 envelope (K=all), ours": "B2 (ours)",
}
# Fixed display order
_METHOD_ORDER = [
    "B0 generic norms",
    "B1 single reference (K=1)",
    "B2 envelope (K=all), ours",
]

_CALIBRATION_TEXT = "T1"

# ---------------------------------------------------------------------------
# Data extraction (pure; tested independently)
# ---------------------------------------------------------------------------

def extract_gradient_by_severity(
    methods: dict,
    calibration_text: str = _CALIBRATION_TEXT,
) -> dict:
    """Return per-method, per-text, per-severity matching scores.

    Returns
    -------
    {method: {text: {severity_int: score_float}}}
    """
    out: dict = {}
    for method, texts in methods.items():
        out[method] = {}
        for text_id, data in texts.items():
            if text_id == calibration_text:
                continue
            bl = data.get("by_level", {})
            out[method][text_id] = {int(k): float(v) for k, v in bl.items()}
    return out


def extract_fa_rates(
    methods: dict,
    calibration_text: str = _CALIBRATION_TEXT,
) -> dict:
    """Return FA/min for good_pairs and null_edit per method per text.

    Returns
    -------
    {method: {text: {good_pairs: float, null_edit: float}}}
    """
    out: dict = {}
    for method, texts in methods.items():
        out[method] = {}
        for text_id, data in texts.items():
            if text_id == calibration_text:
                continue
            out[method][text_id] = {
                "good_pairs": data.get("fa_per_min_good_pairs"),
                "null_edit": data.get("fa_per_min_null_edit"),
            }
    return out


def extract_timing_errors(labels: list[dict]) -> dict:
    """Return timemap_err_s values (in ms) from every synthetic clip that has one.

    Parameters
    ----------
    labels : parsed labels.jsonl rows (list of dicts)

    Returns
    -------
    {"timemap_err_ms": [float, ...]}
        timemap_err_ms: per-clip timing-map error converted to milliseconds,
        for every row where timemap_err_s is not None.
    """
    errs_ms = [
        float(row["timemap_err_s"]) * 1000.0
        for row in labels
        if row.get("timemap_err_s") is not None
    ]
    return {"timemap_err_ms": errs_ms}


def extract_gradient_by_type(labels: list[dict]) -> dict:
    """Compute |delta_comparison_domain| grouped by flaw_type × severity_injected.

    Returned structure
    ------------------
    {flaw_type: {severity_int: {median: float, q1: float, q3: float, n: int}}}
    """
    from collections import defaultdict

    store: dict = defaultdict(lambda: defaultdict(list))
    for row in labels:
        ft = row.get("flaw_type")
        sv = row.get("severity_injected")
        delta = row.get("delta_comparison_domain")
        if ft and ft != "none" and sv is not None and delta is not None:
            store[ft][int(sv)].append(abs(float(delta)))

    out: dict = {}
    for ft, svs in store.items():
        out[ft] = {}
        for sv, vals in sorted(svs.items()):
            sorted_vals = sorted(vals)
            n = len(sorted_vals)
            med = statistics.median(sorted_vals)
            q1 = sorted_vals[n // 4]
            q3 = sorted_vals[(3 * n) // 4]
            out[ft][sv] = {"median": med, "q1": q1, "q3": q3, "n": n}
    return out


def pool_gradient(by_severity: dict) -> dict:
    """Pool per-text scores across held-out texts, return {severity: mean}.

    Parameters
    ----------
    by_severity : {method: {text: {severity: score}}}
    """
    out: dict = {}
    for method, texts in by_severity.items():
        pooled: dict = {}
        for text_id, svs in texts.items():
            for sv, score in svs.items():
                pooled.setdefault(sv, []).append(score)
        out[method] = {sv: statistics.mean(scores) for sv, scores in sorted(pooled.items())}
    return out


# ---------------------------------------------------------------------------
# Plotting helpers
# ---------------------------------------------------------------------------

def _apply_style(fig, axes_list=None) -> None:
    """Apply consistent minimal style to all axes in fig."""
    import matplotlib as mpl

    mpl.rcParams.update({
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#c3c2b7",
        "axes.linewidth": 1.0,
        "xtick.color": "#898781",
        "ytick.color": "#898781",
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "axes.labelsize": 9,
        "axes.titlesize": 10,
        "axes.titleweight": "bold",
        "axes.facecolor": _LIGHT_SURFACE,
        "figure.facecolor": _LIGHT_SURFACE,
        "axes.grid": True,
        "grid.color": "#e1e0d9",
        "grid.linewidth": 1.0,
        "grid.linestyle": "-",
        "axes.axisbelow": True,
        "font.family": ["DejaVu Sans", "sans-serif"],
        "font.size": 9,
        "legend.fontsize": 8,
        "legend.frameon": False,
    })


def _save(fig, path: Path) -> None:
    """Save figure deterministically (no timestamps in metadata)."""
    fig.savefig(
        path,
        dpi=150,
        bbox_inches="tight",
        facecolor=_LIGHT_SURFACE,
        metadata={"Software": None},
    )


# ---------------------------------------------------------------------------
# Figure A: Matching score vs severity, one line per method
# ---------------------------------------------------------------------------

def fig_gradient_matching(by_severity: dict, out_path: Path) -> None:
    """Figure a: gradient_matching_by_severity.png"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    _apply_style(None)

    # Discover held-out text IDs from data (union across methods, sorted)
    held_out_texts = sorted(
        {t for texts in by_severity.values() for t in texts}
    )
    text_list = ", ".join(held_out_texts)

    fig, ax = plt.subplots(figsize=(5.5, 3.5))
    ax.set_facecolor(_LIGHT_SURFACE)
    ax.set_xlabel("Injected severity", labelpad=6)
    ax.set_ylabel("Matching score", labelpad=6)
    ax.set_title(
        f"Matching score vs injected severity\n"
        f"(held-out texts {text_list}, pooled)"
    )
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.set_ylim(-0.02, 1.05)

    pooled = pool_gradient(by_severity)
    severities = [1, 2, 3, 4, 5]

    for method in _METHOD_ORDER:
        if method not in by_severity:
            continue
        texts_data = by_severity[method]
        color = _SERIES_COLORS[method]
        label = _METHOD_DISPLAY[method]

        # Faint per-text lines
        for text_id, svs in texts_data.items():
            xs = sorted(svs.keys())
            ys = [svs[x] for x in xs]
            ax.plot(xs, ys, color=color, alpha=0.15, linewidth=1.0, zorder=1)

        # Pooled mean line (no legend= parameter — legend is suppressed)
        mean_ys = [pooled[method].get(sv, float("nan")) for sv in severities]
        ax.plot(
            severities, mean_ys,
            color=color,
            linewidth=2.0,
            solid_capstyle="round",
            solid_joinstyle="round",
            zorder=3,
        )
        # End-point marker (>=8px = r>=4)
        ax.scatter(
            [severities[-1]], [mean_ys[-1]],
            color=color, s=60, zorder=5,
            edgecolors=_LIGHT_SURFACE, linewidths=2,
        )
        # Direct label at last point (relief for aqua sub-3:1 slot; legend dropped)
        ax.annotate(
            label,
            xy=(severities[-1], mean_ys[-1]),
            xytext=(5, 0), textcoords="offset points",
            fontsize=7.5, color="#52514e", va="center",
        )

    ax.set_xlim(0.8, 6.2)

    ax.spines["left"].set_color("#c3c2b7")
    ax.spines["bottom"].set_color("#c3c2b7")
    ax.tick_params(colors="#898781")

    fig.tight_layout()
    _save(fig, out_path)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure B: Gradient by flaw type (small multiples from labels.jsonl)
# ---------------------------------------------------------------------------

def fig_gradient_by_type(by_type: dict, out_path: Path) -> None:
    """Figure b: gradient_by_type.png — |delta| vs severity per flaw type."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    _apply_style(None)

    flaw_types = sorted(by_type.keys())
    n_types = len(flaw_types)
    ncols = 3
    nrows = (n_types + ncols - 1) // ncols

    fig, axes = plt.subplots(
        nrows, ncols, figsize=(7.5, 2.8 * nrows),
        sharey=False,
    )
    axes_flat = axes.flatten() if n_types > 1 else [axes]

    color = _SERIES_COLORS["B2 envelope (K=all), ours"]  # slot 3 aqua
    severities = [1, 2, 3, 4, 5]

    for i, ft in enumerate(flaw_types):
        ax = axes_flat[i]
        ax.set_facecolor(_LIGHT_SURFACE)
        svs_data = by_type[ft]
        medians = [svs_data.get(sv, {}).get("median", float("nan")) for sv in severities]
        q1s = [svs_data.get(sv, {}).get("q1", float("nan")) for sv in severities]
        q3s = [svs_data.get(sv, {}).get("q3", float("nan")) for sv in severities]

        ax.fill_between(
            severities, q1s, q3s,
            color=color, alpha=0.15, zorder=1,
        )
        ax.plot(
            severities, medians,
            color=color, linewidth=2.0,
            solid_capstyle="round", solid_joinstyle="round",
            zorder=3,
        )
        ax.scatter(
            severities, medians,
            color=color, s=40, zorder=5,
            edgecolors=_LIGHT_SURFACE, linewidths=1.5,
        )
        ax.set_title(ft.replace("_", " ").title(), fontsize=9, fontweight="bold")
        ax.set_xticks([1, 2, 3, 4, 5])
        ax.set_xlabel("Severity", fontsize=8, labelpad=4)
        ax.set_ylabel("|Δ| (comparison units)", fontsize=7.5, labelpad=4)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#c3c2b7")
        ax.spines["bottom"].set_color("#c3c2b7")
        ax.tick_params(colors="#898781", labelsize=7.5)
        ax.grid(True, color="#e1e0d9", linewidth=1.0)
        ax.set_axisbelow(True)

    # Hide unused panels
    for j in range(n_types, len(axes_flat)):
        axes_flat[j].set_visible(False)

    fig.suptitle(
        "Injected effect magnitude vs severity, by flaw type\n"
        "(median ± IQR, all texts)",
        fontsize=10, fontweight="bold", y=1.01,
    )
    fig.tight_layout()
    _save(fig, out_path)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure C: False alarms — grouped bars B1 vs B2
# ---------------------------------------------------------------------------

def fig_false_alarms(fa_rates: dict, out_path: Path) -> None:
    """Figure c: false_alarms_null_edit.png — FA/min grouped bars B1 vs B2."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    _apply_style(None)

    b1_key = "B1 single reference (K=1)"
    b2_key = "B2 envelope (K=all), ours"

    # Collect held-out texts in order
    texts = sorted(
        set(fa_rates.get(b1_key, {}).keys()) | set(fa_rates.get(b2_key, {}).keys())
    )
    n_texts = len(texts)
    conditions = ["good_pairs", "null_edit"]
    condition_labels = ["Good pairs", "Null edit"]

    b1_color = _SERIES_COLORS[b1_key]
    b2_color = _SERIES_COLORS[b2_key]

    # Layout: 2 condition subplots side by side
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.2), sharey=True)

    bar_width = 0.35
    x = np.arange(n_texts)

    for ci, (cond, cond_label) in enumerate(zip(conditions, condition_labels)):
        ax = axes[ci]
        ax.set_facecolor(_LIGHT_SURFACE)

        b1_vals = [fa_rates.get(b1_key, {}).get(t, {}).get(cond) for t in texts]
        b2_vals = [fa_rates.get(b2_key, {}).get(t, {}).get(cond) for t in texts]

        # Replace None with 0 for plotting
        b1_vals = [v if v is not None else 0.0 for v in b1_vals]
        b2_vals = [v if v is not None else 0.0 for v in b2_vals]

        bars1 = ax.bar(
            x - bar_width / 2, b1_vals, bar_width,
            color=b1_color, label="B1",
            # 2px surface gap between adjacent bars is handled by the bar_width + offset
        )
        bars2 = ax.bar(
            x + bar_width / 2, b2_vals, bar_width,
            color=b2_color, label="B2 (ours)",
        )

        # Value labels on bars (relief for aqua / legibility)
        for bar, val in zip(bars2, b2_vals):
            ax.text(
                bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                f"{val:.1f}",
                ha="center", va="bottom", fontsize=7, color="#52514e",
            )
        for bar, val in zip(bars1, b1_vals):
            ax.text(
                bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                f"{val:.1f}",
                ha="center", va="bottom", fontsize=7, color="#52514e",
            )

        ax.set_xticks(x)
        ax.set_xticklabels(texts, fontsize=8.5)
        ax.set_xlabel("Text", labelpad=5)
        ax.set_title(cond_label, fontsize=10, fontweight="bold")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#c3c2b7")
        ax.spines["bottom"].set_color("#c3c2b7")
        ax.tick_params(colors="#898781")
        ax.grid(True, axis="y", color="#e1e0d9", linewidth=1.0)
        ax.set_axisbelow(True)
        ax.legend(loc="upper right", fontsize=8)

    axes[0].set_ylabel("False alarms per minute", labelpad=6)
    fig.suptitle(
        "False-alarm rate — B1 vs B2 (held-out texts)",
        fontsize=10, fontweight="bold",
    )
    fig.tight_layout()
    _save(fig, out_path)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure D: Label timing error histogram
# ---------------------------------------------------------------------------

def fig_label_timing(
    timing: dict,
    results_methods: dict,
    out_path: Path,
    calibration_text: str = _CALIBRATION_TEXT,
) -> None:
    """Figure d: label_timing_error.png — histogram of timemap_err_s in ms."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    _apply_style(None)

    errs_ms = timing["timemap_err_ms"]
    if not errs_ms:
        return

    fig, ax = plt.subplots(figsize=(5.5, 3.5))
    ax.set_facecolor(_LIGHT_SURFACE)

    # Histogram
    counts, edges, _ = ax.hist(
        errs_ms, bins=30,
        color=_SERIES_COLORS["B2 envelope (K=all), ours"],
        alpha=0.85, edgecolor=_LIGHT_SURFACE, linewidth=1.5,
    )

    # Overlay median onset/offset error as reference lines (B2, held-out texts)
    b2_key = "B2 envelope (K=all), ours"
    onset_vals = []
    offset_vals = []
    for text_id, data in results_methods.get(b2_key, {}).items():
        if text_id == calibration_text:
            continue
        lad = data.get("ladders", {})
        if lad.get("onset_ms_median") is not None:
            onset_vals.append(float(lad["onset_ms_median"]))
        if lad.get("offset_ms_median") is not None:
            offset_vals.append(float(lad["offset_ms_median"]))

    ymax = max(counts) * 1.15
    ax.set_ylim(0, ymax)

    line_colors = {"onset": "#2a78d6", "offset": "#eb6834"}

    if onset_vals:
        med_onset = statistics.median(onset_vals)
        ax.axvline(
            med_onset, color=line_colors["onset"], linewidth=1.5,
            linestyle="--", label=f"Median onset error {med_onset:.0f} ms",
        )
    if offset_vals:
        med_offset = statistics.median(offset_vals)
        ax.axvline(
            med_offset, color=line_colors["offset"], linewidth=1.5,
            linestyle="--", label=f"Median offset error {med_offset:.0f} ms",
        )

    ax.set_xlabel("Timing error (ms)", labelpad=6)
    ax.set_ylabel("Clips", labelpad=6)
    ax.set_title("Label timing error (timemap)\nwith B2 detection onset/offset medians")
    ax.legend(fontsize=7.5)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#c3c2b7")
    ax.spines["bottom"].set_color("#c3c2b7")
    ax.tick_params(colors="#898781")
    ax.grid(True, axis="y", color="#e1e0d9", linewidth=1.0)
    ax.set_axisbelow(True)

    fig.tight_layout()
    _save(fig, out_path)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def _jsonify(obj):
    """Recursively convert non-serializable types for JSON."""
    if isinstance(obj, dict):
        return {str(k): _jsonify(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonify(v) for v in obj]
    if isinstance(obj, float):
        return obj
    if isinstance(obj, int):
        return obj
    return obj


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    import matplotlib
    matplotlib.use("Agg")

    repo_root = Path(__file__).parent.parent
    figures_dir = repo_root / "docs" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    results_path = repo_root / "results" / "results.json"
    labels_path = repo_root / "data" / "labels" / "labels.jsonl"

    with results_path.open() as f:
        results = json.load(f)
    methods = results["methods"]

    labels: list[dict] = []
    with labels_path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                labels.append(json.loads(line))

    # Extract data
    by_severity = extract_gradient_by_severity(methods)
    fa_rates = extract_fa_rates(methods)
    timing = extract_timing_errors(labels)
    by_type = extract_gradient_by_type(labels)

    # Build gradient.json
    gradient_data = {
        "gradient_by_severity": _jsonify(by_severity),
        "gradient_pooled": _jsonify(pool_gradient(by_severity)),
        "fa_rates": _jsonify(fa_rates),
        "timing_error_ms": {
            "values": timing["timemap_err_ms"],
            "n": len(timing["timemap_err_ms"]),
            "median": statistics.median(timing["timemap_err_ms"]) if timing["timemap_err_ms"] else None,
        },
        "gradient_by_type": _jsonify(by_type),
    }

    out_json = repo_root / "results" / "gradient.json"
    with out_json.open("w") as f:
        json.dump(gradient_data, f, indent=2, sort_keys=True)
    print(f"Wrote {out_json}")

    # Figures
    fig_gradient_matching(
        by_severity,
        figures_dir / "gradient_matching_by_severity.png",
    )
    print("Wrote gradient_matching_by_severity.png")

    fig_gradient_by_type(
        by_type,
        figures_dir / "gradient_by_type.png",
    )
    print("Wrote gradient_by_type.png")

    fig_false_alarms(
        fa_rates,
        figures_dir / "false_alarms_null_edit.png",
    )
    print("Wrote false_alarms_null_edit.png")

    fig_label_timing(
        timing,
        methods,
        figures_dir / "label_timing_error.png",
    )
    print("Wrote label_timing_error.png")


if __name__ == "__main__":
    main()
