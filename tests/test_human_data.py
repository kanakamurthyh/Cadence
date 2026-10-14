import runpy
import sys
from pathlib import Path

import pytest

from cadence.natural import read_labels


def test_audacity_labels(tmp_path):
    f = tmp_path / "x.txt"
    f.write_text("1.0\t2.5\tmissing pause\n\\\t300\t4000\n3\t4\tpace\n")
    labs = read_labels(f)
    assert [l["type"] for l in labs] == ["missing_pause", "pace"] and labs[0]["end"] == 2.5


@pytest.mark.parametrize("line", ["1\t2\tmumbling\n", "2\t1\tpace\n", "1\t2\n"])
def test_bad_labels_rejected(tmp_path, line):
    f = tmp_path / "x.txt"
    f.write_text(line)
    with pytest.raises(ValueError):
        read_labels(f)


def test_ladder_cache_guard():
    sys.argv = ["x"]
    same = runpy.run_path("scripts/build_ladders.py", run_name="lib")["_same_plan"]
    c = {"source": "a", "flaws": [["monotone", 3, 10, 14]]}
    assert same({"source": "a", "flaws": [["monotone", 3, 10, 14]]}, c)
    assert not same({"source": "b", "flaws": [["monotone", 3, 10, 14]]}, c)  # new good set
    assert not same({"source": "a", "flaws": [["monotone", 3, 11, 15]]}, c)  # new span
    assert same({"source": "a", "labels": [{"w0": 10, "severity": 3}]}, c)  # legacy cache


def test_expected_length_change_models_crossfades():
    from cadence.labels import _expected_delta
    words = [{"start": 0.0, "end": 1.0}, {"start": 1.5, "end": 2.0}, {"start": 2.0, "end": 3.0}]
    assert _expected_delta(["misplaced_pause", 5, 0, 0], words) == pytest.approx(2.0 - 0.02)
    assert _expected_delta(["missing_pause", 5, 0, 1], words) == pytest.approx(-(0.5 - 0.01) - 0.01)
    assert _expected_delta(["pace_rushed", 5, 1, 2], words) == pytest.approx((0.55 - 1) * 1.5)
    assert _expected_delta(["monotone", 5, 0, 2], words) == 0.0


def test_instructed_labels_spans_words_and_pause_boundary():
    import importlib.util
    spec = importlib.util.spec_from_file_location("il", Path(__file__).resolve().parent.parent / "scripts" / "instructed_labels.py")
    il = importlib.util.module_from_spec(spec); spec.loader.exec_module(il)
    words = [{"start": i * 1.0, "end": i * 1.0 + 0.5} for i in range(10)]
    lines = il.label_lines(words, 2.0, [{"type": "pace", "w0": 2, "w1": 4}, {"type": "missing_pause", "w0": 6, "w1": 6}])
    assert lines == ["4.000\t6.500\tpace", "8.000\t9.500\tmissing_pause"]
