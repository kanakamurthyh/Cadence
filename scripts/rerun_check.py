"""Analyze the demo clips twice; fail unless the JSON is byte-identical.

Also compares against results/rerun_hashes.json when present (cross-machine check).
"""
import json
import sys
from pathlib import Path

from cadence.pipeline import analyze

CLIPS = [("data/demo/T2_rushed_and_dropped_pause.wav", "T2"), ("data/demo/T3_monotone.wav", "T3")]
ref_file = Path("results/rerun_hashes.json")
expected = json.loads(ref_file.read_text()) if ref_file.exists() else {}
ok = True
seen = {}
for path, tid in CLIPS:
    runs = [json.dumps(analyze(path, tid)[0], sort_keys=True) for _ in range(2)]
    h = json.loads(runs[0])["hash"]
    same = runs[0] == runs[1]
    print(f"{path}: hash {h}, identical across 2 runs: {same}, matches stored: {expected.get(path) == h}")
    ok &= same and (path not in expected or expected[path] == h)
    seen[path] = h
if "--store" in sys.argv:
    ref_file.write_text(json.dumps(seen, indent=1))
sys.exit(0 if ok else 1)
