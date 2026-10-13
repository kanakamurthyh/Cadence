## Results (all numbers as measured; thresholds fitted on T1 only)

| Method | Text | Matching Score | Time F1 | Onset err (ms) | Offset err (ms) | FA/min good pairs | FA/min null-edit | Severity rho |
|---|---|---|---|---|---|---|---|---|
| B0 generic norms | T1 (calib) | 15% | 0.02 | 10 | 60 | 22.42 | 22.12 | 0.18 |
| B0 generic norms | T2 | 18% | 0.03 | 160 | 48 | 26.20 | 26.65 | 0.39 |
| B0 generic norms | T3 | 13% | 0.04 | 145 | 10 | 16.89 | 17.62 | 0.21 |
| B1 single reference (K=1) | T1 (calib) | 22% | 0.38 | 10 | 30 | 0.75 | 0.75 | 0.40 |
| B1 single reference (K=1) | T2 | 20% | 0.19 | 25 | 40 | 0.68 | 0.68 | 0.33 |
| B1 single reference (K=1) | T3 | 18% | 0.33 | 0 | 20 | 0.15 | 0.15 | 0.42 |
| B2 envelope (K=all), ours | T1 (calib) | 32% | 0.21 | 10 | 30 | 0.90 | 0.90 | 0.38 |
| B2 envelope (K=all), ours | T2 | 30% | 0.48 | 20 | 40 | 1.35 | 1.35 | 0.36 |
| B2 envelope (K=all), ours | T3 | 32% | 0.48 | 0 | 20 | 1.32 | 1.32 | 0.32 |

### Matching Score by flaw type (T2 / T3)

| Method | pace | missing_pause | misplaced_pause | monotone | missed_emphasis | volume_fade |
|---|---|---|---|---|---|---|
| B0 generic norms | 30% / 0% | 0% / 0% | 40% / 40% | 40% / 40% | 0% / 0% | 0% / 0% |
| B1 single reference (K=1) | 0% / 0% | 0% / 20% | 70% / 70% | 0% / 0% | 0% / 0% | 50% / 20% |
| B2 envelope (K=all), ours | 0% / 0% | 20% / 20% | 90% / 100% | 0% / 0% | 40% / 50% | 30% / 20% |

### Matching Score by injected severity (T2 / T3)

| Method | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| B0 generic norms | 8% / 0% | 0% / 8% | 0% / 8% | 42% / 25% | 42% / 25% |
| B1 single reference (K=1) | 0% / 0% | 8% / 8% | 25% / 17% | 33% / 25% | 33% / 42% |
| B2 envelope (K=all), ours | 8% / 17% | 25% / 25% | 25% / 25% | 33% / 25% | 58% / 67% |

### Ablations (T2 / T3)

| Variant | Matching Score | FA/min good pairs | FA/min null-edit |
|---|---|---|---|
| K=1 | 20% / 18% | 0.68 / 0.15 | 0.68 / 0.15 |
| K=2 | 20% / 18% | 0.90 / 0.88 | 0.90 / 1.03 |
| K=4 | 27% / 23% | 0.68 / 1.17 | 0.68 / 1.03 |
| K=all | 30% / 32% | 1.35 / 1.32 | 1.35 / 1.32 |
| norm off | 25% / 28% | 1.35 / 1.17 | 1.35 / 1.17 |
| norm z-score (v1) | 20% / 28% | 0.90 / 1.32 | 0.90 / 1.32 |
| no null-edit margin | 32% / 33% | 1.35 / 1.17 | 1.35 / 1.17 |

### Compound clips

- B0 generic norms: Matching Score 38% (T2), 50% (T3)
- B1 single reference (K=1): Matching Score 12% (T2), 25% (T3)
- B2 envelope (K=all), ours: Matching Score 12% (T2), 50% (T3)

### Natural spectrum and listening test

- T2: pending human ranking (data/rankings/<T>.csv); Spearman = n/a
- T3: pending human ranking (data/rankings/<T>.csv); Spearman = n/a
- Listening test: pending: no responses yet
