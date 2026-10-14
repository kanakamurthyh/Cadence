# Project context: Cadence

> Living record of everything done on this project. Updated after every change.
> Last updated: 2026-10-14 (session 10: final documentation pass — dataset v3 results, Indian held-out texts T7/T8, pre-registered v3 decision)

## 1. What this project is

Cadence is the Track C (Contrastive Speech Analytics) hackathon entry built from
`Product spec v2.pdf`.

- **Core idea:** a word is flagged only when a delivery leaves the range that several strong
  renditions of the same text occupy (the *consensus envelope*). Every flag is explained in
  measured units: seconds, semitones, dB, syllables/s.
- **Deadlines:**
  - Draft on Devpost: 14 Oct 2026, 20:00 IST.
  - Final submission: 15 Oct 2026, 00:15 IST.

## 1b. How Cadence works (plain-language overview)

**The question it answers.** "Where, word by word, does this delivery fall outside what good
speakers do with the *same text*, and by how much?" It does **not** give a generic "good
speaker" score. Different strong speakers pause, speed up and stress words differently, so
Cadence treats the whole range they span as acceptable. It flags a word only when the attempt
falls outside that range. This range is the **consensus envelope**.

### What happens when you analyze a recording (dashboard → Analyze)

1. **Input.** Record with the microphone (the default) or upload a file of any format. Uploads
   are converted to WAV so every browser can play them. You must read the **whole selected
   passage**; the dashboard shows it, with a typical reading time.
2. **Preprocess** (`audio.py`): decode with ffmpeg, convert to 16 kHz mono, normalize loudness
   to −23 LUFS.
3. **Find the text** (`align.locate_text`): a wav2vec2 speech recognizer transcribes the audio
   and matches it to the passage, trimming anything before or after, such as a spoken title.
   The match is measured on **letters**, so misheard words still count. If less than 40% of the
   passage is recognized, the analysis stops with an error saying what was heard. This prevents
   comparing unrelated speech.
4. **Align words** (`align.py`): forced alignment gives every word a start and end time
   (MFA if installed, otherwise CTC wav2vec2). Edges are then snapped to silences.
5. **Measure** (`features.py`). Per word:
   - speaking rate (syllables/s, 5-word window);
   - pause after the word (s);
   - pitch range (semitones, 3-word window);
   - loudness (dB relative to your own median);
   - pitch and loudness prominence over neighbouring words.

   Pitch and loudness are referenced to *your* median ("level-only" normalization), so voice
   type and microphone gain don't count, but how you vary them does.
6. **Compare with the envelope** (`envelope.py`). The same measurements exist for K = 6 good
   readings of the same text. For each word and feature, the envelope runs from the lowest to
   the highest good value, widened by a small measurement margin.
   - The deviation d is how far outside that range you are, in units of the typical envelope
     width; inside the range, d = 0.
   - Missed emphasis is only checked at "consensus stress points", where at least ¾ of the
     good readers peak.
   - A missing pause is only checked where every good reader paused.
7. **Find regions** (`detect.py`): consecutive words with high d form a flagged region
   (hysteresis, one threshold per flaw type). Each region gets one of six flaw types: pace
   (rushed/dragging), missing pause, misplaced pause, monotone, missed emphasis, volume fade.
8. **Explain and score.** Each flag gets a template explanation with measured numbers, for
   example: "Word 43: pause after 'near' 0.00 s; the good renditions spanned 0.18–0.98. Pause
   after 'near'." Six rubric scores (0–10) shrink with the size and length of the flagged
   regions. No language model judges anything.
