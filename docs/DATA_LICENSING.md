# Data licensing and provenance

| Material | Licence | Evidence | May we crop, modify, publish? |
|---|---|---|---|
| LibriVox readings (T1-T4, T5 reader) | Public domain (Public Domain Mark 1.0) | `data/raw/<T>/sources.json`: project id, section, URL | Yes |
| FDR "Day of Infamy" original (T5) | Public domain: US federal government work; Commons PD, `Copyrighted=False` | NARA record 10611614 ("Unrestricted"); Commons sha1 recorded and checked on download | Yes (US). Check local law outside the US. |
| Texts T1-T5 | Public domain in the US (published before 1929, or a federal work) | `cadence/data/texts.py` | Yes |
| Derived clips (crops, ladders, null-edits) | Same as their source; released as public domain | `data/labels/labels.csv`: `licence` and `provenance` per clip | Yes |
| Teammate takes | CC0 1.0, by signed consent | `data/consent/<name>.pdf` (form: `data/consent/CONSENT_FORM.md`) | Only with a consent form on file |
| Human ratings and annotations | CC0 1.0, contributed by the team | `data/rankings/`, `data/listening/`, `data/annotations/` | Yes; names are stored lower-cased; use initials if preferred |
| TED / TEDx talks | CC BY-NC-ND 4.0 | TED Talks usage policy: "you cannot edit, remix, create, modify or alter ... including by sharing truncated versions or clips" | **No.** Candidate links only (`data/sources/tedx_candidates.csv`). Nothing downloaded. |

TED/TEDx would need written permission from TED, and for TEDx also from the event organizer,
covering analysis, modification, storage, testing and distribution. TED/TEDx also has a
structural problem: each talk exists as one performance, so it cannot form a same-text envelope
unless several people re-perform the same transcript. The transcript is itself copyrighted, so
re-performing it needs the same permission.
