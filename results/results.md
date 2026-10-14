## Results (all numbers as measured; thresholds fitted on T1 only)

**Detector v3 candidate vs v2** (dataset v3: emphasis targets at perceptible stress points). Thresholds fitted on T1 only; never retuned on T2/T3. T2–T6 are development texts (T6 was used once for v2, so it is no longer untouched). T3 and T4 are two passages read by the same 19 readers, so they are not independent; T3+T4 can jointly supply two of the required wins in the ship rule. T7 (Speech Accent Archive, Indian L1 speakers) and T8 (Tagore) added after detector v3 was designed and evaluated once; frozen v1 results in results/frozen_v1_2026-10-14/, frozen v2 results in results/frozen_v2_2026-10-14/. An automatic, pre-registered ship rule chooses between detector v3 (phrase channels) and v2.

| Method | Text | Matching Score | Time F1 | Onset err (ms) | Offset err (ms) | FA/min good pairs | FA/min null-edit | FA/min on ladders, edit-attributable | Severity rho |
|---|---|---|---|---|---|---|---|---|---|
| B0 generic norms | T1 (calib) | 16% | 0.03 | 10 | 60 | 22.42 | 22.12 | 0.83 | 0.19 |
| B0 generic norms | T2 | 20% | 0.04 | 160 | 48 | 26.20 | 26.65 | 0.11 | 0.42 |
| B0 generic norms | T3 | 13% | 0.03 | 145 | 10 | 16.89 | 17.62 | 0.69 | 0.17 |
| B0 generic norms | T4 | 16% | 0.07 | 30 | 50 | 19.34 | 19.11 | 0.19 | 0.24 |
| B0 generic norms | T6 | 15% | 0.03 | 25 | 5 | 22.54 | 22.36 | 0.11 | 0.32 |
| B0 generic norms | T7 | 22% | 0.13 | 55 | 340 | 25.33 | 24.48 | 1.77 | 0.09 |
| B0 generic norms | T8 | 10% | 0.06 | 20 | 40 | 14.46 | 14.84 | 0.11 | 0.56 |
| B1 single reference (K=1) | T1 (calib) | 25% | 0.33 | 15 | 75 | 0.90 | 0.90 | 0.33 | 0.50 |
| B1 single reference (K=1) | T2 | 33% | 0.31 | 30 | 165 | 0.90 | 0.90 | 0.00 | 0.58 |
| B1 single reference (K=1) | T3 | 22% | 0.39 | 10 | 20 | 0.73 | 0.73 | 0.00 | 0.51 |
| B1 single reference (K=1) | T4 | 29% | 0.21 | 20 | 20 | 0.94 | 0.94 | 0.00 | 0.45 |
| B1 single reference (K=1) | T6 | 29% | 0.14 | 25 | 20 | 2.15 | 2.15 | 0.00 | 0.49 |
| B1 single reference (K=1) | T7 | 22% | 0.35 | 10 | 20 | 3.38 | 3.38 | 0.07 | 0.35 |
| B1 single reference (K=1) | T8 | 28% | 0.16 | 20 | 40 | 2.47 | 2.09 | 0.32 | 0.42 |
| B2 envelope (K=all), ours | T1 (calib) | 40% | 0.39 | 10 | 30 | 0.90 | 0.75 | 0.00 | 0.64 |
| B2 envelope (K=all), ours | T2 | 44% | 0.47 | 30 | 45 | 2.03 | 2.03 | 0.11 | 0.65 |
| B2 envelope (K=all), ours | T3 | 35% | 0.54 | 10 | 20 | 1.47 | 1.62 | 0.00 | 0.59 |
| B2 envelope (K=all), ours | T4 | 40% | 0.35 | 35 | 40 | 0.24 | 0.24 | 0.35 | 0.55 |
| B2 envelope (K=all), ours | T6 | 27% | 0.19 | 10 | 20 | 2.15 | 1.97 | 0.02 | 0.48 |
| B2 envelope (K=all), ours | T7 | 27% | 0.22 | 10 | 21 | 2.11 | 1.69 | 1.77 | 0.40 |
| B2 envelope (K=all), ours | T8 | 28% | 0.35 | 20 | 40 | 2.28 | 2.09 | 0.00 | 0.66 |