9. **Report.** Envelope overlay chart (your line against the grey good-reader band), flaw
   cards, rubric table, A/B playback (your words against a good reader's same words), and a
   JSON report with a hash. Identical input always gives byte-identical output.

### Main parts of the project

| Part | What it does | Where |
|---|---|---|
| Analysis pipeline | Steps 2–9 above | `cadence/pipeline.py` and the modules it calls |
| Dataset factory | Downloads public-domain readings, crops and aligns them, picks the good set | `scripts/fetch_librivox.py`, `scripts/build_refs.py` |
| Flaw injector | Builds "ladders": 6 flaw types × 5 severities injected into a good reading with Praat PSOLA, plus null-edit controls (processed, unchanged) and exact time labels | `cadence/inject.py`, `scripts/build_ladders.py` |
| Labels and validation | Exports every label and checks timestamps, lengths, clicks and measured effects | `cadence/labels.py` (`cadence labels`) |
| Calibration | Fits thresholds, margins, severity map and score weights on **T1 only** | `cadence/evaluate.py` |
| Evaluation | Scores B0 (generic speaking rules), B1 (one reference) and B2 (the envelope) on T2–T8 (T7/T8 held out): Matching Score, edge error, false alarms per minute, equal-false-alarm sweep, ablations, robustness | `cadence/benchmark.py`, `scripts/robustness.py` |
| Human studies | Reader ranking (3 raters), listening test (5 listeners), natural takes with annotations | `cadence/human.py` (`cadence human`, port 7861), `cadence/natural.py` |
| Dashboard / API | Gradio UI (port 7860), FastAPI `POST /analyze`, CLI `cadence …` | `cadence/app.py`, `cadence/api.py`, `cadence/cli.py` |
| Bookkeeping | Inventory, status checklist, before/after comparison | `cadence inventory`, `cadence status`, `cadence compare` |

### Data at a glance

| Text | Content | Readings | Role |
|---|---|---|---|
| T1 | *Sea Fever* | 24 | Calibration only |
| T2 | *Stopping by Woods* | 23 | Test |
| T3 | Gettysburg, closing | 19 | Test |
| T4 | Gettysburg, opening | 19 (same readers as T3) | Test |
| T5 | FDR "Day of Infamy" | 2 | Blocked: needs ≥ 2 teammate takes |
| T6 | Kipling, *If—* (2 stanzas) | 17 (15 before the rebuild) | Test; used once for v2, so now development (no shared speakers) |
| T7 | SAA "Please Call Stella" (12 India-born speakers, 2 each Hindi/Bengali/Telugu/Tamil/Marathi/Malayalam) | 12 | **Held-out Indian** (added after v3 design; evaluated once; CC BY-NC-SA 4.0, separate subset) |
| T8 | Tagore *Fruit-Gathering* XVIII (LibriVox 17632) | 16 | **Held-out Indian-authored text** (added after v3 design; evaluated once; public domain; readers not confirmed Indian-accented, some also read T1–T4) |

All audio is public domain except T7 (CC BY-NC-SA 4.0); TED/TEDx is blocked by its licence. Good
readers are still ranked provisionally by aligner confidence until the 3-rater human ranking is
done; for T7 that ranking left out both Hindi speakers. Dataset v3 (default) places missed-emphasis
targets only at perceptible consensus stress points; 443 synthetic clips in total. Public copy:
https://huggingface.co/datasets/Vedant1605/cadence-contrastive-speech (`public_domain`,
`saa_indian_nc_sa`).

### Detector versions

| Version | What it is | Where |
|---|---|---|
| v1 | Absolute channels; any positive prominence counts as stress | Frozen in `results/frozen_v1_2026-10-14/`; reproducible with params flags off |
| **v2 (shipped)** | Adds self-relative pace/monotone channels and perceptible stress points (≥ 1.5 st / 1 dB); rubric λ pooled across dimensions | `data/params.json` (B2) and `data/params_B1.json` (B1 fallback) |
| v3 (built, **not shipped by rule**) | Phrase-level pace (`rate_phr`) and monotone (`pitch_spread_phr`) channels replace the word-level self-relative ones; phrase regions trimmed to the words that deviate themselves | `Config(phrase=True)`; lost the pre-registered `benchmark.ship_decision` (T1 38% vs 40%; won only T8) |

On dataset v3, B2 (v2) scores 44/35/40/27/27/28% on T2/T3/T4/T6/T7/T8 (`results/results.md`). It
beats B1 on T2–T4 and T7, ties T8 and loses T6 (27 vs 29%). Missed emphasis is detected again
(60/20/0/20% on T2/T3/T4/T6).

### Using the dashboard correctly

- Open **http://localhost:7860** on the Mac running Cadence. The microphone only works on
  `localhost` or HTTPS, not on `http://<LAN IP>`.
- The default exercise is **T4** (Gettysburg, opening), with T3 next to it. Poetry (T1/T2/T6)
  is behind "Show research benchmark texts". T5 is shown as pending.
- The **Demo** tab plays a known rushed-pace edit on T3 ("that we here highly", severity 4) and
  verifies the detection live (`data/demo/demo_T3.json`).
- "Comparison method" switches to the B1 single-reference fallback, which uses its own
  calibrated thresholds.
- Pick the text, read the passage shown on the right **from its first word to its last**
  (T2 begins "Whose woods these are…"; the title is not part of it), then click **Analyze**.
- The page runs top to bottom as three steps: (1) the passage, shown with its line breaks;
  (2) record or upload; (3) Analyze. Results (summary, rubric, flaw cards, chart, A/B, JSON)
  appear only after an analysis. Analyze lists only texts with an envelope (T1–T4).
- A recording that isn't mostly the selected passage is rejected, with the words that were
  heard shown in the error.

## 2. Current state (summary)

