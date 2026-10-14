"""Tests for cadence.benchmark — supplementary to test_core.py."""
from __future__ import annotations


def test_robustness_wrong_word_coverage():
    """Every test text (except T5) has a WRONG_WORD entry with a word present in the text."""
    import importlib.util
    from pathlib import Path
    from cadence.data.texts import TEXTS

    # Load robustness.py dynamically to access WRONG_WORD
    robustness_path = Path(__file__).parent.parent / "scripts" / "robustness.py"
    spec = importlib.util.spec_from_file_location("robustness", robustness_path)
    robustness = importlib.util.module_from_spec(spec)
    # Don't execute the module body (there's an if __name__ guard)
    spec.loader.exec_module(robustness)

    # Find all test texts (except T5)
    test_texts = {tid: v for tid, v in TEXTS.items()
                  if (v["role"].startswith("test") or v["role"] == "calibration") and tid != "T5"}

    wrong_word = robustness.WRONG_WORD

    for tid in test_texts:
        assert tid in wrong_word, f"Text {tid} must have a WRONG_WORD entry"
        word, _substitute = wrong_word[tid]
        text = TEXTS[tid]["text"]
        assert word in text, f"WRONG_WORD[{tid}][0] = {word!r} not found in text {tid}"


def _run(ms, fa) -> dict:
    """Minimal E.run()-shaped result for ship_decision tests."""
    return {"ladders": {"matching_score": ms}, "fa_per_min_good_pairs": fa}


def test_ship_decision_none_values():
    """None (not NaN) for v3 MS counts as loss; None for v3 FA (where v2 is ok) counts as violation."""
    from cadence.benchmark import ship_decision

    # T2: v3 MS = None → loss; v3 FA = None, v2 FA = 0.9 <= 2.0 → FA violation
    # T3: normal v3 win with no FA issue
    v3 = {"T1": _run(0.60, 0.5), "T2": _run(None, None), "T3": _run(0.50, 1.0)}
    v2 = {"T1": _run(0.50, 0.4), "T2": _run(0.45, 0.9), "T3": _run(0.40, 1.1)}

    d = ship_decision(v3, v2)
    assert d["ship"] == "v2"
    assert "T2" in d["losses"], "None MS must count as a loss"
    assert "T2" in d["fa_violations"], "None FA (with v2 FA ok) must count as a violation"
    assert d["wins"] == ["T3"]
    # T1 is fine — v3 wins it
    assert d["t1"]["v3_wins"] is True


def test_markdown_fa_win_both():
    """A text where v3 wins MS but also violates FA cap shows 'v3 wins MS, FA cap violated'."""
    from cadence.benchmark import markdown

    sd = {
        "ship": "v2",
        "t1": {"v3_ms": 0.6, "v2_ms": 0.5, "v3_wins": True},
        "wins": ["T2"],
        "losses": [],
        "fa_violations": ["T2"],
        "per_text": {"T2": {"v3_ms": 0.55, "v2_ms": 0.45, "v3_fa": 2.5, "v2_fa": 1.5}},
        "reason": "FA cap exceeded on ['T2']",
    }
    # Build a minimal out dict that markdown() can render without crashing.
    # We only care about the ship_decision section here.
    stub_r = {
        "ladders": {"matching_score": 0.3, "time_f1": 0.4,
                    "onset_ms_median": 50.0, "offset_ms_median": 60.0},
        "fa_per_min_good_pairs": 1.0,
        "fa_per_min_null_edit": 0.5,
        "fa_per_min_ladder_edit_attributable": 0.2,
        "severity_spearman": 0.5,
        "by_type": {"pace": 0.3, "monotone": 0.2},
        "by_level": {"1": 0.1, "2": 0.2, "3": 0.3, "4": 0.4, "5": 0.5},
        "compound": None,
        "per_type": {},
    }
    o = {
        "status_note": "",
        "methods": {"B2 envelope (K=all), ours": {"T1": stub_r, "T2": stub_r}},
        "ablations": {},
        "equal_fa": {},
        "natural_spectrum": {},
        "listening_test": {},
        "natural_flaws": {},
        "ship_decision": sd,
    }
    md = markdown(o)
    assert "v3 wins MS, FA cap violated" in md, (
        "A text winning on MS but violating FA cap must show 'v3 wins MS, FA cap violated'"
    )
    # Must NOT show a bare "v3 wins" row for T2
    for line in md.splitlines():
        if "| T2 |" in line and "v3 wins MS, FA cap violated" not in line:
            assert "v3 wins" not in line, f"Bare 'v3 wins' found in T2 row: {line!r}"
