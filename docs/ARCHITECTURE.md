# Cadence architecture

This page explains how the code is organised, how data moves through it, and why it is built
that way. For setup and commands see the [README](../README.md); for the method and results
see [`technical_report.md`](technical_report.md).

## Big picture

Cadence has two halves that share one feature extractor and one detector:

- the **online path** analyses a single upload against the good renditions of the same text;
- the **offline path** builds the reference set and the labelled synthetic dataset, then
  calibrates the detector on T1 and evaluates it on the held-out texts.

```
                         OFFLINE (dataset factory + calibration)
  cadence fetch          cadence refs                cadence ladders           cadence evaluate
  data/librivox.py  ──►  scripts/build_refs.py  ──►  scripts/build_ladders.py ──► evaluate.py + benchmark.py
  data/raw/              data/refs/T*/<id>.json      inject.py, labels.py         data/params.json
                         selection.json (good set)   data/ladders/, data/labels/  results/results.{json,md}
                                   │                                                  │
                                   ▼ good renditions                                  ▼ fitted params
  ─────────────────────────────────────────────────────────────────────────────────────────────────
                         ONLINE (pipeline.analyze, one upload)
  audio file ─► audio.preprocess ─► align ─► features ─► envelope.build + deviations ─► detect ─► report
                16 kHz mono,        MFA or   per-word     min/max of K good readings     regions,  JSON + hash
                -23 LUFS, VAD       wav2vec2 rate, pause, plus margin m_f; scaled d      type,
                                    CTC      pitch, loud                                 severity
  ─────────────────────────────────────────────────────────────────────────────────────────────────
  Interfaces: cli.py (cadence <cmd>) · app.py (Gradio :7860) · web.py + web/ (coach :8000) · api.py (FastAPI)
```

## Online path: `cadence/pipeline.py`

`pipeline.analyze(audio_path, text_id)` is the single function every interface calls.

1. **Preprocess** (`audio.py`): decode with ffmpeg, resample to 16 kHz mono, normalise loudness
   to -23 LUFS, detect voice activity.
2. **Align** (`align.py`): locate the known transcript in the recording and time every word.
   It uses the Montreal Forced Aligner when `mfa` is on PATH, otherwise a CTC wav2vec2 aligner
   (the model downloads on first use).
3. **Features** (`features.py`): per-word rate (syll/s), following pause (s), pitch range (st),
   loudness (dB) and prominence. Speaker normalisation is level-only: it removes what biology and
   microphones change and keeps what delivery changes.
4. **Envelope** (`envelope.py`): `build()` takes the features of the K good renditions listed in
   `data/refs/<T>/selection.json` and stores, per word and feature, `L = min - m_f` and
   `U = max + m_f`. `deviations()` turns the upload's distance outside `[L, U]` into a scaled
   deviation `d` per channel. Channels (`CHANNELS`) pair a feature and direction with a flaw type;
   v2 added self-relative channels and v3 phrase channels, appended so older indices never move.
5. **Detect** (`detect.py`): hysteresis on `d` (`tau_high`, `tau_low = tau/2`) gives word regions;
   each region gets a type from its dominant channel, a severity, a plain-language explanation in
   measured units, and the six rubric scores (`DIMENSION` maps flaw type to rubric dimension).
6. **Report** (`pipeline.report`): rounds every number, adds the reference ids used, and hashes
   the sorted JSON.

`measure()` (steps 1-3) is also what `scripts/build_refs.py` runs on every reference reading, so
uploads and references are measured by exactly the same code.

## Offline path

- **Texts** (`cadence/data/texts.py`): the canonical transcript, display layout, role
  (`calibration` or `test...`), and source ids for T1-T8. `MIN_GOOD = 4` renditions are needed
  for an envelope.
- **Fetch** (`cadence/data/librivox.py`, `scripts/fetch_librivox.py`): downloads every reader's
  recording into `data/raw/`, sha1-checked where a hash is known.
- **Refs** (`scripts/build_refs.py`): crops the text out of each reading, aligns, measures, saves
  one JSON per reading and picks the good set (`selection.json`).
- **Ladders** (`inject.py`, `scripts/build_ladders.py`): the flaw injector applies each flaw type
  at five severities (`inject.SEVERITY`) to word spans chosen by a fixed-seed generator. Every
  clip, including clean null-edit controls, goes through the same PSOLA resynthesis, so clean and
  flawed audio share processing artifacts.
- **Labels** (`labels.py`): exports `data/labels/labels.{jsonl,csv}` and validates each clip
  (measured effect vs expected, timing, clicks) into `validation.json`.
- **Natural and human data** (`natural.py`, `human.py`, `status.py`): teammate takes with
  independent annotations, the listening test and reader ranking, and a consistency checklist.

## Calibration and evaluation