| Area | Status |
|---|---|
| Pipeline: preprocess → align → features → envelope → regions → explain → scores | Done |
| Dataset v3: 132 readings (T1 24, T2 23, T3 19, T4 19 = same readers as T3, T5 2, T6 17, T7 12, T8 16) plus 443 synthetic clips (T1 63, T2 65, T3 70, T4 65, T6 65, T7 55, T8 60) | Built; T5 blocked (< 4 renditions); recordings stay local (gitignored) |
| Public dataset | https://huggingface.co/datasets/Vedant1605/cadence-contrastive-speech, subsets `public_domain` and `saa_indian_nc_sa`. Repo public; at the time of the docs pass (2026-10-14) the audio upload was still in progress |
| Labels export and validation (`cadence labels`), inventory (`cadence inventory`) | Done: 476 label rows; `data/labels/validation.json` |
| Licensing docs, TEDx candidates (not downloaded), consent form | Done (`docs/DATA_LICENSING.md`, `data/sources/`, `data/consent/`) |
| Baselines B0 (generic norms), B1 (single reference) and B2 (envelope) | Done |
| Detector v3 (phrase channels) vs v2: pre-registered ship rule `benchmark.ship_decision` | Done: **v2 ships** (v3 lost T1 38% vs 40%; won only T8) |
| Ablations (K, normalization, null-edit margin, relative channels, stress floor, v1 design, other candidate), τ sweep, equal-FA tables | Done |
| Robustness (noise 20/10 dB, MP3 64k, telephone band, wrong word) | Done on T4, T6, T7 (`results/robustness_T*.json`) |
| Severity-gradient evidence figures | Done (`scripts/gradient_figures.py` → `docs/figures/`, `results/gradient.json`) |
| Gradio dashboard (analyze, A/B, dataset explorer, evidence, Demo tab on T3) | Done |
| FastAPI `POST /analyze`, CLI `cadence …` | Done |
| Listening-test and reader-ranking tools (`cadence human`) | Built; **no human data yet** |
| Human-data import: perceived-severity calibration, natural takes (`cadence natural`), `cadence status`, `cadence compare` | Done and fixture-tested; awaiting real data |
| Frozen results for comparison | `results/baseline_2026-10-13/`, `results/frozen_v1_2026-10-14/`, `results/frozen_v2_2026-10-14/` |
| Technical report (2,798 words + 4 figures), data card, README | Done for dataset v3 |
| Reproducibility | From-scratch rebuild reproduced all 371 v2 label rows' clip ids and timestamps; 29 rows' effect sizes drifted (median 1.4%, max 21%) — `results/rebuild_check_2026-10-14.md`; `rerun_check` passes; CI, Dockerfile, uv.lock |
| GitHub repo | `main` public; this work is on branch `scoring-push` (worktree `Cadence-v3`), not pushed |
| YouTube video, Devpost page | **Not done** (needs the team) |
| Stretch: Azure baseline, WavLM rhythm, re-record pilot, LLM rephrasing | Not built |

## 3. Headline results (dataset v3, shipped detector v2; thresholds fitted on T1 only)

Source: `results/results.md`. MS = Matching Score (type correct, IoU ≥ 0.5); FA = false alarms/min
on good-vs-good pairs. T2–T6 are development texts; T7/T8 were added after v3 was designed and
evaluated once.

| Text | B0 MS / FA | B1 MS / FA | B2 MS / FA |
|---|---|---|---|
| T1 (calib) | 16% / 22.4 | 25% / 0.90 | 40% / 0.90 |
| T2 | 20% / 26.2 | 33% / 0.90 | 44% / 2.03 |
| T3 | 13% / 16.9 | 22% / 0.73 | 35% / 1.47 |
| T4 | 16% / 19.3 | 29% / 0.94 | 40% / 0.24 |
| T6 | 15% / 22.5 | 29% / 2.15 | 27% / 2.15 |
| T7 (Indian speakers) | 22% / 25.3 | 22% / 3.38 | 27% / 2.11 |
| T8 (Tagore) | 10% / 14.5 | 28% / 2.47 | 28% / 2.28 |

- **Dataset v3 vs v2 (same detector):** B2 T2 40→44%, T3 30→35%, T4 35→40%, T6 23→27%
  (`results/frozen_v2_2026-10-14/results.md`). Missed-emphasis recall 60/20/0/20% on T2/T3/T4/T6
  (was 30/0/0/0%).
- **Ship decision:** v3 vs v2 MS — T1 38 vs 40, T2 35 vs 44, T3 27 vs 35, T4 20 vs 40, T6 27 vs 27,
  T7 27 vs 27, T8 38 vs 28. v2 ships.
- **Equal FA (≤ 1/min), B1 vs B2:** T2 33 vs 33, T3 22 vs 20, T4 29 vs 40, T6 16 vs 5, T7 11 vs 13,
  T8 18 vs 8. The envelope is not universally better; B1 stays as a calibrated fallback.
- **Robustness (B2, severities 3/5):** clean → 10 dB noise: T4 64→32%, T6 45→23%, T7 39→22%;
  MP3 64k and wrong word unchanged except T7 MP3 39→33%.
- **Demo:** T3 rushed pace L4, "that we here highly": B2 IoU 0.975 with 1 flag; B1 misses; B0 19
  flags, none matching (`data/demo/demo_T3.json`).

Older results: `results/frozen_v2_2026-10-14/` (detector v2 on dataset v2) and
`results/frozen_v1_2026-10-14/` (v1). Generated recordings and human-study assets are not in Git.

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

