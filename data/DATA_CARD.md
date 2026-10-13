# Cadence dataset v1: data card

## Contents

| Folder | What | Count |
|---|---|---|
| `refs/<T>/<id>.wav` | Each reading cropped to the text: 16 kHz mono, −23 LUFS | 24 (T1), 23 (T2), 19 (T3), 19 (T4), 2 (T5) |
| `refs/<T>/<id>.json` | Word alignment, snapped word edges, per-word features, reader metadata, aligner confidence | same |
| `refs/<T>/selection.json` | Reader ranking and the good set (top 6), plus how the ranking was made | 3 |
| `ladders/<T>/<clip>.wav` | Synthetic clips: 6 flaw types × 2 spans × 5 severities, null-edit copies of every good rendition, compound clips | ~200 |
| `ladders/<T>/<clip>.json` | Measured alignment and features of the clip; `meta.labels` holds exact word-span labels | same |
| `ladders/<T>/manifest.json` | Every clip with its source rendition, flaws (type, severity, word span) and labels in clip time | 3 |
| `listening/responses.csv` | Listening-test ratings, 0–4: `listener,clip,type,level,rating,source,time` (created by `cadence human`) | pending |
| `rankings/<T>_ratings.csv`, `rankings/<T>.csv` | Raw 1–10 scores per rater; derived ranks, one column per rater (created by `cadence human`) | pending |
| `takes/<T>/<speaker>_<T>_take<n>.*` | Teammate readings with natural flaws (test only) | pending |
| `annotations/<annotator>/<take_id>.txt` | Audacity label files: `start<TAB>end<TAB>flaw_type`, two independent annotators | pending |
| `labels/labels.jsonl`, `labels/labels.csv` | One row per label, clean reference and null-edit control: file, text, speaker, reference, type, injected (and later perceived) severity, times, word span, original and modified feature values, transformation, licence | 296 rows |
| `labels/validation.json` | Automated checks (bounds, time map, duration, direction, clicks, attribution) and the severity distribution | 1 |
| `inventory.csv`, `inventory.json` | Every recording: source URL, licence, provenance, raw file, crop offset, alignment quality, good-set membership; speaker overlap | 87 rows |
| `raw/T5/fdr_original_1941.ogg` | FDR original, Wikimedia Commons, sha1-checked | 1 |
| `sources/tedx_candidates.csv` | TEDx talks recorded as candidates only (CC BY-NC-ND, not downloaded) | 2 |
| `consent/` | Consent form template; signed forms for teammate takes | template |
| `params.json` | Everything fitted on T1 and frozen: m_f, s_f, τ, λ_d, severity map | 1 |

## Texts and roles

| Text | Passage | Renditions | Role |
|---|---|---|---|
| T1 | *Sea Fever* | 24 LibriVox | Calibration only |
| T2 | *Stopping by Woods* | 23 LibriVox | Held-out test |
| T3 | Gettysburg Address, closing paragraph | 19 LibriVox | Held-out test (oratory) |
| T4 | Gettysburg Address, opening paragraph | Same 19 readings as T3 | Held-out test (oratory); shares speakers with T3, not with calibration |
| T5 | FDR "Day of Infamy", opening | FDR original + 1 LibriVox | Held-out test; excluded until ≥ 4 renditions |
| T6 | Kipling, *If—*, first two stanzas | 15 LibriVox (2 of 17 downloads failed) | **Untouched final test**: added 2026-10-14 after detector v2 was frozen; no speaker shared with any text |

No speaker in T1's good set (the only T1 audio calibration uses) appears in any test text.
`cadence inventory` checks this.

## Texts and licences

- **T1:** *Sea Fever*, John Masefield (1902).
- **T2:** *Stopping by Woods on a Snowy Evening*, Robert Frost (1923).
- **T3:** Gettysburg Address, closing paragraph, Abraham Lincoln (1863).

All texts are public domain in the US. All recordings are LibriVox recordings, released into
the public domain ([LibriVox licence](https://librivox.org/pages/public-domain/)). Reader names
are LibriVox display names, as published. Derived clips (crops, ladders) are released into
the public domain on the same terms.

## Flaw injection (fixed seed 20261013 + text number)

Each flaw is injected into the top-ranked good rendition. Every clip, including the clean
null-edit copies, is resynthesized through the same Praat PSOLA pass, so clean and flawed
audio share processing artifacts.

| Type | Edit | Severity 1 → 5 |
|---|---|---|
| Pace (rushed / dragging) | PSOLA duration change over 4–7 words, pitch kept | ×0.9 → ×0.55 / ×1.1 → ×1.8 |
| Missing pause | Phrase-boundary silence (≥ 0.3 s) shortened | 20% → 100% removed |
| Misplaced pause | Room-tone silence inserted between two mid-phrase words | 0.3 → 2.0 s |
| Monotone | Pitch compressed toward the span median (semitone scale) | 80% → 10% of range kept |
| Missed emphasis | Pitch above the neighbours' median, and the loudness excess, flattened on one consensus stress point | 80% → 0% of the peak kept |
| Volume fade | Gain ramp down over the first quarter of the span, held to the end | −3 → −18 dB |

**Label spans:**
- Pace, monotone, fade and emphasis: the edited words.
- Missing pause: the two words around the boundary.
- Misplaced pause: the inserted silence itself.

**Label precision.**
- Time-stretch labels are exact: an analytic time map, checked against the final audio length
  by `cadence labels`.
- Cut and insert labels are exact to within the 10 ms crossfade at each join.
- Word attribution comes from the source alignment. On T1 one misplaced-pause span
  (`T1_misplaced_pause_s0_*`) has its silence after word 17, not word 16. Its time span is
  correct, and the validator reports it.
- Texts from T4 on use span rule 2, which avoids gapless boundaries next to very short words.

**Leakage rule:** the edited rendition is excluded from the envelope when its own ladder is scored.

## Version history

| Version | Emphasis targets | `--dataset` flag |
|---|---|---|
| v2 | Any consensus prominence: ≥ 75 % of good readers have any positive `prom_pitch` or `prom_loud` | `--dataset 2` |
| v3 | Perceptible consensus stress only: ≥ 75 % of good readers peak by ≥ 1.5 st (pitch) or ≥ 1 dB (loudness) | `--dataset 3` (default) |

## Known limitations

- The good set is provisionally ranked by aligner confidence until the 3-rater human ranking
  exists (see `selection.json` → `method`).
- Severities are injected levels, not perceived levels, until the listening test is run.
- LibriVox readers are amateurs; T3 has no recording of the original orator, and none exists.
- Readings follow slightly different editions of each text. Words a reader changed are
  force-aligned to the canonical text, which adds noise to those words.
