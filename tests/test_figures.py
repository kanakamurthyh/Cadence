"""Tests for data-extraction functions in scripts/gradient_figures.py.

Runs on synthetic data only — no file I/O, no matplotlib import.
"""
import sys
from pathlib import Path

# Add scripts/ to path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import gradient_figures as gf  # noqa: E402

# ---------------------------------------------------------------------------
# Synthetic fixtures
# ---------------------------------------------------------------------------

def _make_methods() -> dict:
    """Minimal synthetic results dict with T1 (calibration) and T2/T3 (held-out)."""
    def _text(levels, fa_gp, fa_ne, on_ms, off_ms):
        return {
            "by_level": {str(k): v for k, v in levels.items()},
            "by_type": {"pace": 0.5, "monotone": 0.4},
            "fa_per_min_good_pairs": fa_gp,
            "fa_per_min_null_edit": fa_ne,
            "ladders": {
                "matching_score": 0.4,
                "onset_ms_median": on_ms,
                "offset_ms_median": off_ms,
            },
        }

    return {
        "B0 generic norms": {
            "T1": _text({1: 0.0, 2: 0.1, 3: 0.2, 4: 0.3, 5: 0.4}, 1.0, 1.0, 20, 25),
            "T2": _text({1: 0.0, 2: 0.1, 3: 0.2, 4: 0.3, 5: 0.4}, 1.5, 1.5, 25, 30),
            "T3": _text({1: 0.0, 2: 0.15, 3: 0.25, 4: 0.35, 5: 0.45}, 1.2, 1.2, 22, 28),
        },
        "B1 single reference (K=1)": {
            "T1": _text({1: 0.0, 2: 0.15, 3: 0.3, 4: 0.45, 5: 0.6}, 0.9, 0.9, 20, 25),
            "T2": _text({1: 0.0, 2: 0.15, 3: 0.3, 4: 0.45, 5: 0.6}, 1.1, 1.1, 25, 30),
            "T3": _text({1: 0.0, 2: 0.2, 3: 0.35, 4: 0.5, 5: 0.65}, 1.0, 1.0, 22, 28),
        },
        "B2 envelope (K=all), ours": {
            "T1": _text({1: 0.0, 2: 0.2, 3: 0.4, 4: 0.6, 5: 0.8}, 0.9, 0.9, 20, 25),
            "T2": _text({1: 0.0, 2: 0.2, 3: 0.4, 4: 0.6, 5: 0.8}, 2.0, 2.0, 30, 40),
            "T3": _text({1: 0.0, 2: 0.25, 3: 0.45, 4: 0.65, 5: 0.85}, 1.5, 1.5, 25, 35),
        },
    }


def _make_labels() -> list:
    """Synthetic labels list with flaw data."""
    rows = []
    flaw_types = ["pace", "monotone"]
    for ft in flaw_types:
        for sv in range(1, 6):
            for i in range(4):
                delta = sv * 0.1 * (i + 1)
                rows.append({
                    "flaw_type": ft,
                    "severity_injected": sv,
                    "delta_comparison_domain": delta,
                    "timemap_err_s": 0.001 * (i + 1),
                    "text_id": "T2",
                    "start_s": 1.0,
                    "end_s": 2.0,
                })
    # Add null/clean rows that should be ignored
    rows.append({"flaw_type": "none", "severity_injected": None, "delta_comparison_domain": None,
                 "timemap_err_s": None, "text_id": "T1", "start_s": 0.0, "end_s": 1.0})
    rows.append({"kind": "clean_reference", "text_id": "T1", "start_s": 0.0, "end_s": 1.0})
    return rows


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_extract_gradient_by_severity_excludes_calibration():
    methods = _make_methods()
    result = gf.extract_gradient_by_severity(methods, calibration_text="T1")
    for method_data in result.values():
        assert "T1" not in method_data, "Calibration text T1 must not appear in output"
        assert "T2" in method_data
        assert "T3" in method_data


def test_extract_gradient_by_severity_levels():
    methods = _make_methods()
    result = gf.extract_gradient_by_severity(methods, calibration_text="T1")
    b2 = result["B2 envelope (K=all), ours"]
    assert set(b2["T2"].keys()) == {1, 2, 3, 4, 5}
    # Values should be monotone for this synthetic fixture
    vals = [b2["T2"][s] for s in [1, 2, 3, 4, 5]]
    assert vals == sorted(vals), "Severity scores should be non-decreasing for synthetic fixture"


