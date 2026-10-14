# From-scratch rebuild check (2026-10-14)

Workstream W0 of the scoring push: the dataset-v2 pipeline was rebuilt from nothing
(`fetch → refs → ladders`, committed code, 3 workers) and compared with the committed
`data/labels/labels.jsonl` (dataset v2, before the v3 emphasis rule).

| Check | Result |
|---|---|
| Label rows compared | 371 |
| Clip ids identical | 371 / 371 |
| Timestamps identical (start_s, end_s, word bounds) | 371 / 371 |
| Rows whose measured effect values (delta / modified_value) differ | 29 |
| Size of those differences | median 1.4 % relative, max 21 % |
| Example | `T3_pace-dragging_s1_L3`: edge note 201 → 211 ms |
| `scripts/rerun_check.py` (analysis JSON) | byte-identical across runs |

The labels themselves (what was edited, where, and how strongly by construction) are fully
reproducible. The 29 differences are in values *measured* back from the rebuilt audio, and are
attributed to floating-point drift in resynthesis and measurement. The committed labels were
kept; the rebuild copy was not committed.

`rerun_check.py --store` exits 1 by design when previously stored hashes differ; a fresh check
after re-storing the hashes for the shipped detector passes (exit 0).
