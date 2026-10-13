# Track C Scoring Push Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dataset v3 (emphasis rule, Indian texts), detector v3 (phrase-level pace/monotone), severity-gradient evidence, public HF dataset and a demo that is caught live, before 15 Oct 00:15 IST.

**Architecture:** Phrase channels are per-word arrays that hold one value per consensus phrase, so the existing envelope machinery (min/max per word, margin, scale, hysteresis) is reused unchanged. Phrase boundaries come from the good readers' pauses and are stored on the `Envelope`. A phrase flag is trimmed to the words whose word-level self-relative deviation is positive, so temporal grounding stays word-precise.

**Tech Stack:** Python 3.12 (uv), numpy, parselmouth, torchaudio, Gradio, pytest, huggingface_hub, matplotlib.

**Spec:** `docs/superpowers/specs/2026-10-14-track-c-scoring-push-design.md`

## Global Constraints

- Thresholds fitted on T1 only; never retune on T2/T3 (or any other held-out text).
- Long jobs (refs, ladders, evaluate, robustness) run with `nohup` and at most 3 workers (`--workers 3`).
- After every change update `project context.md` (dated change-log entry, status, results, pending, "Last updated").
- v1 and v2 stay reproducible: every new behaviour is behind a `Params`/`Config` flag defaulting to the old behaviour.
- Licence of any new audio must allow derivatives (PD, CC0, CC-BY, CC-BY-SA; NC only if stated in DATA_LICENSING).
- Push to GitHub and create the public HF repo only after the user confirms.

## Review Focus

1. A text whose good readers never pause together (one giant phrase): phrase channels must still produce finite values and must not flag the whole text; test `test_phrase_ids_no_consensus_pause`.
2. Records saved before this change (no `syl`/`dur` in feats): loading must add them from `words`; test `test_word_basics_backfilled`.
3. Phrases with < 2 voiced words (NaN pitch spread): no flag and no crash; test `test_phrase_feats_nan_safe`.
4. Explanations for a phrase-channel region must quote phrase values in "x your own typical value" units; test `test_explain_phrase_region`.
5. Emphasis targets when a text has fewer than `n` perceptible stress points: fewer clips, never a fallback to imperceptible points; test `test_emphasis_targets_perceptible_only`.

---

### Task 1: Dataset v3 emphasis rule

**Files:**
- Modify: `cadence/inject.py` (`choose_spans`)
- Modify: `scripts/build_ladders.py:40` (pass perceptible stress)
- Modify: `cadence/data/texts.py` (no change unless span_rule needed), `data/DATA_CARD.md` (version history)
- Test: `tests/test_core.py`

**Interfaces:**
- Produces: `choose_spans(..., stress_rule: int = 1)`; `stress_rule=2` means `stress` is the perceptible mask and the "allow any consensus stress point" fallback is disabled.

- [ ] **Step 1: Failing test**

```python
def test_emphasis_targets_perceptible_only():
    from cadence import inject
    W = 20
    words = [{"word": f"w{i}", "start": i * 0.4, "end": i * 0.4 + 0.35} for i in range(W)]
    f = {"pause": np.zeros(W), "prom_pitch": np.full(W, 2.0), "prom_loud": np.full(W, 2.0)}
    stress = np.zeros(W, bool)
    stress[6] = True  # one perceptible consensus point only
    spans = inject.choose_spans(words, f, stress, np.random.default_rng(0), stress_rule=2)
    assert spans["missed_emphasis"] == [(6, 6)]
```

- [ ] **Step 2:** `uv run pytest tests/test_core.py::test_emphasis_targets_perceptible_only -v` → FAIL (unexpected keyword `stress_rule`).
- [ ] **Step 3: Implement.** Add `stress_rule: int = 1` to `choose_spans`; wrap the fallback:

```python
    if stress_rule < 2 and len(pick(list(stress_c), n)) < n:  # v1/v2: allow any consensus stress point
        stress_c += [(i, i) for i in inner if stress[i] and not own[i]]
```

In `scripts/build_ladders.py` add CLI flag `--dataset {2,3}` (default 3). For 3 pass `env.stress_pitch_p | env.stress_loud_p` and `stress_rule=2`; for 2 keep the current call. Record `"dataset_version"` in each `manifest.json` entry's text-level metadata.
- [ ] **Step 4:** test passes; full `uv run pytest -q` green.
- [ ] **Step 5:** DATA_CARD "Version history": v2 (targets: any consensus prominence), v3 (targets: ≥ ¾ of good readers peak by ≥ 1.5 st or ≥ 1 dB). Commit `Dataset v3: emphasis targets at perceptible consensus stress points`.

