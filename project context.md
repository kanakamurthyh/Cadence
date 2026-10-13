# Project context: Cadence

> Living record of everything done on this project. Updated after every change.
> Last updated: 2026-10-14 (session 10: Task 2 phrase segmentation and phrase-level features implemented)

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
| Evaluation | Scores B0 (generic speaking rules), B1 (one reference) and B2 (the envelope) on held-out T2–T4: Matching Score, edge error, false alarms per minute, equal-false-alarm sweep, ablations, robustness | `cadence/benchmark.py`, `scripts/robustness.py` |
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
| T6 | Kipling, *If—* (2 stanzas) | 15 | **Untouched final test** (added after v2 was frozen; no shared speakers) |

All audio is public domain; TED/TEDx is blocked by its licence. Good readers are still ranked
provisionally by aligner confidence until the 3-rater human ranking is done.

### Detector versions

| Version | What it is | Where |
|---|---|---|
| v1 | Absolute channels; any positive prominence counts as stress | Frozen in `results/frozen_v1_2026-10-14/`; reproducible with params flags off |
| **v2 (shipped)** | Adds self-relative pace/monotone channels and perceptible stress points (≥ 1.5 st / 1 dB); rubric λ pooled across dimensions | `data/params.json` (B2) and `data/params_B1.json` (B1 fallback) |

v2 helped the development texts (T4 23 → 35% at 0.24 FA/min) but **not** the untouched T6: there
B2 v2 scores 23% at 2.15 FA/min, against B1 27% and the v1 design 27% at 1.43. Missed emphasis
is no longer detected (0%).

### Using the dashboard correctly

- Open **http://localhost:7860** on the Mac running Cadence. The microphone only works on
  `localhost` or HTTPS, not on `http://<LAN IP>`.
- The default exercise is **T4** (Gettysburg, opening), with T3 next to it. Poetry (T1/T2/T6)
  is behind "Show research benchmark texts". T5 is shown as pending.
- The **Demo** tab plays a known rushed-pace edit on T4 and verifies the detection live.
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
| Dataset: 87 readings (T1 24, T2 23, T3 19, T4 19 = same readings as T3, T5 2) plus 278 synthetic clips (T1–T4) | Built; T5 blocked (< 4 renditions); recordings stay local (gitignored) |
| Labels export and validation (`cadence labels`), inventory (`cadence inventory`) | Done: 296 label rows; `data/labels/validation.json` |
| Licensing docs, TEDx candidates (not downloaded), consent form | Done (`docs/DATA_LICENSING.md`, `data/sources/`, `data/consent/`) |
| Baselines B0 (generic norms), B1 (single reference) and B2 (envelope) | Done |
| Ablations (K, normalization, null-edit margin), τ sweep, robustness | Done |
| Gradio dashboard (analyze, A/B, dataset explorer, evidence) | Done. Microphone is the default input; uploads are converted to WAV; shows the passage to read; rejects recordings of the wrong text |
| FastAPI `POST /analyze`, CLI `cadence …` | Done |
| Listening-test and reader-ranking tools (`cadence human`) | Built and fixed; running on :7861; **no human data yet** |
| Human-data import: perceived-severity calibration, natural takes (`cadence natural`), `cadence status`, `cadence compare` | Done and fixture-tested; awaiting real data |
| Baseline frozen for before/after comparison | `results/baseline_2026-10-13/` |
| Technical report, data card, README | Done (`docs/`, `data/DATA_CARD.md`) |
| Reproducibility (byte-identical reruns, CI workflow, Dockerfile, uv.lock) | Done; rerun check passes |
| GitHub repo | Public project state pushed to `main`; branch tracks `origin/main` |
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

**T4 (held out, added in session 5b):**

| Method | Matching Score | FA/min |
|---|---|---|
| B0 | 15% | 19.3 |
| B1 | 17% | 0.47 |
| B2 | 23% | 1.65 |

- At below 1 FA/min, B2 does not beat B1 on T4 (12% @0.71 vs 17% @0.47).
- New failure mode: the ladder source sits outside its own envelope, giving 176 flags outside
  labels.
- Telephone-band robustness: T2 42 → 29%, T4 33 → 29%.

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
    among non-reference readers (T1–T3/T4: 2) and between test texts (T3–T4: all 19).
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

- [ ] Step 0: ≥ 2 (ideally 4) teammates record a rehearsed T5 take → `data/raw/T5/team_<name>_take1.wav` plus a consent form.
- [ ] Step 1: 3 teammates rank all 102 readings (T1 24, T2 23, T3 19, T4 19, T5 2 + team, T6 15); T1 and T4/T3 first.
- [ ] Step 2: `cadence refs && cadence ladders`, then check with `cadence status`.
- [ ] Step 3: 5 listeners take the listening test (on the rebuilt ladders).
- [ ] Step 4: teammate takes plus 2 independent annotators (protocol in `docs/human_data_protocol.md`).
- [ ] Step 5: `cadence evaluate`, robustness, make_demo, `rerun_check --store`, `cadence compare`.
- [ ] Phone-microphone robustness take.
- [ ] Improve pace and monotone detection: region-level rate, a stricter good set, WavLM rhythm.
- [ ] The demo clip's rushed pace is not detected; adjust the 0:50 demo segment or fix pace.
- [ ] Publish the dataset link separately; generated recordings and human-study assets are not in Git.
- [ ] W0–W6 of the scoring-push spec (rebuild, dataset v3, Indian texts, detector v3, gradient figures, HF publish, demo).
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
