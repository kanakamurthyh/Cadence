# Track C scoring push (2026-10-14, final-submission night)

## Goal

Make the four heaviest Track C criteria visibly strong, with evidence, before the final cutoff
(15 Oct 2026, 00:15 IST). Every number is reported honestly, including regressions.

| Criterion (weight) | What this push adds |
|---|---|
| Data engineering (30%) | Reproduced dataset; v3 emphasis rule; Indian-speaker text(s); severity-gradient evidence; public HF dataset |
| Causal + temporal (25%) | Phrase-level pace/monotone flags with whole-phrase rationale; emphasis detection restored |
| Feature extraction (20%) | Stress points detectable again; phrase F0 range and articulation rate |
| Dashboard (15%) | Demo clip whose flaw is caught live |
| Reproducibility (10%) | From-scratch rebuild checked against committed labels/hashes |

## Constraints

- Thresholds fitted on T1 only; never retuned on T2/T3 (CLAUDE.md).
- Long jobs use `nohup` and at most 3 workers.
- T2–T6 have all informed development once v3 is evaluated; the report says so.
- `project context.md` is updated after every change.

## Workstreams

**W0: Reproduce v2.** fetch → refs → ladders with committed code (`--workers 3`). Compare the
rebuilt labels with `data/labels/labels.jsonl` and run `scripts/rerun_check.py`. Mismatches are
reported, not hidden.

**W1: Dataset v3, emphasis rule.** Root cause of 0% missed-emphasis recall:
`scripts/build_ladders.py` picks targets from v1 stress points (any positive prominence), while
the v2 detector only reads perceptible stress points (≥ 1.5 st / ≥ 1 dB, `STRESS_MIN`) and zeros
d elsewhere. v3 draws missed-emphasis targets from `env.stress_pitch_p | env.stress_loud_p`
("you cannot miss an emphasis nobody makes"). Ladders are rebuilt; `cadence labels` validates;
v2 labels are frozen for comparison; DATA_CARD gets a version history.

**W1b: Indian-speaker data.** Add 1–2 texts with ≥ 4 (ideally 6+) openly licensed renditions by
Indian speakers, chosen from the deep-research report
(`reports/Indian speech dataset sources.md`). Licence must allow derivatives. They enter as
held-out texts (never used for calibration) and as a speaker-agnostic stress test.

**W2: Detector v3, phrase channels.**
- Phrase boundaries: word gaps where ≥ ¾ of the good readers pause (≥ 0.05 s). Text-defined,
  speaker-agnostic, computed once per envelope.
- Per phrase: articulation rate (syllables / speech time, pauses excluded) and F0 range
  (p90 − p10 in semitones), each relative to the reader's own median across phrases.
- Compared with the envelope on the log scale, as the existing rel channels are. A flag covers
  the whole phrase (word-aligned edges). Explanations quote the phrase value against the good
  readers' span.
- `Params.phrase_channels` (default False) keeps v1/v2 reproducible; when True the phrase
  channels replace the word-level rel channels; absolute channels stay.
- Margins, scales and τ fitted on T1 only.

**W3: Evaluate.** Freeze v2 results to `results/frozen_v2_2026-10-14/`, run `cadence evaluate`
and robustness. Ship rule: v3 ships only if it beats v2 on T1 and on ≥ 2 held-out texts
without FA/min on good pairs exceeding ~2/min; otherwise ship the v2 detector on dataset v3
and say so.

**W4: Severity-gradient evidence.** Figures from results/labels: Matching Score and mean d vs
severity 1–5 per flaw type; null-edit false alarms; label edge-error distribution. Saved in
`docs/figures/` and used in the technical report, README and HF card.

**W5: Publish and demo.** Upload audio, labels and card to a public Hugging Face dataset (name
confirmed with the user first); link it in the README. Re-pick the demo with `cadence demo` and
confirm live detection.

**W6: Bookkeeping.** `project context.md`, commit; push only after the user agrees.

## Testing

- Unit tests for phrase segmentation (boundaries from consensus pauses), phrase features
  (rate/F0 range on a synthetic contour) and the v3 emphasis target rule.
- Existing `tests/` stay green; byte-identical rerun check passes for v3.

## Out of scope tonight

Dashboard explainability redesign, LLM rephrasing, WavLM rhythm, Azure baseline.