### Task 2: Phrase segmentation and phrase features

**Files:**
- Modify: `cadence/features.py` (`word_basics`, `UNITS`, `word_features` emits `syl`, `dur`)
- Modify: `cadence/envelope.py` (`phrase_ids`, `with_phrases`, `Envelope.phrase_id`, `build`, `deviations`)
- Modify: `cadence/evaluate.py::_record`, `cadence/pipeline.py::load_record` (backfill `syl`/`dur`)
- Test: `tests/test_core.py`

**Interfaces:**
- Produces: `features.word_basics(words) -> dict[str, np.ndarray]` with `syl`, `dur`.
- Produces: `envelope.phrase_ids(pauses: np.ndarray (K, W)) -> np.ndarray[int] (W,)`; boundary after word i when ≥ `STRESS_FRACTION` of readers have `pause[i] >= 0.05`.
- Produces: `envelope.with_phrases(feats, pid) -> dict` adding `rate_phr` (phrase articulation rate / reader's median phrase rate) and `pitch_spread_phr` ((p90 − p10 of word `pitch` in the phrase + 1) / (median over phrases + 1)), broadcast to each word.
- Produces: `Envelope.phrase_id: np.ndarray | None`.

- [ ] **Step 1: Failing tests**

```python
def test_phrase_ids_consensus():
    p = np.zeros((4, 8)); p[:, 2] = 0.3; p[:3, 5] = 0.3  # all pause after w2, 3 of 4 after w5
    assert list(E.phrase_ids(p)) == [0, 0, 0, 1, 1, 1, 2, 2]

def test_phrase_ids_no_consensus_pause():
    p = np.zeros((4, 8)); p[0, 3] = 0.5
    assert set(E.phrase_ids(p)) == {0}

def test_word_basics_backfilled():
    from cadence.features import word_basics
    b = word_basics([{"word": "water", "start": 0.0, "end": 0.5}])
    assert b["syl"][0] == 2 and abs(b["dur"][0] - 0.5) < 1e-9

def test_phrase_feats_nan_safe():
    f = {"syl": np.ones(6), "dur": np.full(6, 0.25), "pitch": np.array([np.nan] * 3 + [0, 2, 4.0])}
    out = E.with_phrases(f, np.array([0, 0, 0, 1, 1, 1]))
    assert np.isnan(out["pitch_spread_phr"][:3]).all() and np.isfinite(out["rate_phr"]).all()
```

- [ ] **Step 2:** run → FAIL (missing names).
- [ ] **Step 3: Implement.**

```python
# features.py
UNITS.update({"rate_phr": "x", "pitch_spread_phr": "x"})

def word_basics(words: list[dict]) -> dict[str, np.ndarray]:
    return {"syl": np.array([syllables(w["word"]) for w in words], float),
            "dur": np.array([max(w["end"] - w["start"], 0.02) for w in words], float)}
```

`word_features` adds `**word_basics(words)` to `feats`; `_record` and `load_record` do `feats = {**word_basics(words), **feats}` before `add_derived`.

```python
# envelope.py
PHRASE_FEATURES = {"rate_phr", "pitch_spread_phr"}
CHANNELS += [("rate_phr", +1, "pace"), ("rate_phr", -1, "pace"), ("pitch_spread_phr", -1, "monotone")]
TRANSFORM.update({"rate_phr": TRANSFORM["rate_rel"], "pitch_spread_phr": TRANSFORM["pitch_range_rel"]})

def phrase_ids(pauses: np.ndarray) -> np.ndarray:
    br = (np.nan_to_num(pauses) >= 0.05).mean(0) >= STRESS_FRACTION
    br[-1] = False
    return np.concatenate([[0], np.cumsum(br[:-1])]).astype(int)

def with_phrases(feats: dict, pid: np.ndarray) -> dict:
    out = dict(feats)
    W = len(pid)
    rate, spread = np.full(W, np.nan), np.full(W, np.nan)
    if "syl" in feats and "dur" in feats:
        for p in np.unique(pid):
            m = pid == p
            rate[m] = feats["syl"][m].sum() / feats["dur"][m].sum()
            v = feats["pitch"][m]
            v = v[np.isfinite(v)]
            if len(v) >= 2:
                spread[m] = np.percentile(v, 90) - np.percentile(v, 10)
    with np.errstate(all="ignore"):
        out["rate_phr"] = rate / np.nanmedian(rate) if np.isfinite(rate).any() else rate
        out["pitch_spread_phr"] = ((spread + 1) / (np.nanmedian(spread) + 1)
                                   if np.isfinite(spread).any() else spread)
    return out
```

`Envelope` gets `phrase_id: np.ndarray | None = None` (last field). `build` computes `pid = phrase_ids(np.stack([r["pause"] for r in ref_feats]))`, applies `with_phrases(r, pid)` to every ref before stacking, and stores `pid`. `deviations(..., phrase: bool = False)`: `x = with_phrases(add_derived(x), env.phrase_id)`; channels in `PHRASE_FEATURES` are zeroed unless `phrase`; when `phrase` is True the word-level `REL_FEATURES` channels are zeroed (phrase replaces them).
- [ ] **Step 4:** tests pass; full suite green (existing `feats()` fixture lacks `syl`/`dur` → phrase values NaN → d = 0, unchanged behaviour).
- [ ] **Step 5:** commit `Phrase segmentation and phrase-level rate / pitch-spread features`.

### Task 3: Detector v3 (phrase channels, trimmed regions, explanations)

**Files:**
- Modify: `cadence/detect.py` (`Params.phrase_channels`, `detect`, `explain`)
- Modify: `cadence/evaluate.py` (`Config.phrase`, name, `calibrate`, `fit_margin_scale`)
- Modify: `cadence/cli.py` evaluate flag `--detector {v2,v3}` if evaluate exposes variants
- Test: `tests/test_core.py`

**Interfaces:**
- Consumes: `E.with_phrases`, `Envelope.phrase_id`, `deviations(..., phrase=)`.
- Produces: `Params.phrase_channels: bool = False`; `Config.phrase: bool = False`.

- [ ] **Step 1: Failing tests**

```python
def _phr_reader(tempo, seed, W=30):
    f = _reader(tempo, seed)
    f["syl"], f["dur"] = np.ones(W), np.full(W, 1 / tempo)
    f["pause"] = np.zeros(W); f["pause"][[9, 19]] = 0.4
    return f

def test_v3_phrase_pace_flags_rushed_phrase_trimmed():
    refs = [_phr_reader(t, s) for s, t in enumerate([3.0, 3.6, 4.2, 4.8, 5.4])]
    att = _phr_reader(3.0, 99)
    att["dur"][12:17] /= 1.8; att["rate"][12:17] *= 1.8
    words = [{"word": f"w{i}", "start": i * 0.4, "end": i * 0.4 + 0.35} for i in range(30)]
    env = E.build(refs)
    p = Params(margin={f: 0.0 for f in E.ENV_FEATURES}, scale={f: 0.3 for f in E.ENV_FEATURES},
               tau={t: 1.0 for t in E.FLAW_TYPES}, relative_channels=True, stress_floor=True,
               phrase_channels=True)
    hit = [r for r in detect(att, words, env, p) if r["type"] == "pace"]
    assert hit and 10 <= hit[0]["w0"] <= 13 and 15 <= hit[0]["w1"] <= 19

def test_explain_phrase_region():
    from cadence.detect import explain
    refs = [_phr_reader(t, s) for s, t in enumerate([3.0, 3.6, 4.2, 4.8])]
    env = E.build(refs)
    att = E.with_phrases(_phr_reader(3.0, 7), env.phrase_id)
    words = [{"word": f"w{i}", "start": i * 0.4, "end": i * 0.4 + 0.35} for i in range(30)]
    r = {"type": "pace", "feature": "rate_phr", "side": 1, "w0": 12, "w1": 16, "start": 4.8, "end": 6.75}
    assert "x your own typical value" in explain(r, att, words, env)
```

- [ ] **Step 2:** run → FAIL.
- [ ] **Step 3: Implement.**
  - `Params.phrase_channels: bool = False` (after `stress_floor`).
  - `detect`: `dev = deviations(..., phrase=p.phrase_channels)`. After computing `idx` for a region whose dominant channel feature is in `PHRASE_FEATURES`, trim to words with positive word-level self-relative deviation, computed once per call via `deviations(..., phrase=False)` with `relative=True` for the matching `REL` feature (`rate_rel` for `rate_phr`, `pitch_range_rel` for `pitch_spread_phr`), same side; if none are positive keep the phrase.
  - `explain`: start with `x = E.with_phrases(E.add_derived(x), env.phrase_id) if env.phrase_id is not None else x`; `what` for `rate_phr` = "phrase speaking rate relative to your own pace", for `pitch_spread_phr` = "phrase pitch movement relative to your own".
  - `evaluate.Config.phrase: bool = False`; `name` appends ", phrase channels"; `calibrate` passes `phrase_channels=cfg.phrase`; `fit_margin_scale` builds the all-good envelope first and applies `with_phrases(·, env.phrase_id)` to `fr`/`fn` before diffing.
  - Main config for the v3 run: `Config(phrase=True)`; params saved to `data/params.json` only if the ship rule passes (Task 5).
- [ ] **Step 4:** tests pass; full suite green.
- [ ] **Step 5:** commit `Detector v3: phrase-level pace and monotone channels`.

### Task 4: Indian-speaker texts (after research report)

**Files:**
- Modify: `cadence/data/texts.py` (new `T7`/`T8` entries, `role: "test-indian"`), `cadence/data/librivox.py` or new `cadence/data/fetch_other.py` (non-LibriVox sources)
- Modify: `docs/DATA_LICENSING.md`, `data/DATA_CARD.md`, `data/inventory.*` (via `cadence inventory`)

- [ ] **Step 1:** Pick 1–2 texts from `reports/Indian speech dataset sources.md` with ≥ 4 renditions under a derivative-allowing licence; record URL, licence quote, speaker L1/accent per file.
- [ ] **Step 2:** Add the entries in the same shape as `T6` (text, source ids/URLs, `span_rule: 2`, role). Write fetch code that stores per-file licence like the LibriVox path.
- [ ] **Step 3:** `nohup uv run cadence fetch` → `build_refs.py --workers 3` → `build_ladders.py --workers 3 --dataset 3`; check alignment confidence in `selection.json`; drop renditions that fail `locate_text`.
- [ ] **Step 4:** `uv run cadence labels` validation passes for the new texts; commit `Add Indian-speaker held-out text(s)`.

### Task 5: Evaluate v3 and apply the ship rule

- [ ] **Step 1:** `cp -r results/{results.json,results.md,robustness*.json,rerun_hashes.json} results/frozen_v2_2026-10-14/` plus `data/params.json`, `data/labels/` snapshot.
- [ ] **Step 2:** `nohup uv run cadence evaluate > logs/evaluate_v3.log 2>&1 &` (v3 config on dataset v3; also v2 config on dataset v3 for the comparison row).
- [ ] **Step 3:** Ship rule: v3 beats v2 (both on dataset v3) on T1 and on ≥ 2 held-out texts, with FA/min on good pairs ≤ ~2. Otherwise keep v2 params. Write the decision with numbers into `results/results.md`.
- [ ] **Step 4:** `nohup uv run python scripts/robustness.py --workers 3`; `uv run python scripts/rerun_check.py --store`; `uv run cadence demo` and confirm the chosen demo is detected by the shipped detector.
- [ ] **Step 5:** commit `Evaluate dataset v3 / detector v3`.

### Task 6: Severity-gradient evidence

**Files:**
- Create: `scripts/gradient_figures.py`; outputs `docs/figures/*.png`, `results/gradient.json`
- Modify: `docs/technical_report.md`, `README.md`

- [ ] **Step 1:** Script reads `results/results.json` and `data/labels/labels.jsonl` + `validation.json`; writes (a) Matching Score vs severity 1–5 per flaw type (B2 shipped, B1, B0), (b) mean d at the labelled words vs severity, (c) null-edit FA/min per text, (d) label onset/offset error histogram. Matplotlib, fixed style, deterministic output.
- [ ] **Step 2:** Embed figures in the report (≤ 6 pages total) and README "Evidence" section. Commit.

### Task 7: Publish dataset on Hugging Face

- [ ] **Step 1:** Ask the user for the repo id (e.g. `<user>/cadence-contrastive-speech`) and confirm public.
- [ ] **Step 2:** Stage `data/refs`, `data/ladders`, `data/labels`, `data/DATA_CARD.md` (as `README.md` with HF YAML: licence `cc0-1.0` for LibriVox-derived audio plus per-file licence column) into a scratch dir; `huggingface-cli upload <repo> <dir> --repo-type dataset`.
- [ ] **Step 3:** Add the link to `README.md` and `DATA_CARD.md`; commit.

### Task 8: Bookkeeping

- [ ] Update `project context.md` after each task (change log, status, results, pending, Last updated). Ask before `git push`.
