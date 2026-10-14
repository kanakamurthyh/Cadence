# Cadence: judging a delivery against the range of good renditions

Track C, Contrastive Speech Analytics · technical report (max 6 pages)

## 1. Problem and claim

Competitive speakers get vague and inconsistent delivery feedback. Human raters of oratory
agree poorly (ICC 0.03–0.38 in 3MT_French; ρ = 0.47 in APSA). Existing tools judge against
generic norms, such as PowerPoint Speaker Coach's 100–165 wpm, or against a reference text
(Azure). Neither can tell a stylistic choice from a flaw.

Cadence flags a word only when the attempt leaves the range spanned by **several** strong
renditions of the same text, and explains each flag in measured units.

The claim we test is modest: compared with a single reference, the envelope should find more
injected flaws at an equal false-alarm rate on good-vs-good pairs. We report every result,
including the ones that do not support it. Numbers below come from files in the repository, named next to
them; the v2 diagnosis figures in §3 are carried over from the v2 analysis.

## 2. Dataset construction

Public dataset: `huggingface.co/datasets/Vedant1605/cadence-contrastive-speech`, subsets
`public_domain` and `saa_indian_nc_sa`. Totals (`data/inventory.json`): 132 recordings,
443 synthetic clips, 476 label rows (`data/labels/validation.json`): 427 flaw labels plus
clean-reference and null-edit rows.

| Text | Readers | Role |
|---|---|---|
| T1 *Sea Fever* | 24 LibriVox | Calibration only |
| T2 *Stopping by Woods* | 23 | Development test (poetry) |
| T3 Gettysburg Address, closing | 19 | Development test (speech) |
| T4 Gettysburg Address, opening | The same 19 readers | Development test; **not independent of T3** |
| T5 FDR "Day of Infamy", opening | 1941 original + 1 reader | Blocked: needs ≥ 4 renditions |
| T6 Kipling, *If—* | 17 (15 before the rebuild) | Test; used once for v2, so no longer untouched |
| **T7** SAA "Please call Stella" | 12 India-born speakers | **Held out** (Indian-accented English) |
| **T8** Tagore, *Fruit-Gathering* XVIII | 16 LibriVox | **Held out** (Indian-authored text) |

**Indian-speaker texts.** A source survey (`reports/Indian speech dataset sources.md`) found
the Speech Accent Archive (GMU) to be the only large pool of Indian speakers reading one
identical text. T7 takes 2 India-born speakers each with Hindi, Bengali, Telugu, Tamil,
Marathi and Malayalam as L1 (speaker table in `data/DATA_CARD.md`). LibriVox's Tagore XVIII
gives 16 public-domain readings of an Indian-authored text, but its readers are **not
confirmed Indian-accented**, and several also read T1–T4 (`data/inventory.json`). Both texts
were added after detector v3 was designed and were evaluated once.

**Licences.** LibriVox audio is public domain (PDM 1.0); the FDR original is a US federal work.
T7 is CC BY-NC-SA 4.0 (accent.gmu.edu/howto), so it and every clip derived from it form a
separate non-commercial, share-alike subset. TED/TEDx (CC BY-NC-ND) is candidates only.

**Speaker overlap.** No reader in T1's good set appears in any test text (`cadence inventory`).

**Preparing each reading.**
- Decode with ffmpeg to 16 kHz mono at −23 LUFS.
- Locate the passage with wav2vec2 greedy transcription, matched on letters so accented or
  misheard speech still counts.
- Force-align the known transcript; snap word edges to silences.

**Good set.** Top 6 per text, **provisionally ranked by aligner confidence**; the 3-rater human
ranking is pending. For T7 this ranking is itself accent-sensitive: an English aligner picked
Bengali, Tamil (2), Marathi, Malayalam and Telugu speakers, and **no Hindi speaker**
(`data/refs/T7/selection.json`).

**Synthetic ladders.** 6 flaw types × 2 spans × 5 severities, injected with Praat PSOLA into the
top-ranked rendition from a fixed seed, plus null-edit copies of every good rendition and
compound clips. A flaw type is skipped where no valid span exists.

| Type | Edit | Severity 1 → 5 |
|---|---|---|
| Pace | PSOLA duration factor, pitch kept | ×0.9→×0.55 (rushed), ×1.1→×1.8 (dragging) |
| Missing pause | Silence shortened where **every** good reader pauses | 20→100% removed |
| Misplaced pause | Room tone inserted where **no** good reader pauses | 0.3→2.0 s |
| Monotone | Pitch compressed toward the span median | 80→10% of range kept |
| Missed emphasis | Peak flattened at a **perceptible** consensus stress point | 80→0% kept |
| Volume fade | Gain ramp held across the span | −3→−18 dB |

