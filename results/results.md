## Results (all numbers as measured; thresholds fitted on T1 only)

**Detector v2** (2026-10-14: self-relative pace/monotone channels, perceptible stress points). Thresholds fitted on T1 only. The v2 changes were partly motivated by inspecting T3/T4, so **T2-T4 are development feedback**; **T6 is the untouched final test** (added after v2 was frozen, evaluated once). T3 and T4 are two passages read by the same 19 readers, so they are not independent. The frozen v1 results are in results/frozen_v1_2026-10-14/.

| Method | Text | Matching Score | Time F1 | Onset err (ms) | Offset err (ms) | FA/min good pairs | FA/min null-edit | FA/min on ladders, edit-attributable | Severity rho |
|---|---|---|---|---|---|---|---|---|---|
| B0 generic norms | T1 (calib) | 15% | 0.02 | 10 | 60 | 22.42 | 22.12 | 0.73 | 0.18 |
| B0 generic norms | T2 | 18% | 0.03 | 160 | 48 | 26.20 | 26.65 | 0.12 | 0.39 |
| B0 generic norms | T3 | 13% | 0.04 | 145 | 10 | 16.89 | 17.62 | 0.66 | 0.21 |
| B0 generic norms | T4 | 15% | 0.06 | 30 | 50 | 19.34 | 19.11 | 0.17 | 0.22 |
| B0 generic norms | T6 | 13% | 0.03 | 25 | 5 | 22.54 | 22.36 | 0.13 | 0.30 |
| B1 single reference (K=1) | T1 (calib) | 23% | 0.31 | 15 | 75 | 0.90 | 0.90 | 0.32 | 0.47 |
| B1 single reference (K=1) | T2 | 30% | 0.28 | 30 | 161 | 0.90 | 0.90 | 0.00 | 0.55 |
| B1 single reference (K=1) | T3 | 25% | 0.44 | 10 | 20 | 0.73 | 0.73 | 0.00 | 0.57 |
| B1 single reference (K=1) | T4 | 27% | 0.19 | 20 | 20 | 0.94 | 0.94 | 0.00 | 0.42 |
| B1 single reference (K=1) | T6 | 27% | 0.12 | 25 | 20 | 2.15 | 2.15 | 0.00 | 0.47 |
| B2 envelope (K=all), ours | T1 (calib) | 37% | 0.37 | 10 | 30 | 0.90 | 0.75 | 0.00 | 0.59 |
| B2 envelope (K=all), ours | T2 | 40% | 0.43 | 30 | 45 | 2.03 | 2.03 | 0.08 | 0.61 |
| B2 envelope (K=all), ours | T3 | 30% | 0.49 | 45 | 20 | 1.47 | 1.62 | 0.00 | 0.54 |
| B2 envelope (K=all), ours | T4 | 35% | 0.31 | 30 | 40 | 0.24 | 0.24 | 0.32 | 0.51 |
| B2 envelope (K=all), ours | T6 | 23% | 0.16 | 10 | 20 | 2.15 | 1.97 | 0.02 | 0.42 |

### Matching Score by flaw type (T2 / T3 / T4 / T6)

| Method | misplaced_pause | missed_emphasis | missing_pause | monotone | pace | volume_fade |
|---|---|---|---|---|---|---|
| B0 generic norms | 40% / 40% / 40% / 50% | 0% / 0% / 0% / 0% | 0% / 0% / 0% / 0% | 40% / 40% / 50% / 30% | 30% / 0% / 0% / 0% | 0% / 0% / 0% / 0% |
| B1 single reference (K=1) | 70% / 70% / 60% / 80% | 0% / 0% / 0% / 0% | 0% / 20% / 10% / 10% | 20% / 20% / 60% / 30% | 40% / 30% / 10% / 10% | 50% / 10% / 20% / 30% |
| B2 envelope (K=all), ours | 70% / 70% / 60% / 80% | 30% / 0% / 0% / 0% | 10% / 20% / 10% / 20% | 40% / 20% / 40% / 10% | 50% / 50% / 60% / 0% | 40% / 20% / 40% / 30% |

### Per-flaw precision / recall, B2 (T2 / T3 / T4 / T6): recall = Matching Score (type + IoU >= 0.5); precision = share of flags overlapping a label of the same type (raw, then excluding flags the untouched source also gets)

| Type | T2 R / P raw / P edit | T3 R / P raw / P edit | T4 R / P raw / P edit | T6 R / P raw / P edit |
|---|---|---|---|---|
| misplaced_pause | 70% / 100% / 100% (n=7) | 70% / 100% / 100% (n=7) | 60% / 100% / 100% (n=6) | 80% / 100% / 100% (n=8) |
| missed_emphasis | 30% / 100% / 100% (n=3) | 0% / n/a / n/a (n=0) | 0% / n/a / n/a (n=0) | 0% / n/a / n/a (n=0) |
| missing_pause | 10% / 100% / 100% (n=1) | 20% / 100% / 100% (n=2) | 10% / 100% / 100% (n=1) | 20% / 100% / 100% (n=2) |
| monotone | 40% / 100% / 100% (n=4) | 20% / 100% / 100% (n=3) | 40% / 11% / 100% (n=62) | 10% / 100% / 100% (n=2) |
| pace | 50% / 15% / 64% (n=46) | 50% / 75% / 75% (n=8) | 60% / 35% / 35% (n=17) | 0% / 1% / 25% (n=119) |
| volume_fade | 40% / 100% / 100% (n=5) | 20% / 100% / 100% (n=2) | 40% / 57% / 57% (n=7) | 30% / 100% / 100% (n=3) |

