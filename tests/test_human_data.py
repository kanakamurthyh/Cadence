import runpy
import sys

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
