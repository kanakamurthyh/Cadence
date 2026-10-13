# Cadence: judging a delivery against the range of good renditions

Track C, Contrastive Speech Analytics · technical report (max 6 pages)

## 1. Problem and claim

Competitive speakers get vague and inconsistent delivery feedback. Human raters of oratory
agree poorly (ICC 0.03–0.38 in 3MT_French; ρ = 0.47 in APSA). Existing tools judge against
generic norms, such as PowerPoint Speaker Coach's 100–165 wpm, or against a reference text
(Azure). Neither can tell a stylistic choice from a flaw.

Cadence flags a word only when the attempt leaves the range spanned by **several** strong
renditions of the same text, and it explains each flag in measured units.

The claim we test is modest: compared with a single reference, the envelope should find more
injected flaws at an equal false-alarm rate on good-vs-good pairs. We report every result,
including the ones that do not support it. **On our untouched final test it does not.**

## 2. Dataset construction

| Text | Readers | Role |
|---|---|---|
| T1 *Sea Fever* | 24 LibriVox | Calibration only |
| T2 *Stopping by Woods* | 23 | Held out (poetry) |
| T3 Gettysburg Address, closing paragraph | 19 | Held out (speech) |
| T4 Gettysburg Address, opening paragraph | The same 19 readers | Held out (speech); **not independent of T3** |
| T5 FDR "Day of Infamy", opening | Original 1941 recording + 1 reader | Pending: needs ≥ 4 renditions |
| **T6** Kipling, *If—* (two stanzas) | 15 (2 of 17 downloads failed) | **Untouched final test**: added after v2 was frozen, evaluated once |

**Licences.** All audio is public domain: LibriVox (PDM 1.0), and the FDR original is a US
federal work (NARA 10611614). TED/TEDx (CC BY-NC-ND 4.0: no edits or clips) is listed as
candidates only.

