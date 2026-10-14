# Cadence dataset v3: data card

Public copy: [huggingface.co/datasets/Vedant1605/cadence-contrastive-speech](https://huggingface.co/datasets/Vedant1605/cadence-contrastive-speech),
in two subsets with different licences: `public_domain` (T1–T6, T8; LibriVox and NARA) and
`saa_indian_nc_sa` (T7; CC BY-NC-SA 4.0). Totals from `inventory.json`: 132 recordings,
443 synthetic clips.

## Contents

| Folder | What | Count |
|---|---|---|
| `refs/<T>/<id>.wav` | Each reading cropped to the text: 16 kHz mono, −23 LUFS | 24 (T1), 23 (T2), 19 (T3), 19 (T4), 2 (T5), 17 (T6), 12 (T7), 16 (T8) |
| `refs/<T>/<id>.json` | Word alignment, snapped word edges, per-word features, reader metadata, aligner confidence | same |
| `refs/<T>/selection.json` | Reader ranking and the good set (top 6), plus how the ranking was made | 8 |
| `ladders/<T>/<clip>.wav` | Synthetic clips: 6 flaw types × 2 spans × 5 severities, null-edit copies of every good rendition, compound clips (dataset v3) | 443: T1 63, T2 65, T3 70, T4 65, T6 65, T7 55, T8 60 |
| `ladders/<T>/<clip>.json` | Measured alignment and features of the clip; `meta.labels` holds exact word-span labels | same |
| `ladders/<T>/manifest.json` | Every clip with its source rendition, flaws (type, severity, word span), `dataset_version` and labels in clip time | 7 |
| `listening/responses.csv` | Listening-test ratings, 0–4: `listener,clip,type,level,rating,source,time` (created by `cadence human`) | pending |
| `rankings/<T>_ratings.csv`, `rankings/<T>.csv` | Raw 1–10 scores per rater; derived ranks, one column per rater (created by `cadence human`) | pending |
| `takes/<T>/<speaker>_<T>_take<n>.*` | Teammate readings with natural flaws (test only) | pending |
| `annotations/<annotator>/<take_id>.txt` | Audacity label files: `start<TAB>end<TAB>flaw_type`, two independent annotators | pending |
| `labels/labels.jsonl`, `labels/labels.csv` | One row per label, clean reference and null-edit control: file, text, speaker, reference, type, injected (and later perceived) severity, times, word span, original and modified feature values, transformation, licence | 476 rows |
| `labels/validation.json` | Automated checks (bounds, time map, duration, direction, clicks, attribution) and the severity distribution | 1 |
| `inventory.csv`, `inventory.json` | Every recording: source URL, licence, provenance, raw file, crop offset, alignment quality, good-set membership; speaker overlap | 132 rows |
| `raw/T5/fdr_original_1941.ogg` | FDR original, Wikimedia Commons, sha1-checked | 1 |
| `sources/tedx_candidates.csv` | TEDx talks recorded as candidates only (CC BY-NC-ND, not downloaded) | 2 |
| `consent/` | Consent form template; signed forms for teammate takes | template |
| `params.json` | Everything fitted on T1 and frozen: m_f, s_f, τ, λ_d, severity map | 1 |

## Texts and roles

| Text | Passage | Renditions | Role |
|---|---|---|---|
| T1 | *Sea Fever* | 24 LibriVox | Calibration only |
| T2 | *Stopping by Woods* | 23 LibriVox | Development test |
| T3 | Gettysburg Address, closing paragraph | 19 LibriVox | Development test (oratory) |
| T4 | Gettysburg Address, opening paragraph | Same 19 readings as T3 | Development test (oratory); **not independent of T3** (same readers), none shared with calibration |
| T5 | FDR "Day of Infamy", opening | FDR original + 1 LibriVox | **Blocked** until ≥ 4 renditions |
| T6 | Kipling, *If—*, first two stanzas | 17 LibriVox (15 before the 2026-10-14 rebuild, when 2 downloads failed) | Test; used once for v2, so no longer untouched; no speaker shared with any text |
| T7 | SAA "Please Call Stella" elicitation | 12 Speech Accent Archive (India-born speakers) | **Held-out Indian-speaker test (Speech Accent Archive)**: added 2026-10-14 after detector v3 was designed; evaluated once; never used for calibration |
| T8 | Tagore *Fruit-Gathering* XVIII | 16 LibriVox (project 17632) | **Held-out Indian-authored text** (readers not confirmed Indian-accented): added 2026-10-14 after detector v3 was designed; evaluated once; never used for calibration |

No speaker in T1's good set (the only T1 audio calibration uses) appears in any test text.
`cadence inventory` checks this.

## Texts and licences

- **T1:** *Sea Fever*, John Masefield (1902).
- **T2:** *Stopping by Woods on a Snowy Evening*, Robert Frost (1923).
- **T3:** Gettysburg Address, closing paragraph, Abraham Lincoln (1863).
- **T6:** *If—* (first two stanzas), Rudyard Kipling (1910).
- **T8:** *Fruit-Gathering* poem XVIII, Rabindranath Tagore (1916).

All of the above texts are public domain in the US. Their recordings are LibriVox recordings,
released into the public domain ([LibriVox licence](https://librivox.org/pages/public-domain/)).
Reader names are LibriVox display names, as published. Derived clips (crops, ladders) are
released into the public domain on the same terms.

- **T7:** "Please Call Stella" elicitation paragraph, Speech Accent Archive (GMU). Recordings
  are CC BY-NC-SA 4.0 — "the contents of this project are made availalbe under the BY-NC-SA 4.0
  license from Creative Commons" (http://accent.gmu.edu/howto/). T7 audio and every clip derived
  from it (ladders, crops) is CC BY-NC-SA 4.0 and is published as a separate subset with that
  licence. No commercial redistribution.

## T7 Indian-speaker details (held-out; CC BY-NC-SA 4.0)

T7 covers 12 India-born speakers across 6 L1 languages (2 per language). Added 2026-10-14 after
detector v3 was designed. Never used for calibration.

| ID | L1 | Birthplace | Sex | Age | English onset |
|---|---|---|---|---|---|
| saa_hindi1 | Hindi | Nagpur, Maharashtra, India | M | 27 | 2 (academic) |
| saa_hindi2 | Hindi | Hyderabad, India | M | 31 | 3 (academic) |
| saa_bengali6 | Bengali | Jamshedpur, Jharkhand, India | M | 29 | 4 (naturalistic) |
| saa_bengali9 | Bengali | Kolkata, India | F | 61 | 12 (academic) |
| saa_telugu1 | Telugu | Kadapa, India | M | 31 | 6 (academic) |
| saa_telugu2 | Telugu | Guntur, Andhra Pradesh, India | M | 18 | 6 (academic) |
| saa_tamil2 | Tamil | Madras, Tamil Nadu, India | F | 35 | 4 (naturalistic) |
| saa_tamil5 | Tamil | Coimbatore, Tamil Nadu, India | F | 36 | 5 (academic) |
| saa_marathi1 | Marathi | Bombay, India | F | 21 | 3 (academic) |
| saa_marathi2 | Marathi | Madras, India | M | 28 | 10 (academic) |
| saa_malayalam1 | Malayalam | Kerala State, India | M | 24 | 5 (academic) |
| saa_malayalam2 | Malayalam | Trivandrum, Kerala, India | F | 29 | 5 (academic) |

## T8 (LibriVox Tagore; held-out; public domain)

T8 uses 16 readings of *Fruit-Gathering* poem XVIII (Rabindranath Tagore, 1916) from LibriVox
project 17632. Text and recordings are public domain. Added 2026-10-14 after detector v3 was
designed; never used for calibration.

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
| Missed emphasis | Pitch above the neighbours' median, and the loudness excess, flattened on one perceptible consensus stress point (dataset v3) | 80% → 0% of the peak kept |
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

Under v3, T3 has 2 emphasis spans, T1/T2/T4/T6 have 1, and T7/T8 have none (the injector found no
eligible perceptible consensus stress point), so T7 and T8 carry no missed-emphasis clips.
A from-scratch rebuild of v2 (fetch → refs → ladders) reproduced all 371 v2 label rows with
identical clip ids and timestamps; 29 rows' measured effect values differed by
floating-point drift (median 1.4 %, max 21 %); see `results/rebuild_check_2026-10-14.md`.

## Known limitations

- The good set is provisionally ranked by aligner confidence until the 3-rater human ranking
  exists (see `selection.json` → `method`).
- T7's good set is chosen by an English aligner's confidence, which is itself accent-sensitive:
  it contains no Hindi speaker. T8's LibriVox readers are not confirmed Indian-accented, and
  some also read T1–T4 (`inventory.json` → `speaker_overlap`).
- Severities are injected levels, not perceived levels, until the listening test is run.
- LibriVox readers are amateurs; T3 has no recording of the original orator, and none exists.
- Readings follow slightly different editions of each text. Words a reader changed are
  force-aligned to the canonical text, which adds noise to those words.
