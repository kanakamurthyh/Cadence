## Results (all numbers as measured; thresholds fitted on T1 only)

| Method | Text | Matching Score | Time F1 | Onset err (ms) | Offset err (ms) | FA/min good pairs | FA/min null-edit | Severity rho |
|---|---|---|---|---|---|---|---|---|
| B0 generic norms | T1 (calib) | 15% | 0.02 | 10 | 60 | 22.42 | 22.12 | 0.18 |
| B0 generic norms | T2 | 18% | 0.03 | 160 | 48 | 26.20 | 26.65 | 0.39 |
| B0 generic norms | T3 | 13% | 0.04 | 145 | 10 | 16.89 | 17.62 | 0.21 |
| B0 generic norms | T4 | 15% | 0.06 | 30 | 50 | 19.34 | 19.11 | 0.22 |
| B1 single reference (K=1) | T1 (calib) | 22% | 0.38 | 10 | 30 | 0.75 | 0.75 | 0.40 |
| B1 single reference (K=1) | T2 | 20% | 0.19 | 25 | 40 | 0.68 | 0.68 | 0.33 |
| B1 single reference (K=1) | T3 | 18% | 0.33 | 0 | 20 | 0.15 | 0.15 | 0.42 |
| B1 single reference (K=1) | T4 | 17% | 0.27 | 25 | 40 | 0.47 | 0.47 | 0.41 |
| B2 envelope (K=all), ours | T1 (calib) | 32% | 0.21 | 10 | 30 | 0.90 | 0.90 | 0.38 |
| B2 envelope (K=all), ours | T2 | 30% | 0.48 | 20 | 40 | 1.35 | 1.35 | 0.36 |
| B2 envelope (K=all), ours | T3 | 32% | 0.48 | 0 | 20 | 1.32 | 1.32 | 0.32 |
| B2 envelope (K=all), ours | T4 | 23% | 0.11 | 20 | 45 | 1.65 | 1.65 | 0.40 |

### Matching Score by flaw type (T2 / T3 / T4)

| Method | pace | missing_pause | misplaced_pause | monotone | missed_emphasis | volume_fade |
|---|---|---|---|---|---|---|
| B0 generic norms | 30% / 0% / 0% | 0% / 0% / 0% | 40% / 40% / 40% | 40% / 40% / 50% | 0% / 0% / 0% | 0% / 0% / 0% |
| B1 single reference (K=1) | 0% / 0% / 0% | 0% / 20% / 10% | 70% / 70% / 60% | 0% / 0% / 0% | 0% / 0% / 0% | 50% / 20% / 30% |
| B2 envelope (K=all), ours | 0% / 0% / 0% | 20% / 20% / 20% | 90% / 100% / 80% | 0% / 0% / 0% | 40% / 50% / 10% | 30% / 20% / 30% |

### Matching Score by injected severity (T2 / T3 / T4)

| Method | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| B0 generic norms | 8% / 0% / 0% | 0% / 8% / 8% | 0% / 8% / 8% | 42% / 25% / 25% | 42% / 25% / 33% |
| B1 single reference (K=1) | 0% / 0% / 0% | 8% / 8% / 0% | 25% / 17% / 17% | 33% / 25% / 25% | 33% / 42% / 42% |
| B2 envelope (K=all), ours | 8% / 17% / 0% | 25% / 25% / 17% | 25% / 25% / 17% | 33% / 25% / 33% | 58% / 67% / 50% |

### Ablations (T2 / T3 / T4)

| Variant | Matching Score | FA/min good pairs | FA/min null-edit |
|---|---|---|---|
| K=1 | 20% / 18% / 17% | 0.68 / 0.15 / 0.47 | 0.68 / 0.15 / 0.47 |
| K=2 | 20% / 18% / 20% | 0.90 / 0.88 / 1.65 | 0.90 / 1.03 / 1.65 |
| K=4 | 27% / 23% / 22% | 0.68 / 1.17 / 0.71 | 0.68 / 1.03 / 0.71 |
| K=all | 30% / 32% / 23% | 1.35 / 1.32 / 1.65 | 1.35 / 1.32 / 1.65 |
| norm off | 25% / 28% / 18% | 1.35 / 1.17 / 1.65 | 1.35 / 1.17 / 1.65 |
| norm z-score (v1) | 20% / 28% / 27% | 0.90 / 1.32 / 0.71 | 0.90 / 1.32 / 0.94 |
| no null-edit margin | 32% / 33% / 25% | 1.35 / 1.17 / 1.65 | 1.35 / 1.17 / 1.65 |

### Compound clips (T2 / T3 / T4)

- B0 generic norms: Matching Score 38% / 50% / 38%
- B1 single reference (K=1): Matching Score 12% / 25% / 25%
- B2 envelope (K=all), ours: Matching Score 12% / 50% / 38%

### Natural spectrum and listening test

- T2: pending human ranking (data/rankings/<T>.csv); Spearman = n/a
- T3: pending human ranking (data/rankings/<T>.csv); Spearman = n/a
- T4: pending human ranking (data/rankings/<T>.csv); Spearman = n/a
- Listening test: pending: no responses yet

### Natural flaws (teammate takes)

- Status: pending: no takes in data/takes/<T>/

### Robustness (T2 ladders, severities 3 and 5, envelope K=all)

| Condition | Matching Score | Time F1 | Onset err (ms) |
|---|---|---|---|
| clean | 42% | 0.59 | 15 |
| noise_20 | 29% | 0.42 | 80 |
| noise_10 | 21% | 0.10 | 70 |
| mp3_64k | 42% | 0.59 | 15 |
| wrong_word | 42% | 0.59 | 15 |
| telephone_band | 29% | 0.45 | 20 |

### Robustness (T4 ladders, severities 3 and 5, envelope K=all)

| Condition | Matching Score | Time F1 | Onset err (ms) |
|---|---|---|---|
| clean | 33% | 0.16 | 20 |
| noise_20 | 25% | 0.08 | 70 |
| noise_10 | 17% | 0.04 | 75 |
| mp3_64k | 33% | 0.16 | 20 |
| telephone_band | 29% | 0.13 | 40 |
| wrong_word | 33% | 0.16 | 20 |
