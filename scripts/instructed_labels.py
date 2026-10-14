"""Labels for *instructed* takes: the reader was told, before recording, which words to deliver with which flaw.

The plan (data/takes/instructed_plan.json) fixes each take's flaw word spans in advance. This script aligns each
take and writes the spans in take-file seconds to data/annotations/instructed/<take_id>.txt (Audacity label format),
so `cadence natural` can score Cadence against them. Caveats, to be disclosed with any result:
  - the labels are the instructions, not a listener's judgement (the reader may not have produced the flaw well);
  - label times come from the same forced aligner Cadence uses;
  - one reader, one "annotator": there is no annotator-vs-annotator ceiling.

Usage: uv run python scripts/instructed_labels.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
PLAN = ROOT / "data" / "takes" / "instructed_plan.json"
OUT = ROOT / "data" / "annotations" / "instructed"


def label_lines(words: list[dict], offset: float, flaws: list[dict]) -> list[str]:
    """Audacity label lines for word-index spans. A missing pause spans the two words around the boundary."""
    out = []
    for f in flaws:
        w0, w1 = f["w0"], (f["w0"] + 1 if f["type"] == "missing_pause" else f["w1"])
        out.append(f"{words[w0]['start'] + offset:.3f}\t{words[w1]['end'] + offset:.3f}\t{f['type']}")
    return out


def main() -> None:
    from cadence.natural import TAKES
    from cadence.pipeline import analyze
    plan = json.loads(PLAN.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    for take_id, p in plan["takes"].items():
        tid = p["text_id"]
        audio = [f for f in (TAKES / tid).glob(f"{take_id}.*") if f.suffix != ".txt"]
        if not audio:
            print(f"skip {take_id}: no recording in data/takes/{tid}/")
            continue
        rep, rec = analyze(audio[0], tid)
        lines = label_lines(rep["words"], rec["offset"], p["flaws"])
        (OUT / f"{take_id}.txt").write_text("".join(line + "\n" for line in lines))
        print(f"{take_id}: {len(lines)} label(s)", *lines, sep="\n  ")


if __name__ == "__main__":
    main()