**Speaker overlap.** No reader used for calibration (T1's good set) appears in any test text.
T6 shares no speaker with any other text.

**Preparing each reading.**
- Decode with ffmpeg to 16 kHz mono at −23 LUFS.
- Locate the passage with wav2vec2 greedy transcription. Coverage is measured on letters, so
  accented or misheard speech still counts.
- Force-align the known transcript and snap word edges to silences.

**Good set.** The top 6 per text, **provisionally ranked by aligner confidence**. That is not
delivery quality; the 3-rater human ranking is pending.

**Synthetic ladders.**
- 6 flaw types × 2 spans × 5 severities, injected with Praat PSOLA into the top-ranked rendition
  from a fixed seed.
- Also built: null-edit copies of every good rendition, and compound clips.
- In total, 348 clips across T1–T4 and T6.

| Type | Edit | Severity 1 → 5 |
|---|---|---|
| Pace | PSOLA duration factor, pitch kept | ×0.9→×0.55 (rushed), ×1.1→×1.8 (dragging) |
| Missing pause | Silence shortened where **every** good reader pauses | 20→100% removed |
| Misplaced pause | Room tone inserted where **no** good reader pauses | 0.3→2.0 s |
| Monotone | Pitch compressed toward the span median | 80→10% of range kept |
| Missed emphasis | Peak flattened at a consensus stress point | 80→0% kept |
| Volume fade | Gain ramp held across the span | −3→−18 dB |

**Controls.**
- Every clip, the clean ones included, goes through the same PSOLA resynthesis.
- The edited rendition is never in its own envelope.

**Label validation** (`cadence labels`, 371 rows):
- Timestamps are inside the audio and word indices valid: all pass.
- Clip lengths match the stretch, cut and insert maths: all pass.
- Spliced joins: one borderline (1.02× the click threshold).
- 29 edges differ from an independent re-alignment by more than 100 ms. These are aligner
  error on faded or stretched speech; the analytic time map is verified by the length check.

## 3. Method

`preprocess → locate text → align → features → envelope → regions → type + explain → scores`

**Features (per word).**
- Articulation rate (5-word window).
- Pause after the word.
- Pitch range (3-word window, semitones).
- Loudness (dB relative to the speaker's median).
- Pitch and loudness prominence over the neighbours.

**Normalization.** Level-only: pitch and loudness are relative to the speaker's median; range,
dynamics, rate and pauses are never z-scored.

**Envelope.** For K good renditions, with rate, pause and range compared on a log scale:

    L = min_k x_k − m_f,  U = max_k x_k + m_f,  d = max(0, L − x, x − U) / s_f

- *m_f* is the null-edit measurement margin.
- *s_f* is the median envelope width on T1.
- Both are frozen, so K = 1 is exactly the single-reference baseline B1.

**Detector v2** (2026-10-14). Root causes were diagnosed on T1, and the fixes are switchable flags:
1. **Self-relative pace and monotone channels.** Good readers' overall tempo differs by up to
   1.8×. That made the absolute rate envelope 0.85 log2 wide, so a severity-5 rush stuck out by
   only 0.21. Measured relative to each reader's own median, the width is 0.31 and the same rush
   sticks out by 0.61. The absolute channels remain, so whole-speech rushing is still caught.
2. **Perceptible stress points.** v1 counted any positive prominence, even 0.1 dB, as a peak.
   v2 counts only peaks ≥ 1.5 semitones or ≥ 1 dB ('t Hart et al. 1990).
3. **Rubric λ pooled across dimensions.** Per-dimension fits from a few tiny detections had
   exploded (λ_pacing 68, λ_emphasis 86) while other dimensions kept a default.

**Regions.** Hysteresis per flaw type (open at τ_t, close at τ_t/2). Regions snap to words,
or to the silence for pauses. The dominant feature names the flaw.

**Severity.** Isotonic regression from d to severity, fitted on T1. The map is fitted to
perceived severity once the listening test exists.

**Scores.** score = 10·exp(−λ Σ d̄·dur/T).

**Explanations.** Templates filled with measured values only; no language model.

**Calibration (T1 only).** One τ per flaw type, by coordinate ascent: maximize T1 Matching
Score subject to ≤ 1 false alarm per minute on good-vs-good pairs. B1 gets its own τ by the
same rule.

**Reproducibility.** Sorted, rounded JSON with a SHA-256 hash. Two demo clips rerun
byte-identically, checked in CI. The environment is pinned with `uv.lock` and Docker.

## 4. Results

**Metrics.**
- **MS (Matching Score):** a flaw counts only if the type is correct and IoU ≥ 0.5.
- **FA:** false alarms per minute on good-vs-good pairs, leave-one-out.

**Status of each text.**
- v2 was motivated partly by inspecting T3/T4, so **T2–T4 are development feedback**.
- **T6 is the only untouched test.**
- The frozen v1 results are kept in `results/frozen_v1_2026-10-14/`.

| B2 envelope | v1 MS / FA | v2 MS / FA | B1 v2 MS / FA | B0 MS / FA |
|---|---|---|---|---|
| T1 (calibration) | 32% / 0.90 | 37% / 0.90 | 23% / 0.90 | 15% / 22.4 |
| T2 (development) | 30% / 1.35 | 40% / 2.03 | 30% / 0.90 | 18% / 26.2 |
| T3 (development) | 32% / 1.32 | 30% / 1.47 | 25% / 0.73 | 13% / 16.9 |
| T4 (development) | 23% / 1.65 | **35% / 0.24** | 27% / 0.94 | 15% / 19.3 |
| **T6 (untouched)** | 27% / 1.43 † | **23% / 2.15** | **27% / 2.15** | 13% / 22.5 |

† The v1 detector, run once on T6 as an ablation.

**Equal false-alarm budget** (best sweep point at or below the budget, B1 vs B2):
- **T6:** ≤ 1 FA/min: 15% vs 5%; ≤ 2 FA/min: 15% vs 17%.
- **T3:** ≤ 1 FA/min: 25% vs 18%.
- **T4:** ≤ 0.25 FA/min: 17% vs 35%.
- **T2:** ≤ 1 FA/min: 30% vs 30%.

**On the untouched text the single reference is as good as or better than the envelope, and v2
did not improve on v1.** The envelope's gains appear on development texts only.

**Per flaw (B2 v2, recall T3 / T4 / T6):**

| Flaw | Recall | Notes |
|---|---|---|
| Misplaced pause | 70 / 60 / 80% | Precision 100% |
| Pace | 50 / 60 / **0%** | On T6 the relative channel fires 119 times |
| Volume fade | 20 / 40 / 30% | |
| Missing pause | 20 / 10 / 20% | |
| Monotone | 20 / 40 / 10% | |
| **Missed emphasis** | **0% everywhere** | The stress floor removed it; v1 had 40–50% recall but it was the main false-alarm source |

**Temporal edges.** Median onset error 10–45 ms and offset error 20–45 ms on matched flaws, at
the aligner's floor (MFA reports 24 ms).

**Null-edit controls.** False alarms on null-edited clips equal those on originals (for
example 0.24 vs 0.24 per minute on T4). The detector does not react to PSOLA processing.

**Ladder flags outside labels.** Most are the source reader's own style, repeated on every
clip. Counted once per clip, the flags attributable to the edit are 0–0.3 per minute.

**Robustness** (B2 v2, severities 3 and 5):
| Condition | T4 MS | T6 MS |
|---|---|---|
| Clean | 54% | 38% |
| MP3 64 kbps | 54% | 38% |
| One wrong transcript word | 58% | 38% |
| Telephone band (simulated mic change) | 62% | 38% |
| Noise 20 dB SNR | 50% | 33% |
| Noise 10 dB SNR | 25% | 25% |

24 clips per text, so ±10 points is within noise.

**Human data.** The reader ranking, the listening test (perceived severity) and annotated
natural takes are all pending; the tools are ready (`cadence human`, `cadence natural`).

## 5. Limitations

- **The envelope is not universally better.** On the untouched T6, B1 matches or beats B2, so
  the dashboard ships B1 as a calibrated fallback mode.
- **v2 fits the development texts better than fresh data.** Relative pace fires often on T6, and
  missed emphasis is now undetected.
- **The good sets are provisional** (aligner confidence). With amateur readers the envelope is
  wide, and a source reader's own style shows up as flags. This is the spec's named risk.
- **Small samples:** 60 ladder clips per text and 5–6 good readers, so differences of 5–10
  points are within noise.
- **T3 and T4 share all 19 readers.**
- **Severity is the injected level until the listening test.** All results are on synthetic
  flaws until annotated natural takes exist.
- **Not built:** Azure baseline, WavLM rhythm, re-record pilot.

## 6. Reproduce

```bash
uv sync --extra dev
uv run cadence all      # fetch, refs, ladders, calibrate + evaluate
uv run cadence app      # dashboard
```