### Matching Score at equal false-alarm budgets (best sweep point at or below the budget)

| Text | Method | <= 0.25/min | <= 0.5/min | <= 1/min | <= 2/min |
|---|---|---|---|---|---|
| T2 | B1 single reference | 22% | 22% | 30% | 30% |
| T2 | B2 envelope | 15% | 15% | 30% | 30% |
| T3 | B1 single reference | 13% | 13% | 25% | 25% |
| T3 | B2 envelope | 7% | 7% | 18% | 30% |
| T4 | B1 single reference | 17% | 17% | 27% | 27% |
| T4 | B2 envelope | 35% | 35% | 35% | 35% |
| T6 | B1 single reference | 15% | 15% | 15% | 15% |
| T6 | B2 envelope | 5% | 5% | 5% | 17% |

### Matching Score by injected severity (T2 / T3 / T4 / T6)

| Method | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| B0 generic norms | 8% / 0% / 0% / 0% | 0% / 8% / 8% / 0% | 0% / 8% / 8% / 8% | 42% / 25% / 25% / 25% | 42% / 25% / 33% / 33% |
| B1 single reference (K=1) | 0% / 0% / 8% / 0% | 8% / 8% / 8% / 17% | 33% / 17% / 25% / 17% | 50% / 33% / 25% / 33% | 58% / 67% / 67% / 67% |
| B2 envelope (K=all), ours | 0% / 0% / 0% / 0% | 8% / 8% / 8% / 17% | 33% / 25% / 33% / 25% | 75% / 50% / 58% / 25% | 83% / 67% / 75% / 50% |

### Ablations (T2 / T3 / T4 / T6)

| Variant | Matching Score | FA/min good pairs | FA/min null-edit |
|---|---|---|---|
| K=1 | 30% / 25% / 27% / 27% | 0.90 / 0.73 / 0.94 / 2.15 | 0.90 / 0.73 / 0.94 / 2.15 |
| K=2 | 32% / 22% / 35% / 27% | 1.35 / 1.62 / 1.18 / 3.76 | 1.58 / 1.91 / 1.18 / 4.65 |
| K=4 | 37% / 25% / 32% / 27% | 0.68 / 0.59 / 0.47 / 1.07 | 0.90 / 0.59 / 0.24 / 1.07 |
| K=all | 40% / 30% / 35% / 23% | 2.03 / 1.47 / 0.24 / 2.15 | 2.03 / 1.62 / 0.24 / 1.97 |
| no null-edit margin | 40% / 30% / 35% / 23% | 1.35 / 1.17 / 0.24 / 1.97 | 1.58 / 1.17 / 0.24 / 1.97 |
| norm off | 35% / 27% / 32% / 20% | 2.26 / 1.47 / 0.47 / 2.68 | 2.03 / 1.62 / 0.24 / 2.68 |
| norm z-score (v1) | 23% / 25% / 30% / 28% | 1.81 / 1.62 / 2.12 / 2.50 | 1.81 / 1.62 / 1.65 / 2.33 |
| v1 detector (frozen design) | 30% / 32% / 23% / 27% | 1.35 / 1.32 / 1.65 / 1.43 | 1.35 / 1.32 / 1.65 / 1.43 |
| v2 without relative channels | 32% / 25% / 23% / 28% | 0.68 / 1.32 / 0.94 / 1.07 | 0.68 / 1.47 / 0.71 / 0.89 |
| v2 without stress floor | 40% / 35% / 35% / 23% | 2.26 / 1.62 / 0.47 / 2.15 | 2.03 / 1.76 / 0.47 / 1.97 |

### Compound clips (T2 / T3 / T4 / T6)

- B0 generic norms: Matching Score 38% / 50% / 38% / 38%
- B1 single reference (K=1): Matching Score 38% / 50% / 38% / 38%
- B2 envelope (K=all), ours: Matching Score 38% / 50% / 62% / 12%

### Natural spectrum and listening test

- T2: pending human ranking (data/rankings/<T>.csv); Spearman = n/a
- T3: pending human ranking (data/rankings/<T>.csv); Spearman = n/a
- T4: pending human ranking (data/rankings/<T>.csv); Spearman = n/a
- T6: pending human ranking (data/rankings/<T>.csv); Spearman = n/a
- Listening test: pending: no responses yet

### Natural flaws (teammate takes)

- Status: pending: no takes in data/takes/<T>/

### Robustness (T4 ladders, severities 3 and 5, envelope K=all)

| Condition | Matching Score | Time F1 | Onset err (ms) |
|---|---|---|---|
| clean | 54% | 0.41 | 30 |
| noise_20 | 50% | 0.20 | 60 |
| noise_10 | 25% | 0.12 | 85 |
| mp3_64k | 54% | 0.41 | 30 |
| telephone_band | 62% | 0.23 | 40 |
| wrong_word | 58% | 0.45 | 35 |

### Robustness (T6 ladders, severities 3 and 5, envelope K=all)

| Condition | Matching Score | Time F1 | Onset err (ms) |
|---|---|---|---|
| clean | 38% | 0.25 | 10 |
| noise_20 | 33% | 0.18 | 33 |
| noise_10 | 25% | 0.07 | 105 |
| mp3_64k | 38% | 0.25 | 10 |
| telephone_band | 38% | 0.20 | 10 |
| wrong_word | 38% | 0.21 | 10 |
