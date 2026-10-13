"""Word alignment for a known transcript.

Backends, in order of preference (spec section 7, choice 1):
  * Montreal Forced Aligner, if `mfa` is on PATH (lowest published boundary error);
  * CTC forced alignment with wav2vec2 (the model WhisperX uses for alignment),
    run through torchaudio.functional.forced_align (torchaudio pinned below 2.9).
Set CADENCE_ALIGNER=ctc or =mfa to force one.

Word edges are then snapped to silence edges (see features.refine_edges).
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path

import numpy as np

from .audio import SR, save

FRAME_S = 320 / SR  # wav2vec2 frame stride


def words_of(text: str) -> list[str]:
    """Tokenize a transcript into the words we align and score."""
    text = text.replace("-", " ").replace("’", "'")
    return [w.strip("'") for w in re.findall(r"[A-Za-z']+", text) if w.strip("'")]


def backend() -> str:
    pref = os.environ.get("CADENCE_ALIGNER", "auto")
    if pref == "auto":
        return "mfa" if shutil.which("mfa") else "ctc"
    return pref


@lru_cache(maxsize=1)
def _w2v():
    import torch
    import torchaudio
    torch.set_num_threads(max(1, os.cpu_count() or 1))
    bundle = torchaudio.pipelines.WAV2VEC2_ASR_BASE_960H
    model = bundle.get_model().eval()
    labels = bundle.get_labels()
    return model, labels, {c: i for i, c in enumerate(labels)}


def emissions(x: np.ndarray, chunk_s: float = 20.0, ctx_s: float = 1.0) -> np.ndarray:
    """Frame log-probabilities (T, C), computed in overlapping chunks."""
    import torch
    model, _, _ = _w2v()
    n_frames = int(len(x) / (SR * FRAME_S))
    out = []
    step = int(chunk_s / FRAME_S)
    ctx = int(ctx_s / FRAME_S)
    with torch.inference_mode():
        for f0 in range(0, n_frames, step):
            f1 = min(n_frames, f0 + step)
            a = max(0, f0 - ctx)
            b = min(n_frames, f1 + ctx)
            seg = torch.from_numpy(x[int(a * FRAME_S * SR): int(b * FRAME_S * SR)])[None]
            if seg.shape[1] < 400:
                seg = torch.nn.functional.pad(seg, (0, 400 - seg.shape[1]))
            em = torch.log_softmax(model(seg)[0], dim=-1)[0].numpy()
            lo = f0 - a
            out.append(em[lo: lo + (f1 - f0)])
    em = np.concatenate(out)
    if len(em) < n_frames:  # pad the tail with blanks
        pad = np.full((n_frames - len(em), em.shape[1]), -30.0, dtype=em.dtype)
        pad[:, 0] = 0.0
        em = np.concatenate([em, pad])
    return em


def transcribe(x: np.ndarray, em: np.ndarray | None = None) -> list[dict]:
    """Greedy CTC transcription with word times (used to find the text in a recording)."""
    _, labels, _ = _w2v()
    em = emissions(x) if em is None else em
    ids = em.argmax(1)
    words, cur, start, last = [], "", None, None
    prev = -1
    for t, i in enumerate(ids):
        if i != prev and i != 0:
            ch = labels[i]
            if ch == "|":
                if cur:
                    words.append({"word": cur.lower(), "start": start * FRAME_S, "end": (last + 1) * FRAME_S})
                cur, start = "", None
            else:
                if start is None:
                    start = t
                cur += ch
                last = t
        elif i == prev and i != 0 and labels[i] != "|":
            last = t
        prev = i
    if cur:
        words.append({"word": cur.lower(), "start": start * FRAME_S, "end": (last + 1) * FRAME_S})
    return words


def locate_text(x: np.ndarray, transcript: str, pad_s: float = 0.25) -> tuple[float, float]:
    """Find where `transcript` is read inside a longer recording (LibriVox
    preambles, titles, end notes, or a full speech around an excerpt)."""
    asr = transcribe(x)
    a = [w["word"].replace("'", "") for w in asr]
    b = [w.lower().replace("'", "") for w in words_of(transcript)]
    sm = SequenceMatcher(None, a, b, autojunk=False)
    pairs = [(blk.a + k, blk.b + k) for blk in sm.get_matching_blocks() for k in range(blk.size)]
    if not pairs:
        raise ValueError("transcript not found in recording")

    def dense(i, sign):
        ai, bj = pairs[i]
        return sum(1 for (a2, b2) in pairs
                   if 0 < sign * (a2 - ai) < 14 and 0 < sign * (b2 - bj) < 14) >= 4

    first = next((p for i, p in enumerate(pairs) if p[1] <= 8 and dense(i, +1)), pairs[0])
    last = next((p for i, p in reversed(list(enumerate(pairs)))
                 if p[1] >= len(b) - 9 and dense(i, -1)), pairs[-1])
    ia = max(0, first[0] - first[1])
    ib = min(len(a) - 1, last[0] + (len(b) - 1 - last[1]))
    lo = max(asr[ia - 1]["end"] + 0.05 if ia > 0 else 0.0, asr[ia]["start"] - pad_s)
    hi = min(asr[ib + 1]["start"] - 0.05 if ib + 1 < len(asr) else len(x) / SR, asr[ib]["end"] + pad_s)
    return max(0.0, lo), min(len(x) / SR, hi)


def _align_ctc(x: np.ndarray, words: list[str]) -> list[dict]:
    import torch
    import torchaudio.functional as F
    _, labels, idx = _w2v()
    em = emissions(x)
    tokens, owner = [], []
    for wi, w in enumerate(words):
        for ch in w.upper():
            if ch in idx:
                tokens.append(idx[ch])
                owner.append(wi)
        if wi < len(words) - 1:
            tokens.append(idx["|"])
            owner.append(-1)
    ali, scores = F.forced_align(torch.from_numpy(em)[None], torch.tensor([tokens], dtype=torch.int32), blank=0)
    spans = F.merge_tokens(ali[0], scores[0].exp())
    out = [{"word": w, "start": None, "end": None, "score": []} for w in words]
    for sp, wi in zip(spans, owner):
        if wi < 0:
            continue
        o = out[wi]
        o["start"] = sp.start * FRAME_S if o["start"] is None else o["start"]
        o["end"] = sp.end * FRAME_S
        o["score"].append(float(sp.score))
    for o in out:
        o["score"] = float(np.mean(o["score"])) if o["score"] else 0.0
    return out


def _align_mfa(x: np.ndarray, words: list[str]) -> list[dict]:
    import parselmouth
    with tempfile.TemporaryDirectory() as td:
        corpus, out = Path(td) / "corpus", Path(td) / "out"
        corpus.mkdir()
        save(corpus / "utt.wav", x)
        (corpus / "utt.lab").write_text(" ".join(words))
        subprocess.run(["mfa", "align", "--clean", "--single_speaker", str(corpus),
                        "english_us_arpa", "english_us_arpa", str(out)],
                       check=True, capture_output=True)
        tg = parselmouth.read(str(out / "utt.TextGrid"))
        tier = parselmouth.praat.call(tg, "Get number of intervals", 1)
        ints = []
        for i in range(1, tier + 1):
            lab = parselmouth.praat.call(tg, "Get label of interval", 1, i).strip()
            if lab:
                ints.append((lab, parselmouth.praat.call(tg, "Get start time of interval", 1, i),
                             parselmouth.praat.call(tg, "Get end time of interval", 1, i)))
    if len(ints) != len(words):
        raise RuntimeError("MFA word count mismatch; falling back to CTC")
    return [{"word": w, "start": s, "end": e, "score": 1.0} for w, (_, s, e) in zip(words, ints)]


def align(x: np.ndarray, transcript: str) -> list[dict]:
    """Return one {word, start, end, score} per transcript word, in seconds."""
    words = words_of(transcript)
    if backend() == "mfa":
        try:
            return _align_mfa(x, words)
        except Exception:
            pass
    return _align_ctc(x, words)
