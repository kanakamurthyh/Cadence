# Project context: Cadence

> Living record of everything done on this project. Updated after every change.
> Last updated: 2026-10-13 (session 5: public source publication)

## 1. What this project is

Cadence is the Track C (Contrastive Speech Analytics) hackathon entry built from
`Product spec v2.pdf`.

- **Core idea:** a word is flagged only when a delivery leaves the range that several strong
  renditions of the same text occupy (the *consensus envelope*). Every flag is explained in
  measured units: seconds, semitones, dB, syllables/s.
- **Deadlines:**
  - Draft on Devpost: 14 Oct 2026, 20:00 IST.
  - Final submission: 15 Oct 2026, 00:15 IST.

## 2. Current state (summary)

| Area | Status |
|---|---|
| Pipeline: preprocess → align → features → envelope → regions → explain → scores | Done |
| Dataset: 66 LibriVox readings (T1 24, T2 23, T3 19) plus 208 ladder clips | Built; generated recordings and human-study assets remain local |
| Baselines B0 (generic norms), B1 (single reference) and B2 (envelope) | Done |
| Ablations (K, normalization, null-edit margin), τ sweep, robustness | Done |
| Gradio dashboard (analyze, A/B, dataset explorer, evidence) | Done, verified HTTP 200 and callbacks |
| FastAPI `POST /analyze`, CLI `cadence …` | Done |
| Listening-test and reader-ranking tools (`cadence human`) | Built and fixed; running on :7861; **no human data yet** |
| Human-data import: perceived-severity calibration, natural takes (`cadence natural`), `cadence status`, `cadence compare` | Done and fixture-tested; awaiting real data |
| Baseline frozen for before/after comparison | `results/baseline_2026-10-13/` |
| Technical report, data card, README | Done (`docs/`, `data/DATA_CARD.md`) |
| Reproducibility (byte-identical reruns, CI workflow, Dockerfile, uv.lock) | Done; rerun check passes |
| GitHub repo | Public source-only snapshot pushed to `main`; branch tracks `origin/main` |
| YouTube video, Devpost page | **Not done** (needs the team) |
| Stretch: Azure baseline, WavLM rhythm, re-record pilot, LLM rephrasing | Not built |

## 3. Headline results (thresholds fitted on T1 only; T2/T3 held out)

| Method | Matching Score T2 / T3 | FA/min good pairs T2 / T3 |
|---|---|---|
| B0 generic norms | 18% / 13% | 26.2 / 16.9 |
| B1 single reference (K=1) | 20% / 18% | 0.68 / 0.15 |
| **B2 envelope (K=6)** | **30% / 32%** | 1.35 / 1.32 |

**Equal false-alarm comparison:** T2 25% vs 20% at 0.68 FA/min; T3 32% vs 22% at 1.32 FA/min;
tie at T3's strictest point (0.15 FA/min).

**K ablation:** 20 → 20 → 27 → 30% on T2 for K = 1, 2, 4, 6.

**Robustness (T2, severities 3 and 5):**

| Condition | Matching Score |
|---|---|
| Clean | 42% |
| 64 kbps MP3 | 42% |
| One wrong transcript word | 42% |
| Noise, 20 dB SNR | 29% |
| Noise, 10 dB SNR | 21% |

**Known failures:**
- Pace and monotone are not detected at the shipped operating point.
- Compound clips are weak: B2 scores 12% on T2, against 38% for B0.

Full tables: `results/results.md`. Raw numbers: `results/results.json`. These compact reports
are included in the published source snapshot; generated recordings and human-study assets are
excluded.

## 4. Key decisions and why

1. **Aligner.** CTC wav2vec2 (torchaudio, pinned below 2.9), with word edges snapped to silence.
   MFA could not be installed (it needs conda); it is used automatically if `mfa` is on PATH.
2. **Texts.**

   | Text | Source | Role |
   |---|---|---|
   | T1 | *Sea Fever* (LibriVox 1452) | Calibration |
   | T2 | *Stopping by Woods* (13668) | Test |
   | T3 | Gettysburg Address, closing paragraph (8387 + 389/390/1157/1293) | Test (oratory) |

   No recording of Lincoln exists, so T3's envelope uses LibriVox readers.
3. **Locating the text** inside each LibriVox file: greedy CTC transcription plus dense
   sequence matching. This removes preambles and, for T3, the rest of the speech.