### Matching Score by flaw type (T2 / T3 / T4 / T6 / T7 / T8)

| Method | misplaced_pause | missed_emphasis | missing_pause | monotone | pace | volume_fade |
|---|---|---|---|---|---|---|
| B0 generic norms | 40% / 40% / 40% / 50% / 40% / 40% | 0% / 0% / 0% / 0% / n/a / n/a | 0% / 0% / 0% / 0% / 0% / 0% | 40% / 40% / 50% / 30% / 80% / 10% | 30% / 0% / 0% / 0% / 0% / 0% | 0% / 0% / 0% / 0% / 0% / 0% |
| B1 single reference (K=1) | 70% / 70% / 60% / 80% / 80% / 60% | 0% / 0% / 0% / 0% / n/a / n/a | 0% / 20% / 10% / 10% / 0% / 0% | 20% / 20% / 60% / 30% / 40% / 20% | 40% / 10% / 10% / 10% / 20% / 30% | 50% / 10% / 20% / 30% / 0% / 30% |
| B2 envelope (K=all), ours | 70% / 70% / 60% / 80% / 80% / 60% | 60% / 20% / 0% / 20% / n/a / n/a | 10% / 20% / 10% / 20% / 10% / 10% | 40% / 20% / 40% / 10% / 20% / 0% | 50% / 60% / 70% / 0% / 50% / 20% | 40% / 20% / 40% / 30% / 0% / 50% |

### Per-flaw precision / recall, B2 (T2 / T3 / T4 / T6 / T7 / T8): recall = Matching Score (type + IoU >= 0.5); precision = share of flags overlapping a label of the same type (raw, then excluding flags the untouched source also gets)

| Type | T2 R / P raw / P edit | T3 R / P raw / P edit | T4 R / P raw / P edit | T6 R / P raw / P edit | T7 R / P raw / P edit | T8 R / P raw / P edit |
|---|---|---|---|---|---|---|
| misplaced_pause | 70% / 100% / 100% (n=7) | 70% / 100% / 100% (n=7) | 60% / 100% / 100% (n=6) | 80% / 100% / 100% (n=8) | 80% / 100% / 100% (n=4) | 60% / 100% / 100% (n=6) |
| missed_emphasis | 60% / 100% / 100% (n=3) | 20% / 100% / 100% (n=2) | 0% / n/a / n/a (n=0) | 20% / 100% / 100% (n=1) | n/a / n/a / n/a (n=0) | n/a / n/a / n/a (n=0) |
| missing_pause | 10% / 100% / 100% (n=1) | 20% / 100% / 100% (n=2) | 10% / 100% / 100% (n=1) | 20% / 100% / 100% (n=2) | 10% / 100% / 100% (n=1) | 10% / 100% / 100% (n=1) |
| monotone | 40% / 100% / 100% (n=4) | 20% / 100% / 100% (n=3) | 40% / 12% / 100% (n=57) | 10% / 100% / 100% (n=2) | 20% / 100% / 100% (n=2) | 0% / 100% / 100% (n=3) |
| pace | 50% / 17% / 58% (n=41) | 60% / 78% / 78% (n=9) | 70% / 39% / 39% (n=18) | 0% / 1% / 25% (n=110) | 50% / 10% / 17% (n=84) | 20% / 11% / 100% (n=56) |
| volume_fade | 40% / 100% / 100% (n=5) | 20% / 100% / 100% (n=2) | 40% / 57% / 57% (n=7) | 30% / 100% / 100% (n=3) | 0% / n/a / n/a (n=0) | 50% / 100% / 100% (n=5) |

### Matching Score at equal false-alarm budgets (best sweep point at or below the budget)