13. **New texts (session 5b).**
    - **T4:** Gettysburg opening, reusing T3's downloads.
    - **T5:** FDR "Day of Infamy" (Commons PD original, NARA 10611614, sha1-checked) plus 1
      LibriVox reading. Gated by `MIN_GOOD = 4`.
    - **TED/TEDx:** blocked. The policy (CC BY-NC-ND 4.0) forbids derivatives and truncated
      clips, and each talk is a single performance anyway.
    - Other multi-rendition public-domain speeches searched (LibriVox API, archive.org): none had
      ≥ 4 renditions except Gettysburg. Julius Caesar (Antony's oration) has only 2 full-cast
      versions.
14. **Span rule v2** for new texts: misplaced pauses only between words ≥ 0.15 s. T1–T3 stay on
    rule 1, frozen, so results are unchanged. The validator found one T1 span whose word
    attribution is off by one (time correct).
15. **Speaker leakage.** T1's good set shares no speaker with any test text. Overlaps exist only
    among non-reference readers (T1–T3/T4: 2) and between test texts (T3–T4: all 19). T8 (Tagore,
    LibriVox) shares readers with T1 (1: lee ann), T2 (3: bruce kachuk, david lawrence, larry
    wilson), T3 and T4 (2 each: david lawrence, triciag); `data/inventory.json` → `speaker_overlap`.
    T6 and T7 share no speaker with any text.
16. **Regression rule.** Adding a text must leave `data/params.json` and every T1–T3 result
    byte-identical. Verified in session 5b.

## 5. Layout

```
cadence/        package: audio, align, features, envelope, detect, inject, pipeline,
                baselines, metrics, evaluate, benchmark, app (Gradio), api (FastAPI),
                human (listening test + ranking), cli, data/{texts,librivox}
scripts/        fetch_librivox, build_refs, build_ladders, robustness, make_demo, rerun_check
data/           demo/, params.json, DATA_CARD.md; raw/, refs/, ladders/, listening/ and
                rankings/ are generated/local assets and gitignored
results/        results.json, results.md, robustness_T*.json, gradient.json, rerun_hashes.json,
                rebuild_check_2026-10-14.md, frozen_v1_/frozen_v2_2026-10-14/
docs/           technical_report.md, figures/, DATA_LICENSING.md
tests/          test_core.py, test_benchmark.py, test_figures.py (51 tests, passing)
logs/           run logs
```

## 6. How to run

```bash
uv sync --extra dev
uv run cadence all        # fetch → refs → ladders → evaluate (long: run with nohup, ≤ 3 workers)
uv run cadence app        # dashboard :7860
uv run cadence human      # listening test + reader ranking :7861
uv run cadence analyze file.wav --text T2
```

Long jobs: run with `nohup` and ≤ 3 workers. Earlier sessions were killed (exit 137) under
memory pressure.

## 7. Pending / next steps

- [ ] Human reader ranking: 3 teammates rank all readings (`cadence human`), then `cadence refs && cadence ladders`, check with `cadence status`.
- [ ] Listening test: 5 listeners on the rebuilt ladders (perceived-severity calibration on T1).
- [ ] Natural takes: teammate recordings plus 2 independent annotators (`docs/human_data_protocol.md`).
- [ ] T5: ≥ 2 (ideally 4) teammate takes of "Day of Infamy" plus consent forms.
- [ ] Confirm by listening whether any T8 (Tagore) reader is Indian-accented.
- [ ] Confirm the Hugging Face audio upload finished (repo is public; upload was in progress during the docs pass).
- [ ] YouTube video (3–10 min) and the Devpost page (Track C, all teammates).
- [ ] Merge `scoring-push` into `main` and push (needs the user's go-ahead).

## 8. Change log

- **2026-10-14 (session 10, Task 8 fix round 1): judge-facing wording.**
  - DATA_CARD role table matches the README (T2–T4 development, T6 no longer untouched, T8 Indian-authored
    text with unconfirmed accents). §4.15 lists T8's reader overlaps with T1–T4.
  - New tracked `results/rebuild_check_2026-10-14.md` (W0 rebuild facts), cited instead of the gitignored ledger.
  - Report/README: v2 diagnosis figures marked as carried over; equal-FA summary includes T3's slight loss; headline
    tables note per-method operating points (bold removed where B2 does not win at equal FA); ship rule says
    "≥ 2 non-calibration texts (T2–T8)" and discloses the T3/T4 shared-reader caveat; 476 rows vs 427 flaw labels.
  - §5/§6 updated (51 tests, robustness_T*.json, no stale runtime). Report 2,798 words.

- **2026-10-14 (session 10, scoring push, consolidated): dataset v3, Indian held-out texts, pre-registered v3 decision, final docs.**
  - **W0 reproducibility:** from-scratch fetch → refs → ladders reproduced all 371 v2 label rows with identical
    clip ids and timestamps; 29 rows' measured effect values differed (median 1.4%, max 21%). T6 now has 17
    readings (2 downloads that failed earlier succeeded).
  - **Dataset v3** (`3cfcd11`, `f6f95ca`): missed-emphasis targets only at perceptible consensus stress points.
    Fixes the structural 0% emphasis recall (targets the v2 detector could not see).
  - **Detector v3** (`b0c89f8`…`8f175b8`): phrase-level pace/monotone channels, trimmed to deviating words, behind
    `Config(phrase=True)`.
  - **T7/T8** (`9ba5128`, `94cb0e1`): SAA "Please call Stella" (12 India-born speakers, CC BY-NC-SA 4.0) and Tagore
    *Fruit-Gathering* XVIII (16 LibriVox readers, PD). T7 good set (aligner confidence) has no Hindi speaker.
  - **Evaluation** (`936fd40`, `f19da7b`, `16bde30`, `bdb5500`, `0ff72c4`): froze v2 results; pre-registered
    `benchmark.ship_decision` chose **v2** (v3 lost T1 38 vs 40%, won only T8).
  - **Evidence** (`8ec9cae`, `142dd40`, `6b4e6cd`): four severity-gradient figures, regenerated for dataset v3.
  - **Robustness and demo** (`bd13b21`, `18ebd08`, `58b7357`): robustness on T4/T6/T7; rerun hashes re-stored;
    dashboard Demo tab switched to the T3 rushed-pace case (B2 IoU 0.975, B1 miss, B0 19 flags) and
    `WRONG_WORD` added for T7/T8. This entry also records commit `18ebd08`, whose review finding
    ("project context.md not updated") was deferred to this pass.
  - **Published** the dataset at https://huggingface.co/datasets/Vedant1605/cadence-contrastive-speech
    (subsets `public_domain`, `saa_indian_nc_sa`).
  - **Docs pass:** README (dataset link, v3 results, T7/T8 data table, reproduction commands), technical report
    rewritten (2,798 words + 4 figures), DATA_CARD (v3, HF link, counts), this file. Fixed the misleading
    `exec_module` comment in `tests/test_benchmark.py`.

- **2026-10-14: Task 6 fix round 1 — data-driven titles; captions describe measurements (session 10).**
  - `fig_gradient_matching`: title now discovers held-out text IDs from data (no hard-coded range).
  - Figure A: legend removed; direct endpoint labels remain as the sole identity channel.
  - `extract_timing_errors` docstring corrected to match actual return value.
  - README and technical_report captions rewritten to describe what is measured, not comparative claims; hard-coded text-id claims and counts removed.
  - 9 tests pass.

- **2026-10-14: Task 6 — Severity-gradient evidence figures (session 10).**
  - Added `scripts/gradient_figures.py`: data-driven, re-runnable with one command.
  - Added optional dependency group `report` (matplotlib) to `pyproject.toml`.
  - Outputs: `docs/figures/gradient_matching_by_severity.png`, `gradient_by_type.png`, `false_alarms_null_edit.png`, `label_timing_error.png`, `results/gradient.json`.
  - Added `tests/test_figures.py` (9 tests, data-extraction only, no plotting).
  - Embedded 4 figures with captions in `README.md` (Evidence section) and `docs/technical_report.md` (§4a).
  - All 50 tests pass.

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
- **2026-10-13 (session 5b): dataset expansion toward public speaking.** Uncommitted; the last
  commit is `2afabec` from the parallel session.
  - Audited the sources; found and fixed the count (87 recordings, inventory in `data/inventory.*`).
  - TED policy checked: CC BY-NC-ND 4.0, so TEDx is blocked and listed as candidates only.
  - Added T4 (Gettysburg opening, 19 readings, full pipeline, 70 clips) and T5 (FDR original
    plus LibriVox; awaiting teammate takes).
  - Fetcher: direct sources with licence, provenance, sha1 and a Wikimedia-compliant User-Agent;
    reuse of other texts' downloads; `team_*` takes.
  - New `cadence labels` (export plus 7 automated checks) and `cadence inventory` (incl. leakage check).
  - Benchmark and report generalized to all eligible held-out texts. Robustness takes `--text`
    and adds a telephone-band condition; its tables are generated from JSON, never appended.
  - Validator fixes: crossfade-aware length model; locate-based attribution check.
  - Natural takes can't double as reference candidates.
  - Regression check passed (params and T1–T3 identical). Rerun hashes still match. 14 tests pass.
  - The first probe of Wikimedia sent the user's email in a User-Agent header (one request);
    disclosed to the user, and removed from the code.
- **2026-10-13 (session 6): dashboard upload fix.** The user reported that an uploaded 7 s
  clip showed 0:00 and would not play.
  - Cause: the file was a WhatsApp voice note (`.opus`, Ogg-Opus), which Safari cannot play.
    Python also maps `.m4a` to `audio/mp4a-latm`, which browsers reject.
  - Fix: `app.to_playable_wav` transcodes every upload to 16-bit PCM WAV on `.upload`.
    Analysis is unchanged, since it already decodes with ffmpeg.
  - Also found: the clip did not read any Cadence text (ASR heard unrelated speech). New
    `align.TextNotFound` guard: analysis refuses recordings where < 50% of the selected text's
    words are heard, and the dashboard shows the reason.
  - Verified: the user's clip is rejected (1%); demo clips and real readings of T1–T5 (incl.
    FDR) pass; 14 tests pass; rerun hashes unchanged; dashboard restarted (logs/app.log).
- **2026-10-13 (session 6b): dashboard usability and overview.**
  - The user's "exact T2 reading" was a 3 s WhatsApp note containing only the **title**
    ("stopping by woods on a snowy evening"). The guard rightly rejected it (4% of 108 words),
    but the dashboard never showed what to read.
  - Added a passage panel: the full text, word count, and the good readers' median duration
    (T2: 108 words, about 44 s).
  - The error now states the recording length, what was heard, and how the passage begins.
  - Microphone is now the default input (`format="wav"`); recordings pass through the same WAV
    conversion; a note explains that browsers allow the mic only on localhost or HTTPS.
  - Verified on the live app (restarted): title clip → clear error; full T2 reading → analyzed,
    same hash `710be9d40782ec51`; page config shows sources `['microphone', 'upload']`.
  - Added section 1b, "How Cadence works", to this file.
- **2026-10-13 (session 7): web page layout and recognition-tolerant text check.**
  - **Bug:** the user's full 40 s T2 reading (WhatsApp, non-native accent) was rejected: 41% of
    words matched exactly, against the 50% threshold. The recognizer mishears accented phone
    speech ("whose words athese are writing i know").
  - **Fix:** coverage is now measured on letters, threshold 0.40, documented in `align.py`.
    Measured: the user's reading 0.63; the same reading against other texts 0.08–0.21;
    unrelated speech 0.03–0.10; title only 0.06; all 87 reference readings ≥ 0.89
    (FDR 1941 lowest).
  - **Layout** (`app.py`):
    - numbered steps;
    - passages shown with line breaks (new `texts.DISPLAY` for the poems, same words as the
      scored text, verified);
    - a serif reading card with no scroll cap;
    - a smaller font on phones;
    - the record/analyze column sticks on desktop;
    - K moved into "Advanced";
    - results hidden until an analysis, with a summary line;
    - the JSON report and hash moved into an accordion;
    - system fonts, no web fonts;
    - Analyze lists only texts with ≥ 4 good renditions.
  - **Wording:** pause explanations say "none of the six good renditions paused there" instead
    of "spanned 0.00–0.00". Explanation text only; scores and flags are unchanged.
  - **Verified** with headless Chromium driving the real page (upload → Analyze) on the user's
    own reading, at 1440 px and 390 px: 5 flagged regions, A/B audio plays. 14 tests pass;
    rerun hashes unchanged.
- **2026-10-14 (session 8): detector v2, untouched final test, speech-first dashboard, demo.**
  - Froze the complete v1 state in `results/frozen_v1_2026-10-14/`.
  - **Diagnosed:**
    - *Pace and monotone* (on T1): readers' overall tempo differs by up to 1.8×, so the
      absolute rate envelope was 0.85 log2 wide; self-relative it is 0.31.
    - *Missed emphasis:* imperceptible 0.1–0.3 dB "peaks" made fake consensus stress points.
    - *T4 flags outside labels:* the source reader's own style repeated on each clip; only
      0.05/min was attributable to the edits.
  - **Implemented** (flags, v1 reproducible):
    - self-relative channels and the stress floor;
    - pooled rubric λ (the per-dimension fit had exploded to pacing 68 and emphasis 86);
    - edit-attributable false alarms and per-type precision;
    - equal-false-alarm tables.
  - **Added T6** (Kipling, 15 readers) after freezing v2, and evaluated it once. B1 ≥ B2 on
    T6, and v2 ≤ v1 on T6. Reported honestly; B1 shipped as a calibrated fallback mode.
  - **Dashboard:** T4 default (lowest false alarms under v2), T3 alongside, poetry behind a
    checkbox, context and expected duration shown, T5 pending, Demo tab, comparison-method radio.
  - **Demo** (`cadence demo`), chosen from computed results: T4 rushed pace, severity 4.
    B2 IoU 0.97 (8/22 ms edge errors), B1 misses, B0 IoU 0.16. Audio copied into `data/demo/`.
  - **Human UI** restarted: the :7861 process dated from before the session-4 fixes. No human
    data had been collected.
  - **Robustness v2:** T4 clean 54%, 10 dB noise 25%; T6 38% → 25%. The v1 robustness files
    were retired to the frozen folder.
  - **Tests:** 16 pass (2 new for v2). Rerun hashes re-stored for v2 and identical across runs.
    Technical report rewritten at 1.7k words.
  - **Verified** in headless Chromium at 1440 and 390 px: T4 default, analysis, 6 scores, JSON,
    unrelated-speech rejection, Demo tab.
- **2026-10-14 (session 9): published the current project state to GitHub.** Pushed the
  detector-v2 implementation and evaluation, T6 untouched-test results, T4 demo, licensing and
  label metadata, and refreshed project documentation to `main`.
- **2026-10-14 (session 10): scoring-push plan for the final submission.**
  - Mapped Cadence against the Track C weighted criteria; plan in
    `docs/superpowers/specs/2026-10-14-track-c-scoring-push-design.md` (W0–W6).
  - Root cause of 0% missed-emphasis recall: ladders target v1 stress points, the v2 detector
    reads only perceptible ones. Fix chosen: dataset v3 rule (targets = perceptible consensus
    stress points). Pace/monotone: phrase-level channels (detector v3, T1-fitted).
  - This checkout had no audio; regenerating fetch → refs → ladders (nohup, 3 workers,
    `logs/regen_2026-10-14.log`). Indian-speaker data sources under deep research
    (`research_notes/`, `reports/`). Hugging Face login done for dataset publishing.
- **2026-10-14 (session 10, Task 1): dataset v3 emphasis rule.**
  - Added `stress_rule: int = 1` param to `inject.choose_spans`; with `stress_rule=2` the
    fallback that admits any (imperceptible) consensus stress point is disabled.
  - `build_ladders.py`: `--dataset {2,3}` flag (default 3). Dataset 3 passes the perceptible
    mask (`env.stress_pitch_p | env.stress_loud_p`) and `stress_rule=2`; dataset 2 reproduces
    the legacy behaviour byte-for-byte. `"dataset_version"` key added to every clip dict.
  - `data/DATA_CARD.md`: Version history section added.
  - New test: `test_emphasis_targets_perceptible_only` in `tests/test_core.py`.
- **2026-10-14 (session 10, Task 2): phrase segmentation and phrase-level rate / pitch-spread features.**
  - `features.py`: added `word_basics(words)` returning `syl`/`dur`; `UNITS` updated with
    `rate_phr`/`pitch_spread_phr`; `word_features` now emits `syl` and `dur`.
  - `envelope.py`: `PHRASE_FEATURES`, three new phrase channels appended to `CHANNELS` (indices
    11–13; v1/v2 indices unchanged); `TRANSFORM` updated; `phrase_ids(pauses)` and
    `with_phrases(feats, pid)` added; `Envelope.phrase_id` field (last, default None); `build`
    computes phrase_ids from ref pauses and applies `with_phrases` to all refs; `deviations`
    gains `phrase: bool = False` — phrase channels give zeros by default (byte-identical to v2),
    REL_FEATURES channels are zeroed when `phrase=True`.
  - `evaluate.py::_record`, `pipeline.py::load_record`: backfill `syl`/`dur` from words before
    `add_derived`, so existing JSON records without those keys still work.
  - `tests/test_core.py`: `feats()` fixture initialises PHRASE_FEATURES to NaN (no syl/dur);
    four new tests: `test_phrase_ids_consensus`, `test_phrase_ids_no_consensus_pause`,
    `test_word_basics_backfilled`, `test_phrase_feats_nan_safe`. 15 tests pass, 0 warnings.
- **2026-10-14 (session 10, Task 2 Fix Round 2): phrase-median normalization corrected.**
  - `envelope.py::with_phrases`: normalization now uses `np.nanmedian` over one value per
    phrase (first element per phrase, since rate/spread is broadcast-constant within a phrase).
    Previously used `np.nanmedian` of the full per-word broadcast array, which is word-weighted;
    the longer phrase dominated the median and would yield rate_phr ≈ 1.0 for unequal splits.
  - `tests/test_core.py`: `test_deviations_phrase_gating` reworked with 4+4+12-word phrases;
    the 12-word phrase is the sped-up one — asserts rate_phr > 1 and d > 0 there.
    `test_with_phrases_normalizes_by_phrase_median` added: 2+8-word split with rates 2.0/4.0
    → phrase-median = 3.0 → rate_phr = 2/3 and 4/3 (not 0.5/1.0 as word-median would give).
    `_phrase_ref` helper signature simplified (removed `tempo`/`pause_after_w4`, supports
    `pause_idxs` tuple for multi-boundary refs). 25 tests pass, 0 RuntimeWarnings.
- **2026-10-14 (session 10, Task 3): detector v3 — phrase channels, trimmed regions, explanations.**
  - `detect.py`: `Params.phrase_channels: bool = False`; `detect` passes `phrase=` to
    `deviations`; a region whose dominant channel is a phrase feature is trimmed to the words
    whose word-level self-relative deviation (same side: `rate_rel` for `rate_phr`,
    `pitch_range_rel` for `pitch_spread_phr`) is positive, else the whole phrase is kept;
    start/end/d_mean/d_max/severity use the kept words. With the flag off, output is unchanged.
  - `explain`: adds phrase features to x when the envelope has phrases; new texts "phrase
    speaking rate relative to your own pace" and "phrase pitch movement relative to your own".
  - `evaluate.py`: `Config.phrase: bool = False`, name suffix ", phrase channels", `calibrate`
    passes `phrase_channels=cfg.phrase`. No CLI flag (evaluate exposes no variant flags).
  - Tests: four new (rushed phrase flagged and trimmed, phrase explanation, flag off never
    yields phrase regions, flattened phrase flagged as monotone). 29 tests pass, 0 warnings.
  - No calibration / evaluation run yet (long job; needs audio data).
- **2026-10-14 (session 10, Task 3 fix round 1): phrase trimming pinned.**
  - `detect.py`: trimming now filters only words whose winning channel is a phrase channel;
    words in the region won by another channel (e.g. absolute `rate`) are always kept.
  - Tests: exact trimmed spans pinned (pace 12-16, monotone 12-19); `rate_phr` explanation text
    asserted; new `test_v3_phrase_trim_falls_back_to_full_phrase` (10-19 kept) and
    `test_v3_phrase_trim_keeps_words_won_by_other_channels` (11-16, not 14-16). Checked that
    disabling trimming or filtering every word makes tests fail. 31 tests pass, 0 warnings.
- **2026-10-14 (session 10, Task 4): Indian-speaker held-out texts T7 and T8 registered.**
  - `cadence/data/texts.py`: added T7 (SAA "Please Call Stella", 12 India-born speakers, CC
    BY-NC-SA 4.0, role "test-indian", span_rule 2) and T8 (LibriVox Tagore *Fruit-Gathering*
    XVIII, 16 readers, public domain, role "test-indian", span_rule 2). Added DISPLAY entries
    for both texts. Added comment that T7/T8 were added 2026-10-14 after detector v3 was
    designed; held out, never used for calibration.
  - `scripts/fetch_librivox.py`: added argparse with `--texts T7 T8` optional argument (default
    = all texts); added `**s.get("meta", {})` to sources rows to pass through L1/birthplace/sex/
    age/english_onset_age for T7 speakers.
  - `docs/DATA_LICENSING.md`: added T7 row (CC BY-NC-SA 4.0, non-commercial, share-alike);
    added T8 (public domain); added T7 speaker L1+birthplace table; added note that T7 audio
    and all derived clips are CC BY-NC-SA 4.0 and must be published as a separate subset.
  - `data/DATA_CARD.md`: added T7 and T8 rows with role "held-out Indian" to texts table;
    added T7 speaker table; added T8 section.
  - T8 ID-match check: staged IDs (lv17632_NN_slug) match exactly what `reader_id()` in
    `cadence/data/librivox.py` would generate from the LibriVox API reader names — IDs match.
  - New test `test_t7_t8_registered`: T7 and T8 in `test_texts()`, T7 has 12 sources each
    with 40-char sha1, T7 text starts with "Please call Stella", T8 has librivox_ids [17632].
  - 32 tests pass, 0 RuntimeWarnings.
- **2026-10-14 (session 10, Task 5): Benchmark: detector v3 candidate with pre-registered ship rule.**
  - `cadence/benchmark.py`:
    - `MAIN = E.Config(phrase=True)` (detector v3); `"v2 detector (no phrase channels)": E.Config()`
      added to ABLATIONS.
    - `STATUS_NOTE` updated to reflect dataset v3, v3 candidate vs v2 with a pre-registered automatic
      ship rule, T2–T6 development status, T7/T8 added post-v3-design, frozen v1 and v2 result dirs.
    - `ship_decision(v3, v2, fa_cap=2.0)`: pure function taking per-text result dicts; returns
      `{"ship": "v3"|"v2", "t1": {...}, "wins": [...], "losses": [...], "fa_violations": [...], "reason": str}`.
      Rule: ship v3 iff v3 MS > v2 on T1 AND on >= 2 held-out texts, AND v3 FA/min <= fa_cap on every
      held-out text where v2's is <= fa_cap.
    - Ablation loop now runs `["T1", *TEST]` (was `TEST` only; cheap, reuses calibrated params; needed
      for ship_decision).
    - `main()`: runs ship_decision after all runs; saves winner's params to PARAMS; b1.lam copied from
      winner. If v2 wins, B2 headline row re-run with v2 config; v3 stashed under ablations as "v3
      detector (phrase channels)". `out["ship_decision"]` written to results.json.
    - `markdown()`: "### Ship decision (v3 vs v2, dataset v3)" section added with T1 scores, wins/losses,
      FA violations and reason.
  - `tests/test_core.py`: three new `ship_decision` tests — v3 wins (T1 + 2 held-out, no FA violation)
    → "v3"; v3 wins T1 but only 1 held-out → "v2"; v3 wins everything but FA cap exceeded on one text
    where v2 is ok → "v2". 35 tests pass, 0 RuntimeWarnings.
  - Long jobs (refs, ladders, evaluate) NOT run by this task; controller runs them.
- **2026-10-14 (session 10, Task 5 fix round 1): Two-phase ship decision; report relative to shipped detector.**
  - `cadence/benchmark.py` fully restructured into two phases:
    - **Phase 1 (decide):** calibrate V3 = `E.Config(phrase=True)` and V2 = `E.Config()` with `full=True`;
      run each on `["T1", *TEST]`; call `ship_decision`; set `SHIP` / `OTHER`.
    - **Phase 2 (report):** call `report_configs(SHIP, OTHER)` for METHODS and ABLATIONS; calibrate any
      new configs (reusing phase-1 params by key); run methods on `["T1", *TEST]` (reuse phase-1 for SHIP/OTHER);
      run ablations on `TEST` only (reuse phase-1 for OTHER). Every downstream analysis (sweep, equal_fa,
      natural_spectrum, severity_vs_listeners, params save) uses `SHIP`.
  - `report_configs(ship, other)`: pure helper returning (METHODS, ABLATIONS).
    - METHODS: B0, B1 = `replace(ship, k=1)`, B2 = ship (B1's phrase= matches SHIP).
    - ABLATIONS: K=1/2/4; norm off/zscore; no margin; without relative channels; without stress floor;
      v1 detector = `replace(ship, relative=False, stress_floor=False, phrase=False)`;
      "other candidate" row = OTHER. No "K=all" (B2 already shows it).
  - `ship_decision`: added `_ms()` / `_fa()` helpers — non-finite or None MS counts as v3 loss; non-finite
    v3 FA counts as FA violation (unless v2 FA is also non-finite). Added `per_text` key to return dict.
  - `markdown()`: ship decision section now includes a per-text table (text, v3 MS, v2 MS, v3 FA/min, v2 FA/min,
    outcome). STATUS_NOTE: restored "T3 and T4 are two passages read by the same 19 readers" note; added
    "T3+T4 can jointly supply two of the required wins."
  - MAIN module alias kept (no external imports found by grep; kept for documentation).
  - Tests: 4 new — `test_ship_decision_v3_loses_t1_wins_all_held_out` (T1 loss → "v2");
    `test_ship_decision_none_nan_handling` (NaN MS = loss, NaN FA = violation);
    `test_report_configs_ship_v3` (B1 phrase=True, v1 phrase=False, other=v2 row present, no K=all);
    `test_report_configs_ship_v2` (B1 phrase=False, other=v3 row present). 39 tests pass, 0 warnings.
