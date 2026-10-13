"""Robustness (spec section 8): T2 ladders at severities 3 and 5 under
background noise (20 and 10 dB SNR), 64 kbps MP3, and one wrong transcript word.
Phone-microphone re-recording needs a person and is left to the team.
Writes results/robustness.json and appends a table to results/results.md.
"""
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

TID = "T2"
LAD = ROOT / "data" / "ladders" / TID
WRONG = TEXTS[TID]["text"].replace("queer", "strange")


def degrade(x, cond, seed):
    if cond.startswith("noise"):
        snr = float(cond.split("_")[1])
        rng = np.random.default_rng(seed)
        n = rng.normal(0, 1, len(x)).astype(np.float32)
        # pink-ish noise: smooth white noise a little
        n = np.convolve(n, np.ones(8) / 8, mode="same")
        ps, pn = np.mean(x ** 2), np.mean(n ** 2)
        return x + n * np.sqrt(ps / (pn * 10 ** (snr / 10)))
    if cond == "mp3_64k":
        with tempfile.TemporaryDirectory() as td:
            w, m = Path(td) / "a.wav", Path(td) / "a.mp3"
            audio.save(w, x)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(w), "-b:a", "64k", str(m)], check=True)
            return audio.load(m)
    return x


def _one(args):
    cond, c = args
    import torch
    torch.set_num_threads(2)
    x = audio.read_wav(LAD / f"{c['id']}.wav")
    y = audio.normalize_loudness(degrade(x, cond, hash(c["id"]) % 2**31))
    rec = measure(y, WRONG if cond == "wrong_word" else TEXTS[TID]["text"])
    preds = detect(rec["feats"], rec["words"], envelope_for(TID, c["source"], None, "level"), load_params())
    return cond, score_clip(c["labels"], preds)


if __name__ == "__main__":
    clips = [c for c in manifest(TID) if c["kind"] == "ladder" and c["labels"][0]["severity"] in (3, 5)]
    conds = ["clean", "noise_20", "noise_10", "mp3_64k", "wrong_word"]
    rows = {k: [] for k in conds}
    with ProcessPoolExecutor(6) as ex:
        for cond, r in ex.map(_one, [(k, c) for k in conds for c in clips]):
            rows[cond].append(r)
    out = {k: aggregate(v) for k, v in rows.items()}
    (ROOT / "results" / "robustness.json").write_text(json.dumps(out, indent=1))
    md = ["\n### Robustness (T2 ladders, severities 3 and 5, envelope K=all)\n",
          "| Condition | Matching Score | Time F1 | Onset err (ms) |", "|---|---|---|---|"]
    for k, a in out.items():
        md.append(f"| {k} | {100 * a['matching_score']:.0f}% | {a['time_f1']:.2f} | {a['onset_ms_median']:.0f} |")
    with (ROOT / "results" / "results.md").open("a") as fh:
        fh.write("\n".join(md) + "\n")
    print("\n".join(md))
