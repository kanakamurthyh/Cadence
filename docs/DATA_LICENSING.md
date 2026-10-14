# Data licensing and provenance

| Material | Licence | Evidence | May we crop, modify, publish? |
|---|---|---|---|
| LibriVox readings (T1-T4, T5 reader, T6, T8) | Public domain (Public Domain Mark 1.0) | `data/raw/<T>/sources.json`: project id, section, URL | Yes |
| FDR "Day of Infamy" original (T5) | Public domain: US federal government work; Commons PD, `Copyrighted=False` | NARA record 10611614 ("Unrestricted"); Commons sha1 recorded and checked on download | Yes (US). Check local law outside the US. |
| Speech Accent Archive recordings (T7) | CC BY-NC-SA 4.0 — "the contents of this project are made availalbe under the BY-NC-SA 4.0 license from Creative Commons" (http://accent.gmu.edu/howto/) — © The Speech Accent Archive, Steven H. Weinberger and Matthew C. Kelley, George Mason University | `data/raw/T7/sources.json`: speaker page URL, sha1, L1 and birthplace per file | **Non-commercial only; share-alike.** T7 audio and every clip derived from it (ladders, crops) is CC BY-NC-SA 4.0 and must be published as a separate subset with that licence. No commercial redistribution. |
| Texts T1-T5, T8 (Tagore 1916) | Public domain in the US (published before 1929, or a federal work) | `cadence/data/texts.py` | Yes |
| Text T7 (SAA elicitation paragraph) | © George Mason University; distributed under CC BY-NC-SA 4.0 with the audio | http://accent.gmu.edu/howto/ | Non-commercial only |
| Derived clips (crops, ladders, null-edits) from T1-T6, T8 | Same as their source; released as public domain | `data/labels/labels.csv`: `licence` and `provenance` per clip | Yes |
| Derived clips from T7 | CC BY-NC-SA 4.0 (inherits from T7 source) | `data/labels/labels.csv`: `licence` per clip | Non-commercial only; share-alike |
| Teammate takes | CC0 1.0, by signed consent | `data/consent/<name>.pdf` (form: `data/consent/CONSENT_FORM.md`) | Only with a consent form on file |
| Human ratings and annotations | CC0 1.0, contributed by the team | `data/rankings/`, `data/listening/`, `data/annotations/` | Yes; names are stored lower-cased; use initials if preferred |
| TED / TEDx talks | CC BY-NC-ND 4.0 | TED Talks usage policy: "you cannot edit, remix, create, modify or alter ... including by sharing truncated versions or clips" | **No.** Candidate links only (`data/sources/tedx_candidates.csv`). Nothing downloaded. |

TED/TEDx would need written permission from TED, and for TEDx also from the event organizer,
covering analysis, modification, storage, testing and distribution. TED/TEDx also has a
structural problem: each talk exists as one performance, so it cannot form a same-text envelope
unless several people re-perform the same transcript. The transcript is itself copyrighted, so
re-performing it needs the same permission.

## T7 speaker details (Speech Accent Archive, CC BY-NC-SA 4.0)

All 12 T7 speakers were born in India. Selected to cover 6 major Indian L1 languages (2 speakers
each). None of these speakers or their recordings appear in any calibration text.

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

**Why held out:** T7 and T8 were added 2026-10-14 after detector v3 was designed. Neither text
was used to choose thresholds, margins, or any other parameter. T7/T8 are held out as an
Indian-speaker generalization test.

**Important:** T7 audio and every clip derived from it (crops, PSOLA ladders) is CC BY-NC-SA 4.0.
It must be published as a separate subset with that licence clearly stated. No commercial
redistribution of T7 material is permitted.

## T8 (LibriVox Tagore, Public Domain)

T8 uses 16 readings of poem XVIII from *Fruit-Gathering* (Rabindranath Tagore, 1916) published
by LibriVox (project 17632). The text is public domain (Tagore 1916, US PD). All LibriVox
recordings are released under Public Domain Mark 1.0. No restrictions on use, modification or
redistribution.
