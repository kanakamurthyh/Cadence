"""Fetch every reader's recording of a LibriVox multi-version project."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import requests

API = "https://librivox.org/api/feed/audiobooks/?id={id}&format=json&extended=1"


def list_sections(book_id: int) -> list[dict]:
    book = requests.get(API.format(id=book_id), timeout=60).json()["books"][0]
    out = []
    for s in book["sections"]:
        reader = s["readers"][0]["display_name"] if s["readers"] else "unknown"
        out.append({
            "book_id": book_id,
            "book_title": book["title"],
            "section": int(s["section_number"]),
            "reader": reader,
            "url": s["listen_url"],
            "playtime_s": int(s["playtime"] or 0),
        })
    return out


def reader_id(sec: dict) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", sec["reader"].lower()).strip("_")[:24]
    return f"lv{sec['book_id']}_{sec['section']:02d}_{slug}"


def _download(url: str, path: Path, tries: int = 4) -> bool:
    for i in range(tries):
        try:
            r = requests.get(url, timeout=120)
            r.raise_for_status()
            path.write_bytes(r.content)
            return True
        except requests.RequestException:
            time.sleep(3 * (i + 1))
    return False


def fetch(book_ids: list[int], out_dir: Path) -> list[dict]:
    """Download mp3s into out_dir (cached); return manifest rows."""
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for bid in book_ids:
        for sec in list_sections(bid):
            rid = reader_id(sec)
            path = out_dir / f"{rid}.mp3"
            if not path.exists() and not _download(sec["url"], path):
                print("skipped (download failed):", sec["url"])
                continue
            rows.append({**sec, "id": rid, "mp3": str(path)})
    (out_dir / "sources.json").write_text(json.dumps(rows, indent=1))
    return rows
