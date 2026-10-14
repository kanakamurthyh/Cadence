"""Download every source recording into data/raw/<text>/ and write sources.json.

LibriVox multi-reader projects, direct public-domain sources (with licence and
provenance, sha1-checked when given), and reuse of another text's downloads.
Files already present are kept. Never downloads anything without a licence entry.
"""
import argparse
import hashlib
import json
from pathlib import Path

from cadence.data.librivox import _download, fetch
from cadence.data.texts import TEXTS

LV_LICENCE = "Public domain (LibriVox; Public Domain Mark 1.0)"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch source recordings for Cadence texts.")
    parser.add_argument(
        "--texts", nargs="*", metavar="TID",
        help="Text IDs to process (e.g. T7 T8). Default: all texts.",
    )
    args = parser.parse_args()
    selected = set(args.texts) if args.texts else None

    for tid, t in TEXTS.items():
        if selected is not None and tid not in selected:
            continue
        out = Path("data/raw") / tid
        out.mkdir(parents=True, exist_ok=True)
        rows = []
        if t.get("reuse_raw"):
            rows += json.loads((Path("data/raw") / t["reuse_raw"] / "sources.json").read_text())
        if t["librivox_ids"]:
            rows += fetch(t["librivox_ids"], out)
        for r in rows:
            r.setdefault("licence", LV_LICENCE)
            r.setdefault("provenance", f"LibriVox project {r.get('book_id')}, section {r.get('section')}")
        for s in t.get("sources", []):
            path = out / (s["id"] + Path(s["url"].split("?")[0]).suffix)
            if not path.exists() and not _download(s["url"], path):
                print("skipped (download failed):", s["url"])
                continue
            sha1 = hashlib.sha1(path.read_bytes()).hexdigest()
            if s.get("sha1") and sha1 != s["sha1"]:
                raise SystemExit(f"{path}: sha1 {sha1} does not match the documented source {s['sha1']}")
            rows.append({"id": s["id"], "mp3": str(path), "reader": s["speaker"], "url": s["url"],
                         "page": s["page"], "licence": s["licence"], "provenance": s["provenance"],
                         "sha1": sha1, "book_id": 0, "section": 0, **s.get("meta", {})})
        # consented teammate takes dropped into data/raw/<T>/ as team_<name>_take<n>.<ext>
        for p in sorted(out.glob("team_*")):
            if p.suffix.lower() in {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}:
                rows.append({"id": p.stem, "mp3": str(p), "reader": p.stem.split("_")[1], "url": "",
                             "licence": "Team recording, consent on file (data/consent/)",
                             "provenance": "recorded by the Cadence team", "book_id": 0, "section": 0})
        (out / "sources.json").write_text(json.dumps(rows, indent=1))
        print(tid, len(rows), "recordings")
