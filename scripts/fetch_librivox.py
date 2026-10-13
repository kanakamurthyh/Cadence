"""Download all LibriVox readings for T1-T3 into data/raw/<text>/."""
from pathlib import Path

from cadence.data.librivox import fetch
from cadence.data.texts import TEXTS

if __name__ == "__main__":
    for tid, t in TEXTS.items():
        rows = fetch(t["librivox_ids"], Path("data/raw") / tid)
        print(tid, len(rows), "recordings")