| Text | Method | <= 0.25/min | <= 0.5/min | <= 1/min | <= 2/min |
|---|---|---|---|---|---|
| T2 | B1 single reference | 24% | 24% | 33% | 33% |
| T2 | B2 envelope | 16% | 16% | 33% | 33% |
| T3 | B1 single reference | 12% | 12% | 22% | 22% |
| T3 | B2 envelope | 8% | 8% | 20% | 35% |
| T4 | B1 single reference | 18% | 18% | 29% | 29% |
| T4 | B2 envelope | 40% | 40% | 40% | 40% |
| T6 | B1 single reference | 16% | 16% | 16% | 16% |
| T6 | B2 envelope | 5% | 5% | 5% | 18% |
| T7 | B1 single reference | 0% | 0% | 11% | 11% |
| T7 | B2 envelope | 9% | 13% | 13% | 13% |
| T8 | B1 single reference | 18% | 18% | 18% | 18% |
| T8 | B2 envelope | 8% | 8% | 8% | 20% |

### Matching Score by injected severity (T2 / T3 / T4 / T6 / T7 / T8)

| Method | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| B0 generic norms | 9% / 0% / 0% / 0% / 11% / 0% | 0% / 8% / 9% / 0% / 11% / 0% | 0% / 8% / 9% / 9% / 22% / 0% | 45% / 25% / 27% / 27% / 33% / 20% | 45% / 25% / 36% / 36% / 33% / 30% |
| B1 single reference (K=1) | 0% / 0% / 9% / 0% / 0% / 0% | 9% / 8% / 9% / 18% / 11% / 10% | 36% / 17% / 27% / 18% / 22% / 40% | 55% / 25% / 27% / 36% / 33% / 50% | 64% / 58% / 73% / 73% / 44% / 40% |
| B2 envelope (K=all), ours | 0% / 0% / 0% / 0% / 11% / 0% | 9% / 8% / 9% / 18% / 22% / 0% | 36% / 33% / 45% / 27% / 22% / 30% | 82% / 58% / 64% / 27% / 22% / 50% | 91% / 75% / 82% / 64% / 56% / 60% |

### Ship decision (v3 vs v2, dataset v3)

- **Shipped: detector v2**
- T1: v3 MS = 38%, v2 MS = 40%, v3 wins T1: False
- Reason: v3 does not beat v2 on T1 (MS 38% vs 40%); v3 beats v2 on only 1 held-out text(s) (need >= 2)

| Text | v3 MS | v2 MS | v3 FA/min | v2 FA/min | Outcome |
|---|---|---|---|---|---|
| T2 | 35% | 44% | 0.68 | 2.03 | v2 wins |
| T3 | 27% | 35% | 1.47 | 1.47 | v2 wins |
| T4 | 20% | 40% | 0.47 | 0.24 | v2 wins |
| T6 | 27% | 27% | 1.43 | 2.15 | v2 wins |
| T7 | 27% | 27% | 0.84 | 2.11 | v2 wins |
| T8 | 38% | 28% | 2.85 | 2.28 | v3 wins |

### Ablations (T2 / T3 / T4 / T6 / T7 / T8)