4. **Level-only normalization** (fixes v1's bug). Pitch and loudness are referenced to the
   speaker's median; range, dynamics, rate and pauses stay absolute.
5. **Log-scale comparison** for rate, pause and pitch range. Rate uses a 5-word window and
   loudness a 3-word window, to reduce word-level noise.
6. **m_f and s_f** (margin and scale) are fitted on T1 and frozen, so K=1 is exactly the B1
   baseline.
7. **Consensus-aware pause ladders.**
   - A missing pause is injected only where every good reader pauses.
   - A misplaced pause is injected only where none does.

   The earlier version produced mislabeled "flaws" that were really style.
8. **Calibration rule.** One τ per flaw type, by coordinate ascent: maximize T1 Matching Score
   subject to ≤ 1 false alarm/min on good-vs-good pairs. The same rule is applied to B1.
   - Earlier attempts (one global τ; a penalty-weighted objective; a global multiplier) were
     replaced. They either disabled types or chose an arbitrary operating point.
   - **Do not retune on T2/T3.**
9. **Good set.** Top 6 per text, ranked provisionally by mean aligner confidence. This is
   replaced automatically once `data/rankings/<T>.csv` exists.
10. **Severity.** Isotonic mapping onto the injected level (1–5), fitted on T1. With listening
    responses it maps onto mean perceived severity (0–4) per (type, level), still T1 only.
    This was claimed earlier but only implemented on 2026-10-13 (session 4).
11. **Human-data order.** Ranking → `cadence refs` → `cadence ladders` → listening test →
    takes → `cadence evaluate`. Ladder clips are reused only if the source reading and
    spans match, so a new good set cannot leak the edited reading into its own envelope.
    Listening rows store the ladder `source`; rows from older ladders are ignored.
12. **Natural takes** are test data only: `data/takes/<T>/<speaker>_<T>_take<n>.*`, with
    Audacity labels in `data/annotations/<annotator>/<take_id>.txt`. They never enter
    calibration or the good set.

## 5. Layout

```
cadence/        package: audio, align, features, envelope, detect, inject, pipeline,
                baselines, metrics, evaluate, benchmark, app (Gradio), api (FastAPI),
                human (listening test + ranking), cli, data/{texts,librivox}
scripts/        fetch_librivox, build_refs, build_ladders, robustness, make_demo, rerun_check
data/           demo/, params.json, DATA_CARD.md; raw/, refs/, ladders/, listening/ and
                rankings/ are generated/local assets and gitignored
results/        results.json, results.md, robustness.json, rerun_hashes.json
docs/           technical_report.md
tests/          test_core.py (8 tests, passing)
logs/           run logs
```

## 6. How to run

```bash
uv sync --extra dev
uv run cadence all        # fetch → refs → ladders → evaluate (~40 min, M3)
uv run cadence app        # dashboard :7860
uv run cadence human      # listening test + reader ranking :7861
uv run cadence analyze file.wav --text T2
```

Long jobs: run with `nohup` and ≤ 3 workers. Earlier sessions were killed (exit 137) under
memory pressure.

## 7. Pending / next steps

- [ ] Step 1: 3 teammates rank all 66 readings (`cadence human` → Rank readers; T1, T2, T3).
- [ ] Step 2: `cadence refs && cadence ladders`, then check with `cadence status`.
- [ ] Step 3: 5 listeners take the listening test (on the rebuilt ladders).
- [ ] Step 4: teammate takes plus 2 independent annotators (protocol in `docs/human_data_protocol.md`).
- [ ] Step 5: `cadence evaluate`, robustness, make_demo, `rerun_check --store`, `cadence compare`.
- [ ] Phone-microphone robustness take.
- [ ] Improve pace and monotone detection: region-level rate, a stricter good set, WavLM rhythm.
- [ ] The demo clip's rushed pace is not detected; adjust the 0:50 demo segment or fix pace.
- [ ] Publish the dataset link separately; generated recordings and human-study assets are not in Git.
- [ ] YouTube video (3–10 min, opening with the section 9 script) and the Devpost page (Track C, all teammates).

## 8. Change log

- **2026-10-13: initial build (sessions 1–3).**
  - Read the spec.
  - Set up the environment: uv, Python 3.12, ffmpeg via brew.
  - Fetched LibriVox (66 recordings; first reported as 65, corrected 2026-10-13).
  - Built the pipeline, injector, evaluation, dashboard, API, CLI and human-study tools.
- **2026-10-13: detector fixes after the first sanity test.**
  - Log-scale comparison; wider rate and loudness windows.
  - Capped edge shrinking; two-pass pitch limits.
  - Emphasis flattened to the neighbours' median.
- **2026-10-13: fixed the compound-clip time map.** PSOLA-warped vs. original edit positions.
- **2026-10-13: dataset fix.** Consensus-aware pause spans and wider emphasis candidates;
  rebuilt the affected clips.
- **2026-10-13: calibration.**
  - Per-type τ: fixed a bug where only the last type kept its threshold.
  - Final rule: ≤ 1 FA/min coordinate ascent.
  - Evaluation rerun.
- **2026-10-13: wrap-up.**
  - Ran robustness, demo clips (including the style pair) and the rerun-hash check.
  - Wrote the technical report, README results and data card.
  - Verified the dashboard callbacks.
- **2026-10-13: added this `project context.md` file.** Also added `CLAUDE.md` with the rule
  to keep this file current, the T1-only tuning rule, and the nohup / ≤ 3 workers guidance.
- **2026-10-13 (session 4): human-data tooling.** The user took over data collection.
  - Froze the baseline results in `results/baseline_2026-10-13/`.
  - Fixed `human.py`:
    - names are case- and space-insensitive;
    - clicking past the last trial no longer crashes;
    - an empty rater name is rejected;
    - responses store the ladder source, and stale rows are ignored;
    - the segment cache is keyed by source.
  - Severity calibration now uses perceived ratings when they exist (T1 only).
  - Added `severity_vs_listeners`.
  - Ladder cache guard (`_same_plan`), so a new good set cannot cause leakage.
  - New `cadence/natural.py` (takes plus Audacity annotations: system vs annotator, annotator
    vs annotator), `cadence status`, `cadence compare`, `docs/human_data_protocol.md`.
  - 5 new tests (13 total, passing).
  - Corrected the recording count: 66, not 65; T1 has 24.
  - The fixture test of every path passed.
  - Launched `cadence human` on :7861 (HTTP 200; 24/23/19 excerpts generated).
- **2026-10-13 (session 5): public source publication.** Initialized the empty public GitHub
  repository and pushed a source-only snapshot to `main` (`c44c5b0`). Added ignores for generated
  recordings, human-study assets, run logs, caches, and the unlicensed project-spec PDF; retained
  source, docs, compact results, and demo fixtures.