def test_pool_gradient_structure():
    methods = _make_methods()
    by_severity = gf.extract_gradient_by_severity(methods, calibration_text="T1")
    pooled = gf.pool_gradient(by_severity)
    for method, svs in pooled.items():
        assert set(svs.keys()) == {1, 2, 3, 4, 5}, f"Pooled must have all 5 severity levels for {method}"
        # Pooled mean must be in [0, 1]
        for sv, val in svs.items():
            assert 0.0 <= val <= 1.0, f"Score out of range for {method} sv={sv}: {val}"


def test_extract_fa_rates_keys():
    methods = _make_methods()
    fa = gf.extract_fa_rates(methods, calibration_text="T1")
    for method_fa in fa.values():
        assert "T1" not in method_fa
        for text_id, rates in method_fa.items():
            assert "good_pairs" in rates
            assert "null_edit" in rates


def test_extract_gradient_by_type_monotone():
    labels = _make_labels()
    result = gf.extract_gradient_by_type(labels)
    assert "pace" in result
    assert "monotone" in result
    # Medians should be monotone for synthetic fixture (delta = sv * 0.1 * i)
    for ft in ["pace", "monotone"]:
        medians = [result[ft][sv]["median"] for sv in [1, 2, 3, 4, 5]]
        assert medians == sorted(medians), f"Gradient for {ft} should be non-decreasing"


def test_extract_gradient_by_type_fields():
    labels = _make_labels()
    result = gf.extract_gradient_by_type(labels)
    for ft, svs in result.items():
        for sv, stats in svs.items():
            assert "median" in stats
            assert "q1" in stats
            assert "q3" in stats
            assert "n" in stats
            assert stats["n"] > 0


def test_extract_gradient_by_type_ignores_none():
    labels = _make_labels()
    result = gf.extract_gradient_by_type(labels)
    assert "none" not in result, "flaw_type='none' must be excluded"


def test_timing_errors():
    labels = _make_labels()
    timing = gf.extract_timing_errors(labels)
    assert "timemap_err_ms" in timing
    # Should have values from the synthetic rows that have timemap_err_s
    assert len(timing["timemap_err_ms"]) == 40  # 2 flaw types × 5 severities × 4 rows
    # Check conversion: 0.001 s * 1000 = 1.0 ms
    assert 1.0 in timing["timemap_err_ms"]


def test_gradient_json_structure():
    """Verify that gradient.json-like output has the expected top-level keys."""
    import statistics

    methods = _make_methods()
    labels = _make_labels()
    by_severity = gf.extract_gradient_by_severity(methods, calibration_text="T1")
    fa_rates = gf.extract_fa_rates(methods, calibration_text="T1")
    timing = gf.extract_timing_errors(labels)
    by_type = gf.extract_gradient_by_type(labels)
    pooled = gf.pool_gradient(by_severity)

    gradient_data = {
        "gradient_by_severity": gf._jsonify(by_severity),
        "gradient_pooled": gf._jsonify(pooled),
        "fa_rates": gf._jsonify(fa_rates),
        "timing_error_ms": {
            "values": timing["timemap_err_ms"],
            "n": len(timing["timemap_err_ms"]),
            "median": statistics.median(timing["timemap_err_ms"]) if timing["timemap_err_ms"] else None,
        },
        "gradient_by_type": gf._jsonify(by_type),
    }

    # Check top-level keys
    required_keys = {
        "gradient_by_severity",
        "gradient_pooled",
        "fa_rates",
        "timing_error_ms",
        "gradient_by_type",
    }
    assert required_keys == set(gradient_data.keys())

    # gradient_by_severity: method -> text -> severity -> score
    for method, texts in gradient_data["gradient_by_severity"].items():
        for text_id, svs in texts.items():
            for sv_str, score in svs.items():
                assert isinstance(score, float)

    # timing_error_ms: has n and median
    te = gradient_data["timing_error_ms"]
    assert te["n"] > 0
    assert te["median"] > 0
