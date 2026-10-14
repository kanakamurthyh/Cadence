"""Robustness (spec section 8): a text's ladders at severities 3 and 5 under
background noise (20 and 10 dB SNR), 64 kbps MP3, a simulated telephone channel
(300-3400 Hz band, 8 kHz; a proxy for a microphone change, not a real re-recording),
and one wrong transcript word. A real phone re-recording needs a person.

usage: robustness.py [--text T2] [--conds clean noise_20 ...]
Writes results/robustness_<T>.json (T2 also to robustness.json) and appends to results.md.
"""
import argparse
import json
import os
import subprocess
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

os.environ.setdefault("OMP_NUM_THREADS", "2")

from cadence import audio  # noqa: E402
from cadence.data.texts import TEXTS  # noqa: E402
from cadence.detect import detect  # noqa: E402
from cadence.evaluate import envelope_for, manifest  # noqa: E402
from cadence.metrics import aggregate, score_clip  # noqa: E402
from cadence.pipeline import ROOT, load_params, measure  # noqa: E402

WRONG_WORD = {"T2": ("queer", "strange"), "T3": ("hallow", "hollow"), "T4": ("Liberty", "freedom"),
              "T1": ("whetted", "sharpened"), "T6": ("Triumph", "Victory"),
              "T7": ("spoons", "forks"), "T8": ("blossom", "flower")}
ALL_CONDS = ["clean", "noise_20", "noise_10", "mp3_64k", "telephone_band", "wrong_word"]
TID, LAD, WRONG = None, None, None


def degrade(x, cond, seed):
    if cond.startswith("noise"):
        snr = float(cond.split("_")[1])
        rng = np.random.default_rng(seed)
        n = rng.normal(0, 1, len(x)).astype(np.float32)
        # pink-ish noise: smooth white noise a little
        n = np.convolve(n, np.ones(8) / 8, mode="same")
        ps, pn = np.mean(x ** 2), np.mean(n ** 2)
        return x + n * np.sqrt(ps / (pn * 10 ** (snr / 10)))
    if cond == "telephone_band":
        with tempfile.TemporaryDirectory() as td:
            w, t = Path(td) / "a.wav", Path(td) / "b.wav"
            audio.save(w, x)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(w), "-af",
                            "highpass=f=300,lowpass=f=3400", "-ar", "8000", str(t)], check=True)
            return audio.load(t)
    if cond == "mp3_64k":
        with tempfile.TemporaryDirectory() as td:
            w, m = Path(td) / "a.wav", Path(td) / "a.mp3"
            audio.save(w, x)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(w), "-b:a", "64k", str(m)], check=True)
            return audio.load(m)
    return x


def _one(args):
    cond, c, tid = args
    global TID, LAD, WRONG
    TID, LAD = tid, ROOT / "data" / "ladders" / tid
    entry = WRONG_WORD.get(tid)
    WRONG = None
    if entry:
        a, b = entry
        WRONG = TEXTS[tid]["text"].replace(a, b, 1)
    elif cond == "wrong_word":
        raise ValueError(f"No WRONG_WORD entry for {tid}")
    import torch
    torch.set_num_threads(2)
    x = audio.read_wav(LAD / f"{c['id']}.wav")
    y = audio.normalize_loudness(degrade(x, cond, hash(c["id"]) % 2**31))
    rec = measure(y, WRONG if cond == "wrong_word" else TEXTS[TID]["text"])
    preds = detect(rec["feats"], rec["words"], envelope_for(TID, c["source"], None, "level"), load_params())
    return cond, score_clip(c["labels"], preds)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default="T2")
    ap.add_argument("--conds", nargs="*", default=ALL_CONDS)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    TID = a.text
    clips = [c for c in manifest(TID) if c["kind"] == "ladder" and c["labels"][0]["severity"] in (3, 5)]
    conds = a.conds
    rows = {k: [] for k in conds}
    with ProcessPoolExecutor(a.workers) as ex:
        for cond, r in ex.map(_one, [(k, c, TID) for k in conds for c in clips]):
            rows[cond].append(r)
    out = {k: aggregate(v) for k, v in rows.items()}
    path = ROOT / "results" / f"robustness_{TID}.json"
    prev = json.loads(path.read_text()) if path.exists() else (
        json.loads((ROOT / "results" / "robustness.json").read_text()) if TID == "T2" else {})
    out = {**prev, **out}  # adding a condition never discards earlier measurements
    path.write_text(json.dumps(out, indent=1))
    if TID == "T2":
        (ROOT / "results" / "robustness.json").write_text(json.dumps(out, indent=1))
    from cadence.benchmark import markdown  # results.md is regenerated, never appended to
    res = ROOT / "results" / "results.json"
    if res.exists():
        (ROOT / "results" / "results.md").write_text(markdown(json.loads(res.read_text())))
    print(json.dumps(out, indent=1))
