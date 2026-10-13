"""Preprocess: decode, 16 kHz mono, loudness to -23 LUFS, voice activity."""
from __future__ import annotations

import subprocess
from functools import lru_cache
from pathlib import Path

import numpy as np
import pyloudnorm
import soundfile as sf

SR = 16000
TARGET_LUFS = -23.0


def load(path: str | Path, sr: int = SR) -> np.ndarray:
    """Decode any format ffmpeg reads to float32 mono at `sr`."""
    out = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-i", str(path), "-f", "f32le",
         "-ac", "1", "-ar", str(sr), "-"],
        check=True, capture_output=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


def normalize_loudness(x: np.ndarray, sr: int = SR) -> np.ndarray:
    meter = pyloudnorm.Meter(sr)
    lufs = meter.integrated_loudness(x.astype(np.float64))
    if not np.isfinite(lufs):
        return x
    y = x * 10 ** ((TARGET_LUFS - lufs) / 20)
    peak = np.abs(y).max()
    return (y / peak * 0.99 if peak > 0.99 else y).astype(np.float32)


def save(path: str | Path, x: np.ndarray, sr: int = SR) -> None:
    sf.write(str(path), x, sr, subtype="PCM_16")


def read_wav(path: str | Path) -> np.ndarray:
    x, sr = sf.read(str(path), dtype="float32")
    assert sr == SR, f"{path}: expected {SR} Hz, got {sr}"
    return x


@lru_cache(maxsize=1)
def _silero():
    from silero_vad import load_silero_vad
    return load_silero_vad()


def speech_segments(x: np.ndarray, sr: int = SR) -> list[tuple[float, float]]:
    """Silero VAD speech spans in seconds."""
    import torch
    from silero_vad import get_speech_timestamps
    ts = get_speech_timestamps(torch.from_numpy(x), _silero(), sampling_rate=sr,
                               min_silence_duration_ms=60, speech_pad_ms=20)
    return [(t["start"] / sr, t["end"] / sr) for t in ts]


def preprocess(path: str | Path) -> np.ndarray:
    return normalize_loudness(load(path))
