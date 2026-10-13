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
including the ones that do not support it.

## 2. Dataset construction

**Texts and readers.**

| Text | Readers | Role |
|---|---|---|
| T1 *Sea Fever* | 24 LibriVox readers | Calibration only |
| T2 *Stopping by Woods* | 23 readers | Test |
| T3 Gettysburg Address, closing paragraph | 19 readers | Test (oratory) |

All recordings are public domain.

**Preparing each reading.**
- Decode to 16 kHz mono and normalize to −23 LUFS.
- Find the text inside the recording with greedy wav2vec2 CTC transcription and dense
  sequence matching. This removes LibriVox preambles and, for T3, the rest of the speech.
- Force-align the known transcript, then snap word edges to silence edges of the intensity
  contour.

**Good set.** The top 6 readers per text. Ranking is provisional, by mean aligner confidence,
until three teammates rank readers on a 20 s excerpt (tool shipped: `cadence human`).

**Synthetic ladders.**
- Injected into the top-ranked rendition from a fixed seed: 6 types × 2 spans × 5 severities
  = 60 clips per text.
- Also built: a null-edit copy of every good rendition, and 2–4 compound clips per text.
- In total, 208 clips with exact word-span labels.

| Type | Edit | Severity 1 → 5 |
|---|---|---|
| Pace | PSOLA duration change, pitch kept | ×0.9→×0.55 (rushed), ×1.1→×1.8 (dragging) |
| Missing pause | Silence shortened at a boundary where **every** good reader pauses | 20→100% removed |
| Misplaced pause | Room tone inserted where **no** good reader pauses | 0.3→2.0 s |
| Monotone | Pitch compressed toward the span median | 80→10% of range kept |
| Missed emphasis | Peak flattened at a consensus stress point (pitch and loudness) | 80→0% kept |
| Volume fade | Gain ramp held across the span | −3→−18 dB |

**Artifact control.** Every clip, the clean controls included, passes through the same Praat
PSOLA resynthesis. A detector therefore cannot score by hearing processing artifacts.

**Leakage rule.** The edited rendition never sits in the envelope that scores its own ladder.

The pause types are constrained by consensus on purpose. An earlier version removed pauses
that only the source reader made. By the envelope's own definition those are stylistic, so
the labels were wrong, and we fixed the generator rather than the detector.

## 3. Rubric and architecture

`preprocess → align (MFA if installed, else CTC wav2vec2) → features → envelope → regions → type + explain → scores`

**Features (per word).**
- Articulation rate over a 5-word window, in syllables/s.
- Pause after the word, in s.
- Pitch range over a 3-word window, in semitones (90th − 10th percentile).
- Loudness over a 3-word window, in dB relative to the speaker's median.
- Pitch and loudness prominence over the two neighbours on each side.

F0 limits are speaker-adaptive (two-pass, Hirst 2011).

**Level-only normalization** fixes v1's bug. Pitch and loudness are referenced to the
speaker's median, while range, dynamics, rate and pauses keep their absolute units. Nothing is
z-scored, so a speaker who rushes the whole text is still flagged.

**Envelope.** For K good renditions:

    L = min_k x_k − m_f,  U = max_k x_k + m_f,  d = max(0, L − x, x − U) / s_f

- Rate, pause and pitch range are compared on a log (ratio) scale.
- *m_f* is the 95th percentile of |reference − null-edited reference|.
- *s_f* is the median envelope width on T1.
- Both are frozen after calibration, so K = 1 is exactly the single-reference baseline.

**Gating.**
- Missed emphasis is read only at consensus stress points, where ≥ 3/4 of good readers peak.
- A missing pause counts only where every good reader paused.

**Regions and typing.** Hysteresis on d per flaw type (open at τ_t, close at τ_t/2), merging
runs one word apart. Regions snap to word edges, or to the silence itself for pauses. When
regions overlap, the dominant feature names the flaw.

**Severity.** Isotonic regression from mean d to severity, fitted on T1. It uses injected
levels until listening-test data exists.

**Scores.** Six dimensions on 0–10:

    score_d = 10·exp(−λ_d Σ_r d̄_r·dur_r/T)

λ_d is set so that a median severity-3 flaw halves the score.

**Explanation.** A template filled with the measured numbers only, for example:

> Word 43 (14.7–15.7 s): pause after 'near' 0.00 s; the good renditions spanned 0.18–0.98
> across six. Pause after 'near'.

No language model judges anything. SSDM reports ChatGPT at F1 5.6 on real dysfluent speech.

**Calibration (T1 only).** One τ per flaw type, chosen by coordinate ascent to maximize T1
Matching Score subject to **≤ 1 false alarm per minute on good-vs-good pairs**. The same
procedure tunes B1.

**Reproducibility.**
- Outputs are rounded to 4 decimals and dumped with sorted keys.
- Each report carries a SHA-256 hash.
- `scripts/rerun_check.py` (run in CI) asserts byte-identical JSON across runs.
- The environment is pinned in `uv.lock`, with a Dockerfile.

## 4. Evaluation results

Thresholds were fitted on T1 only; T2 and T3 were never seen during tuning.

**Metrics.**
- **Matching Score (MS):** a flaw counts only if the type is correct and IoU ≥ 0.5, as in SSDM.
- **False alarms (FA)** are counted per minute of good delivery, leave-one-out.