| Variant | Matching Score | FA/min good pairs | FA/min null-edit |
|---|---|---|---|
| K=1 | 33% / 22% / 29% / 29% / 22% / 28% | 0.90 / 0.73 / 0.94 / 2.15 / 3.38 / 2.47 | 0.90 / 0.73 / 0.94 / 2.15 / 3.38 / 2.09 |
| K=2 | 31% / 23% / 33% / 27% / 22% / 22% | 1.58 / 1.47 / 2.12 / 1.97 / 4.64 / 2.47 | 1.58 / 1.62 / 2.12 / 1.97 / 4.64 / 2.47 |
| K=4 | 40% / 28% / 33% / 31% / 31% / 24% | 0.68 / 0.59 / 0.47 / 1.07 / 1.69 / 1.71 | 0.90 / 0.59 / 0.24 / 1.07 / 1.27 / 1.71 |
| no null-edit margin | 44% / 33% / 38% / 27% / 24% / 28% | 1.35 / 1.17 / 0.24 / 1.97 / 1.69 / 1.90 | 1.58 / 1.17 / 0.24 / 1.97 / 1.69 / 2.09 |
| norm off | 38% / 30% / 36% / 22% / 29% / 20% | 2.26 / 1.47 / 0.47 / 2.68 / 2.11 / 2.47 | 2.03 / 1.62 / 0.24 / 2.68 / 2.53 / 2.47 |
| norm z-score (v1) | 25% / 28% / 29% / 29% / 18% / 30% | 1.81 / 1.62 / 2.12 / 2.50 / 2.53 / 1.71 | 1.81 / 1.62 / 1.65 / 2.33 / 2.53 / 1.71 |
| other candidate: v3 detector (phrase channels) | 35% / 27% / 20% / 27% / 27% / 38% | 0.68 / 1.47 / 0.47 / 1.43 / 0.84 / 2.85 | 0.68 / 1.47 / 0.24 / 1.43 / 0.42 / 2.66 |
| v1 detector (frozen design) | 33% / 28% / 24% / 31% / 20% / 28% | 1.35 / 1.32 / 1.65 / 1.43 / 2.53 / 1.14 | 1.35 / 1.32 / 1.65 / 1.43 / 2.53 / 1.14 |
| without relative channels | 35% / 30% / 25% / 31% / 22% / 30% | 0.68 / 1.32 / 0.94 / 1.07 / 2.11 / 0.95 | 0.68 / 1.47 / 0.71 / 0.89 / 2.11 / 0.95 |
| without stress floor | 44% / 33% / 40% / 25% / 27% / 28% | 2.26 / 1.62 / 0.47 / 2.15 / 2.11 / 2.28 | 2.03 / 1.76 / 0.47 / 1.97 / 1.69 / 2.09 |

### Compound clips (T2 / T3 / T4 / T6 / T7 / T8)

- B0 generic norms: Matching Score 50% / 50% / 25% / 50% / 38% / 38%
- B1 single reference (K=1): Matching Score 62% / 50% / 25% / 50% / 62% / 50%
- B2 envelope (K=all), ours: Matching Score 88% / 50% / 50% / 25% / 62% / 62%

### Natural spectrum and listening test

- T2: pending human ranking (data/rankings/<T>.csv); Spearman = n/a
- T3: pending human ranking (data/rankings/<T>.csv); Spearman = n/a
- T4: pending human ranking (data/rankings/<T>.csv); Spearman = n/a
- T6: pending human ranking (data/rankings/<T>.csv); Spearman = n/a
- T7: pending human ranking (data/rankings/<T>.csv); Spearman = n/a
- T8: pending human ranking (data/rankings/<T>.csv); Spearman = n/a
- Listening test: pending: no responses yet

### Natural flaws (teammate takes)

- Status: pending: no takes in data/takes/<T>/

### Robustness (T4 ladders, severities 3 and 5, envelope K=all)

| Condition | Matching Score | Time F1 | Onset err (ms) |
|---|---|---|---|
| clean | 64% | 0.46 | 35 |
| noise_20 | 45% | 0.22 | 50 |
| noise_10 | 32% | 0.16 | 79 |
| mp3_64k | 64% | 0.46 | 35 |
| telephone_band | 59% | 0.23 | 40 |
| wrong_word | 64% | 0.49 | 55 |

### Robustness (T6 ladders, severities 3 and 5, envelope K=all)

| Condition | Matching Score | Time F1 | Onset err (ms) |
|---|---|---|---|
| clean | 45% | 0.29 | 18 |
| noise_20 | 41% | 0.19 | 35 |
| noise_10 | 23% | 0.06 | 105 |
| mp3_64k | 45% | 0.29 | 18 |
| telephone_band | 45% | 0.24 | 10 |
| wrong_word | 45% | 0.24 | 18 |

### Robustness (T7 ladders, severities 3 and 5, envelope K=all)

| Condition | Matching Score | Time F1 | Onset err (ms) |
|---|---|---|---|
| clean | 39% | 0.32 | 10 |
| noise_20 | 33% | 0.25 | 1 |
| noise_10 | 22% | 0.24 | 11 |
| mp3_64k | 33% | 0.28 | 9 |
| telephone_band | 39% | 0.71 | 10 |
| wrong_word | 39% | 0.32 | 10 |