- `evaluate.py` defines a `Config` (method B0 or envelope, K, normalisation, margin, channel
  options), `calibrate()` fits thresholds, λ and the severity mapping on T1, and `run()` scores a
  config on one text with `metrics.py`. Leakage rule: the rendition a clip was made from is never
  in its own envelope.
- `baselines.py` holds B0 (generic norms as commercial coaching apps apply them); B1 is the
  envelope with K=1; B2 is the full envelope.
- `benchmark.py` calibrates both detector candidates on T1, applies the **pre-registered ship
  rule** (`ship_decision`: v3 ships only if it beats v2 on T1, on at least two held-out texts, and
  never breaks the false-alarm cap where v2 respects it), evaluates baselines and ablations on
  every eligible held-out text, and writes `data/params.json`, `data/params_B1.json` and
  `results/results.{json,md}`.
- `compare.py` diffs two runs; `demo.py` picks the demo case from computed results;
  `scripts/robustness.py` measures noise, MP3, telephone-band and wrong-word robustness.

## Interfaces

All four are thin layers over `pipeline.analyze`:

| Module | Serves | Notes |
|---|---|---|
| `cli.py` | `cadence <command>` | argparse; imports each subcommand lazily so `cadence --help` is fast |
| `app.py` | Gradio dashboard, :7860 | envelope overlay, flaw cards, A/B playback, dataset explorer, evidence |
| `web.py` + `web/` | coach web app, :8000 | FastAPI + static HTML/JS/CSS; recordings stay in memory only |
| `api.py` | FastAPI, :8000 | `POST /analyze` with multipart `file` and `text_id` |

## Key design decisions

- **Determinism.** `pipeline._r` rounds every float to 4 decimals (non-finite becomes `null`),
  reports are serialised with `sort_keys=True`, and the report carries a SHA-256 hash of its own
  sorted JSON. `scripts/rerun_check.py` analyses two demo clips twice and compares against
  `results/rerun_hashes.json`; it runs in CI and in `make verify`. The Dockerfile sets
  `PYTHONHASHSEED=0` and limits `OMP_NUM_THREADS`; span selection uses fixed-seed generators.
- **Frozen parameters.** The online path never fits anything: it reads `data/params.json`
  (`fitted_on: "T1 (K=all)"`), or `params_B1.json` when only one reference is available. Only
  `cadence evaluate` writes those files.
- **T1-only calibration.** Thresholds, λ and the severity mapping are fitted on T1. T2-T8 are
  held out and are never used to retune anything.
- **Pre-registered ship rule.** Which detector version ships is decided by code written before
  the held-out numbers were seen, not by inspection.
- **Same code for references and uploads.** `pipeline.measure` produces both, so any change to
  features applies to both sides of the comparison.
- **Committed reference features.** `data/refs/` JSONs (2.6 MB) are in git, so analysis works
  from a fresh clone; WAVs are only needed for A/B playback and for rebuilding.

## Where artifacts live

| Path | Contents | Produced by |
|---|---|---|
| `data/raw/` | downloaded source recordings (not committed) | `cadence fetch` |
| `data/refs/<T>/` | per-reading features, `selection.json`, reference WAVs (WAVs not committed) | `cadence refs` |
| `data/ladders/<T>/` | synthetic flaw, null-edit and compound clips | `cadence ladders` |
| `data/labels/` | `labels.{jsonl,csv}`, `validation.json` | `cadence labels` |
| `data/params.json`, `params_B1.json` | frozen detector parameters | `cadence evaluate` |
| `data/inventory.{csv,json}` | every recording, licence, counts | `cadence inventory` |
| `data/demo/` | demo clips and their labels | `cadence demo`, `scripts/make_demo.py` |
| `results/` | `results.{json,md}`, `rerun_hashes.json`, robustness, frozen snapshots | `cadence evaluate`, scripts |

## How to extend

**Add a text.** Add an entry to `TEXTS` in `cadence/data/texts.py` (title, author, `role`,
source ids, exact `text`) and a line-broken version in `DISPLAY`. Then run `cadence fetch`,
`cadence refs` (needs at least `MIN_GOOD = 4` good renditions) and, for evaluation,
`cadence ladders` and `cadence evaluate`. Do not use the new text to retune parameters; give it
a `test...` role so it is evaluated as held out.

**Add a flaw type.**
1. `inject.py`: add its severity ladder to `SEVERITY` and the signal edit to `add_flaw`, and
   teach `choose_spans` where it may be placed.
2. `envelope.py`: add the name to `FLAW_TYPES` and append its channel(s) to `CHANNELS`
   (append only, so existing channel indices stay stable); add any new feature in `features.py`.
3. `detect.py`: map it to a rubric dimension in `DIMENSION` and add its explanation text.
4. `labels.py`: add the expected effect for validation.
5. Rebuild ladders, rerun `cadence evaluate` (calibration still on T1 only), and add a test in
   `tests/test_core.py`. If report output changes, refresh `results/rerun_hashes.json` with
   `python scripts/rerun_check.py --store` and say so in the change log.