| Method | MS T2 | MS T3 | Time F1 T2/T3 | FA/min good pairs T2/T3 | Onset / offset err (ms, T2) | Severity ρ T2/T3 |
|---|---|---|---|---|---|---|
| B0 generic norms | 18% | 13% | 0.03 / 0.04 | 26.2 / 16.9 | 160 / 48 | 0.39 / 0.21 |
| B1 single reference (K=1) | 20% | 18% | 0.19 / 0.33 | 0.68 / 0.15 | 25 / 40 | 0.33 / 0.42 |
| **B2 envelope (K=6)** | **30%** | **32%** | **0.48 / 0.48** | 1.35 / 1.32 | 20 / 40 | 0.36 / 0.32 |

**Equal-false-alarm comparison** (each method's thresholds scaled together):

| FA/min budget | Text | B1 MS | B2 MS |
|---|---|---|---|
| ≈ 0.7 | T2 | 20% (0.68) | 25% (0.68) |
| ≈ 1.5 | T2 | 27% (1.58) | 35% (1.58) |
| ≈ 1.3 | T3 | 22% (1.32) | 32% (1.32) |
| ≈ 0.15 | T3 | 18% (0.15) | 17% (0.15) |

At matched false-alarm rates the envelope finds as many flaws or more. The one exception is
the strictest T3 point, where the two tie.

**By type (B2, T2/T3):**

| Type | MS |
|---|---|
| Misplaced pause | 90 / 100% |
| Missed emphasis | 40 / 50% |
| Volume fade | 30 / 20% |
| Missing pause | 20 / 20% |
| Pace | 0% |
| Monotone | 0% |

Under the 1 FA/min budget, calibration switched pace and monotone off: on T1 every threshold
that caught them cost too many false alarms. The detector still separates them at severity 5
(see §5), but not cheaply enough.

**By severity (B2, T2):** 8% → 25% → 25% → 33% → 58% from level 1 to level 5.

**Ablations (MS T2/T3; FA/min T2/T3):**

| Variant | MS | FA/min |
|---|---|---|
| K=1 | 20 / 18% | 0.68 / 0.15 |
| K=2 | 20 / 18% | 0.90 / 0.88 |
| K=4 | 27 / 23% | 0.68 / 1.17 |
| **K=6** | **30 / 32%** | 1.35 / 1.32 |
| Normalization off | 25 / 28% | 1.35 / 1.17 |
| v1 z-score | 20 / 28% | 0.90 / 1.32 |
| No null-edit margin | 32 / 33% | 1.35 / 1.17 |

- **K:** recall grows with K, as the hypothesis predicts.
- **Normalization:** v1's z-scoring costs 10 points on T2 and none on T3. The measured margin
  m_f does **not** help; it is small (0.02 log-units for rate) and we report it as no gain.
- **Null-edit controls:** false alarms on null-edited clips equal those on the originals
  (1.35 vs 1.35 per minute on T2). The detector does not respond to PSOLA processing itself.

**Compound clips** (two flaws each): B2 scores 12% (T2) and 50% (T3); B0 scores 38% and 50%.
Only 4 clips per text, so these numbers are noisy.

**Robustness** (B2 on T2 ladders, severities 3 and 5):

| Condition | MS | Time F1 | Onset error (ms) |
|---|---|---|---|
| Clean | 42% | 0.59 | 15 |
| 64 kbps MP3 | 42% | 0.59 | 15 |
| One wrong transcript word | 42% | 0.59 | 15 |
| Noise, 20 dB SNR | 29% | 0.42 | 80 |
| Noise, 10 dB SNR | 21% | 0.10 | 70 |

Noise is the main weakness: noise floors blur the silence edges, so the intensity threshold is
the place to fix it. The phone-microphone re-recording needs a person and is pending.

**Pending (needs people):**
- Listening test: 5 listeners × 36 clips, tool ready.
- Human reader ranking, which gives the natural-spectrum Spearman.
- Teammate takes with two annotators, which give natural-flaw F1 and annotator IoU.
- Re-record pilot.

## 5. Limitations and failure cases

- **Pace and monotone are not detected at the shipped operating point.** The per-word
  envelope for rate and pitch range is wide: amateur readers vary a lot, and syllable rate is
  noisy at word level. The strongest injections reach d ≈ 0.8–1.1 while clean readers reach
  0.3. A stricter good set from human ranking, region-level rather than word-level rate, or
  WavLM rhythm (stretch) are the next steps.
- **The edge is modest and the samples are small.** About 60 ladder clips per text. The
  envelope's edge over a single reference is 5–10 points of Matching Score at equal false
  alarms, with one tie. Error bars are wide.
- **The good set is provisional.** It is ranked by aligner confidence (clarity and fidelity),
  not by humans. If the good set is mediocre, the envelope is too wide; this is the spec's
  named primary risk.
- **Aligner.** MFA was not installable here, so we used CTC wav2vec2 with silence snapping.
  The median onset error on matched flaws is 0–25 ms, at the aligner floor. We claim nothing
  tighter.
- **Synthetic is not natural.** Ladder numbers are an upper bound for natural flaws until the
  teammate takes are annotated.
- **T3** has no recording of the original orator, because none exists; its envelope is
  LibriVox readers.

## 6. Reproduce

```bash
uv sync --extra dev
uv run cadence all      # fetch, refs, ladders, calibrate + evaluate
uv run cadence app      # dashboard
```