**Dataset v3 emphasis rule (this release).** Under dataset v2, missed-emphasis targets were any
point where ≥ ¾ of good readers had *any* positive prominence, while the v2 detector reads
only perceptible stress (≥ 1.5 st or ≥ 1 dB, 't Hart et al. 1990) and zeroes d elsewhere. Most
targets were therefore invisible to it by construction: B2 emphasis recall was 0% on T3, T4 and
T6 and 30% on T2 (`results/frozen_v2_2026-10-14/results.md`). Dataset v3 places targets only
where ≥ ¾ of good readers peak perceptibly. T3 has 2 such spans, T1/T2/T4/T6 have 1, and T7/T8
have none, so they carry no emphasis clips (`data/ladders/<T>/manifest.json`). Per text:
T1 63, T2 65, T3 70, T4 65, T6 65, T7 55, T8 60 clips.

**Controls.** Every clip, clean ones included, goes through the same PSOLA resynthesis. The
edited rendition is never in its own envelope.

**Label validation** (`cadence labels` → `data/labels/validation.json`, 427 labels):
- Bounds: 427 pass. Clip lengths vs the stretch/cut/insert maths: 401 checks, none fail.
- 19 labels have edges > 100 ms from an independent re-alignment, which is aligner error on
  faded or stretched speech; the analytic time map is exact.
- 5 misplaced-pause labels attribute the silence one word off (time span correct); 1 join is
  at 1.02× the click threshold.

## 3. Method

`preprocess → locate text → align → features → envelope → regions → type + explain → scores`

**Features (per word).** Articulation rate (5-word window); pause after the word; pitch range
(3-word window, semitones); loudness (dB re the speaker's median); pitch and loudness
prominence over the neighbours. Self-relative rate and range (each relative to the reader's
own median) feed the v2 pace and monotone channels.

**Normalization.** Level-only: pitch and loudness are relative to the speaker's median; range,
dynamics, rate and pauses are never z-scored.

**Envelope.** For K good renditions, with rate, pause and range on a log scale:

    L = min_k x_k − m_f,  U = max_k x_k + m_f,  d = max(0, L − x, x − U) / s_f

*m_f* is the null-edit measurement margin and *s_f* the median envelope width on T1. Both are
frozen, so K = 1 is exactly the single-reference baseline B1.

**Detector v2 (shipped).** Root causes diagnosed on T1 only (figures carried over from the v2
analysis, not re-measured on dataset v3):
1. **Self-relative pace and monotone channels.** Good readers' overall tempo differs by up to
   1.8×, so the absolute rate envelope was 0.85 log2 wide and a severity-5 rush stuck out by
   only 0.21. Relative to each reader's median the width is 0.31 and the rush sticks out by
   0.61. Absolute channels remain, so whole-speech rushing is still caught.
2. **Perceptible stress points.** Only peaks ≥ 1.5 st or ≥ 1 dB count.
3. **Rubric λ pooled across dimensions** (per-dimension fits from tiny detections exploded).

**Detector v3 (built, not shipped).** Phrase boundaries are word gaps where ≥ ¾ of good readers
pause. Per phrase: articulation rate and F0 spread (p90 − p10, st), each relative to the
reader's median across phrases. These replace the word-level relative channels; a phrase
region is trimmed to the words that themselves deviate. Available as `Config(phrase=True)`.

**Regions.** Hysteresis per flaw type (open at τ_t, close at τ_t/2), snapped to words or to the
silence for pauses. The dominant feature names the flaw.

**Severity and scores.** Isotonic map from d to severity, fitted on T1 (to perceived severity
once the listening test exists). Score = 10·exp(−λ Σ d̄·dur/T).

**Explanations.** Templates filled with measured values only; no language model.

**Calibration (T1 only).** One τ per flaw type by coordinate ascent: maximize T1 Matching Score
subject to ≤ 1 false alarm/min on good-vs-good pairs. B1 gets its own τ by the same rule.
Nothing is retuned on any other text.

**Pre-registered ship rule.** Before evaluation we coded the choice between v3 and v2 as a
tested function, `benchmark.ship_decision`: v3 ships only if it beats v2 on T1 **and** on ≥ 2
non-calibration texts (T2–T8), without exceeding 2 FA/min on a text where v2 stays under it. The winner's
parameters are saved automatically. T3 and T4 share readers, so they could jointly have
supplied both wins; the rule does not correct for that.

## 4. Results

**Metrics.** **MS** (Matching Score): a flaw counts only if the type is correct and IoU ≥ 0.5.
**FA**: false alarms per minute on good-vs-good pairs, leave-one-out. All numbers are from
`results/results.md` (dataset v3) unless marked.

**The pre-registered decision** (`results/results.json` → `ship_decision`):

| | T1 | T2 | T3 | T4 | T6 | T7 | T8 |
|---|---|---|---|---|---|---|---|
| v3 MS | 38% | 35% | 27% | 20% | 27% | 27% | **38%** |
| v2 MS | **40%** | **44%** | **35%** | **40%** | 27% | 27% | 28% |

v3 loses T1 and wins only T8, so **v2 ships**. v3 does lower FA on T2 (0.68 vs 2.03), T6 (1.43
vs 2.15) and T7 (0.84 vs 2.11), but the rule is about detection at the calibrated operating
point, and we did not change it afterwards.

**Headline (shipped v2 on dataset v3).** Each method is at its own calibrated operating point,
so FA differs; the equal-FA table follows.

| Text | B0 MS / FA | B1 MS / FA | B2 MS / FA | B2 before (dataset v2) |
|---|---|---|---|---|
| T1 (calibration) | 16% / 22.4 | 25% / 0.90 | 40% / 0.90 | 37% / 0.90 |
| T2 (dev) | 20% / 26.2 | 33% / 0.90 | 44% / 2.03 | 40% / 2.03 |
| T3 (dev) | 13% / 16.9 | 22% / 0.73 | 35% / 1.47 | 30% / 1.47 |
| T4 (dev) | 16% / 19.3 | 29% / 0.94 | **40% / 0.24** | 35% / 0.24 |
| T6 | 15% / 22.5 | **29% / 2.15** | 27% / 2.15 | 23% / 2.15 |
| **T7 (held out)** | 22% / 25.3 | 22% / 3.38 | **27% / 2.11** | — |
| **T8 (held out)** | 10% / 14.5 | 28% / 2.47 | 28% / 2.28 | — |

"Before" is `results/frozen_v2_2026-10-14/results.md`. The gain comes from the emphasis fix:
B2 emphasis recall is now 60 / 20 / 0 / 20% on T2 / T3 / T4 / T6.

**Equal false-alarm budget** (best sweep point at or below the budget, B1 vs B2):

| ≤ 1 FA/min | T2 | T3 | T4 | T6 | T7 | T8 |
|---|---|---|---|---|---|---|
| B1 | 33% | 22% | 29% | **16%** | 11% | **18%** |
| B2 | 33% | 20% | **40%** | 5% | **13%** | 8% |

At ≤ 0.5 FA/min on T7, B1 scores 0% and B2 13%. **The envelope is not universally better**: it
wins clearly on T4 and slightly on T7, ties T2, loses slightly on T3 (22% vs 20%) and clearly on
T6 and T8.

**Per flaw (B2 recall, T2 / T3 / T4 / T6 / T7 / T8):**

| Flaw | Recall | Notes |
|---|---|---|
| Misplaced pause | 70 / 70 / 60 / 80 / 80 / 60% | Precision 100% everywhere |
| Pace | 50 / 60 / 70 / **0** / 50 / 20% | On T6, 110 pace flags at 1% precision |
| Volume fade | 40 / 20 / 40 / 30 / 0 / 50% | |
| Monotone | 40 / 20 / 40 / 10 / 20 / 0% | |
| Missing pause | 10 / 20 / 10 / 20 / 10 / 10% | |
| Missed emphasis | 60 / 20 / 0 / 20 / – / –% | No perceptible consensus stress on T7/T8 |

**Severity gradient** (Figure 1). B2 MS at severity 5: 91 / 75 / 82 / 64 / 56 / 60%; at
severity 1: 0–11%. B2's severity ρ (Spearman, predicted vs injected) is 0.40–0.66, above B1 on
every test text except T6 (0.48 vs 0.49).

**Temporal edges.** B2 median onset error 10–35 ms and offset error 20–45 ms on matched flaws
(T2–T8), at the aligner's floor (MFA reports 24 ms).

**Null-edit controls** (Figure 3). B2's FA on PSOLA-resynthesised but unedited clips never
exceeds its good-pair FA by more than 0.15/min (T3 1.62 vs 1.47; T4 0.24 vs 0.24; lower on
T6–T8); the detector does not react to processing. Flags on ladders outside labels are mostly the source
reader's own style; counted once per clip, the edit-attributable rate is 0–0.35/min, except
T7 at 1.77/min.

**Ablations** (MS T2 / T3 / T4 / T6 / T7 / T8): K = 1: 33 / 22 / 29 / 29 / 22 / 28%; K = 4:
40 / 28 / 33 / 31 / 31 / 24%; K = all (B2): 44 / 35 / 40 / 27 / 27 / 28%. More references help on
T2–T4; K = 4 beats K = all on T6 and T7. z-score normalization (v1):
25 / 28 / 29 / 29 / 18 / 30%. Compound clips, B2: 88 / 50 / 50 / 25 / 62 / 62%.

**Robustness** (B2, severities 3 and 5; `results/robustness_T4.json`, `_T6`, `_T7`):

| Condition | T4 MS | T6 MS | T7 MS |
|---|---|---|---|
| Clean | 64% | 45% | 39% |
| MP3 64 kbps | 64% | 45% | 33% |
| One wrong transcript word | 64% | 45% | 39% |
| Telephone band | 59% | 45% | 39% |
| Noise 20 dB SNR | 45% | 41% | 33% |
| Noise 10 dB SNR | 32% | 23% | 22% |

22 labels on T4 and T6, 18 on T7, so one label moves MS by 5–6 points.

**Demo** (`data/demo/demo_T3.json`). T3 rushed pace, severity 4, "that we here highly": B2 finds
it with IoU 0.975 and 1 flag; B1 raises nothing; B0 raises 19 flags, none matching. The Demo tab
reruns this detection live.

**Reproducibility.** A from-scratch rebuild (fetch → refs → ladders) reproduced all 371
dataset-v2 label rows with identical clip ids and timestamps. 29 rows' measured effect sizes
differed (median 1.4%, max 21%) through floating-point drift in resynthesis and measurement
(`results/rebuild_check_2026-10-14.md`). Analysis output is sorted, rounded JSON with a SHA-256
hash and reruns byte-identically (`scripts/rerun_check.py`, CI). Environment: `uv.lock`, Docker.

## 4a. Evidence figures

![Matching score vs severity](figures/gradient_matching_by_severity.png)
*Figure 1. Matching score (type-correct detection with IoU ≥ 0.5) vs injected severity for B0, B1 and B2, pooled across held-out texts (faint lines = per-text, bold = mean).*

![Injected effect by flaw type](figures/gradient_by_type.png)
*Figure 2. Absolute injected effect magnitude (median ± IQR across all texts) vs injected severity, one panel per flaw type; shows the acoustic size of the edit at each rung of the synthetic ladder.*

![False-alarm rate B1 vs B2](figures/false_alarms_null_edit.png)
*Figure 3. FA/min on good-reference pairs (left) and on null-edit clips — PSOLA-resynthesised but acoustically unmodified (right) — for B1 vs B2 across held-out texts; if PSOLA resynthesis alone triggered the detector, null-edit bars would exceed good-pair bars.*

![Label timing error](figures/label_timing_error.png)
*Figure 4. Histogram of per-clip timing-map error (ms) for every synthetic clip with a time map; dashed reference lines show the median onset and offset detection error from B2 matched predictions.*

## 5. Limitations

- **The envelope is not universally better.** On T6 and T8, B1 matches or beats B2 at tight
  false-alarm budgets, so the dashboard ships B1 as a calibrated fallback.
- **T2–T6 are development data.** All of them informed v2 or the v3 dataset decision; only T7
  and T8 are fresh, and each was evaluated once.
- **Indian-speaker caveats.** T7's good set was chosen by an English aligner's confidence and
  contains no Hindi speaker. T8's readers are not confirmed Indian-accented. T7 has no
  emphasis clips and only 18 robustness labels.
- **Good sets are provisional** (aligner confidence). With amateur readers the envelope is
  wide, and a source reader's own style shows up as flags (T7: 1.77 edit-attributable FA/min).
- **Small samples:** 55–70 clips per text and 6 good readers; differences of 5–10 points are
  within noise. T3 and T4 share all 19 readers.
- **Synthetic flaws only, injected severity** until the listening test and natural takes exist;
  the tools are ready (`cadence human`, `cadence natural`).
- **Not built:** Azure baseline, WavLM rhythm, re-record pilot.

## 6. Reproduce

```bash
uv sync --extra dev
uv run cadence all      # fetch, refs, ladders, calibrate + evaluate (ship rule included)
uv run python scripts/robustness.py --text T7 --workers 3
uv run --extra report python scripts/gradient_figures.py
uv run cadence app      # dashboard
```
