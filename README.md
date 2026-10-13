# Cadence

**Contrastive speech analytics (Track C).** Cadence pinpoints the words where a delivery
falls outside the range that several strong performances of the same text occupy, and
explains each flag in measured units: seconds, semitones, dB and syllables per second.
Because it judges against that range instead of one reference or generic norms, it can
tell a real flaw from a legitimate stylistic choice.

```
upload ─► preprocess ─► align words ─► extract features ─► ENVELOPE COMPARE ─► detect regions ─► type + explain ─► report
          16 kHz,        MFA, or CTC    Praat, level-only    vs K good            hysteresis on d    dominant feature,   rubric scores,
          -23 LUFS       wav2vec2       normalization        renditions           snap to words      measured deltas     JSON, overlay, A/B
                                                                  ▲                                         ▲
                       dataset factory (offline): good renditions ─► flaw injector ─► labelled ladders ─────┘ calibration
```

## Prerequisites

- macOS or Linux, Python 3.12, [`uv`](https://docs.astral.sh/uv/), and `ffmpeg` on PATH
  (`brew install uv ffmpeg`, or use the Dockerfile).
- About 3 GB of disk: PyTorch plus the 360 MB wav2vec2 alignment model, which downloads on first run.
- Optional: the Montreal Forced Aligner (`mfa` on PATH, with the `english_us_arpa` models).
  When it is present it is used automatically; otherwise the CTC wav2vec2 aligner runs.

## Setup and one-command run

```bash
uv sync --extra dev          # pinned environment from uv.lock
uv run cadence all           # fetch LibriVox -> refs -> ladders -> calibrate + evaluate (~40 min on an M3)
uv run cadence app           # dashboard at http://localhost:7860
```

Individual steps:

| Command | What it does |
|---|---|
| `cadence fetch` | Downloads every reader of the 3 texts from LibriVox into `data/raw/` |
| `cadence refs` | Locates the text in each reading, aligns, measures, and picks the good set (`data/refs/`) |
| `cadence ladders` | Builds 6 flaw types × 2 spans × 5 severities per text, plus null-edit and compound clips (`data/ladders/`) |
| `cadence evaluate` | Calibrates on T1, evaluates B0/B1/B2 and the ablations on T2/T3, and writes `results/` |
| `cadence analyze my.wav --text T2` | Prints the JSON report for one recording |
| `cadence app` | Gradio dashboard: upload or record, envelope overlay, flaw cards, A/B playback, dataset explorer, evidence |
| `cadence human` | Listening test and reader-ranking pages (port 7861) |
| `cadence status` | Checklist: which human-data steps are done and consistent |
| `cadence inventory` | Every recording: source, speaker, licence, files, alignment quality, speaker overlap |
| `cadence labels` | Exports `data/labels/labels.{jsonl,csv}` and validates every synthetic clip |
| `cadence natural` | Validates teammate takes and annotations, then evaluates natural flaws |
| `cadence compare` | Baseline (`results/baseline_2026-10-13`) vs current results → `results/comparison.md` |
| `cadence api` | FastAPI: `POST /analyze` (multipart `file`, `text_id`) |
| `python scripts/robustness.py` | Noise, MP3 and wrong-word robustness on T2 |
| `python scripts/rerun_check.py` | Byte-identical rerun check (also run in CI) |

## Data

| Text | Source | Readers | Role |
|---|---|---|---|
| T1 | *Sea Fever*, Masefield. LibriVox weekly poetry, 2007 | 24 | Calibration only: thresholds, λ, severity mapping |
| T2 | *Stopping by Woods on a Snowy Evening*, Frost. LibriVox | 23 | Test |
| T3 | Gettysburg Address, closing paragraph. LibriVox (150th anniversary + 4 solo versions) | 19 | Test (oratory) |
| T4 | Gettysburg Address, opening paragraph. Same 19 readings as T3 | 19 | Test (oratory); shares speakers with T3 |
| T5 | FDR "Day of Infamy" opening. Original 1941 recording (public domain, NARA) + 1 LibriVox reading | 2 | Test (oratory); **blocked until ≥ 2 teammate takes** |

TED/TEDx talks are CC BY-NC-ND 4.0, so no derivatives and no clips; they are listed as
candidates only. See [`docs/DATA_LICENSING.md`](docs/DATA_LICENSING.md).

All recordings are public domain (LibriVox). The dataset card is in [`data/DATA_CARD.md`](data/DATA_CARD.md).

## How it scores (published formulas)

For word *w*, feature *f* and K good renditions (rate, pause and pitch range are compared on a log scale):

    L = min_k x_k − m_f,   U = max_k x_k + m_f,   d = max(0, L − x, x − U) / s_f

- *m_f* is the 95th percentile of |reference − null-edited reference|.
- *s_f* is the median envelope width on T1.
- Both are frozen after calibration, so K = 1 is exactly the single-reference baseline.

Regions come from hysteresis on d (open above τ_high, close below τ_high/2) and are typed by
the dominant feature. Missed emphasis is checked only at consensus stress points, where at
least 3/4 of the good readers peak in pitch or loudness. Each dimension score is
10·exp(−λ_d Σ d̄_r·dur_r/T). See [`docs/technical_report.md`](docs/technical_report.md).

## Results (detector v2; thresholds fitted on T1 only; full tables in `results/results.md`)

T2–T4 are **development feedback**, because v2 was motivated partly by inspecting T3/T4.
**T6** (Kipling's *If—*, 15 readers, no shared speakers) is the **untouched final test**: it was
added after v2 was frozen and evaluated once. v1 results are frozen in `results/frozen_v1_2026-10-14/`.

| Text | B0 generic norms | B1 single reference | B2 envelope (ours) |
|---|---|---|---|
| T3 Gettysburg, closing (dev) | 13%, 16.9 FA/min | 25%, 0.73 | 30%, 1.47 |
| T4 Gettysburg, opening (dev) | 15%, 19.3 | 27%, 0.94 | **35%, 0.24** |
| **T6 untouched** | 13%, 22.5 | **27%, 2.15** | 23%, 2.15 |

**On untouched data the envelope does not beat the single reference.** At ≤ 1 false alarm/min
on T6, B1 scores 15% and B2 5%. The dashboard therefore offers B1 as a calibrated fallback
("Comparison method").

| Detection | Status |
|---|---|
| Misplaced pauses | Reliable: 60–80% recall, 100% precision |
| Pace | Works on the speeches (50–60%), fails on T6 (0%) |
| Volume fade, missing pause, monotone | 10–40% |
| Missed emphasis | Not detected in v2 |

**Demo** (`cadence demo`, Demo tab): a rushed-pace edit on T4 is found by B2 with IoU 0.97
(onset error 8 ms). B1 misses it, and B0 smears it over 6.8 s.

## Status and honest deviations from the spec

- **Aligner.** MFA could not be installed here (it needs conda), so the results use the
  CTC wav2vec2 fallback the spec names for that case. Word edges are snapped to silence edges.
  MFA is supported automatically when present.
- **Human data is pending.** The provisional good set is ranked by aligner confidence, which
  measures clarity and fidelity to the text and is independent of the prosodic features we judge.
  - Reader ranking (3 raters), the listening test (5 listeners) and teammate takes need people.
    The tools are ready (`cadence human`), and rerunning `cadence refs && cadence evaluate`
    picks the data up.
  - Until then, the severity scale is the injected level (1–5). Once listening responses exist,
    `cadence evaluate` fits the T1 severity map to perceived severity (0–4). The natural-spectrum
    Spearman and the natural-flaw F1 are reported as *pending* until the data exists. The
    collection procedure is in [`docs/human_data_protocol.md`](docs/human_data_protocol.md).
- **T3 envelope.** No recording of Lincoln exists. T3's envelope uses LibriVox readers until
  teammate takes are added.
- **Not built (stretch):** Azure baseline (needs a key), WavLM rhythm, re-record pilot, and
  language-model rephrasing.
