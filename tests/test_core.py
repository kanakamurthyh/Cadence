import numpy as np
import pytest

from cadence import envelope as E
from cadence.detect import Params, detect, hysteresis, scores
from cadence.metrics import aggregate, iou, score_clip

W = 12


def feats(rate=4.0, pause=0.0, rng_=6.0, loud=0.0, seed=0):
    r = np.random.default_rng(seed)
    # Phrase features require syl/dur which this fixture omits; initialise to NaN
    # so that build()+with_phrases() yields NaN→NaN and the K=1 envelope test passes.
    f = {k: (np.full(W, np.nan) if k in E.PHRASE_FEATURES else np.zeros(W))
         for k in E.ENV_FEATURES + ["pitch"]}
    f["rate"] = rate + r.normal(0, 0.2, W)
    f["pause"] = np.full(W, pause)
    f["pitch_range"] = rng_ + r.normal(0, 0.5, W)
    f["loud"] = loud + r.normal(0, 0.5, W)
    f["prom_pitch"] = r.normal(-1, 0.3, W)
    f["prom_loud"] = r.normal(-1, 0.3, W)
    return f


WORDS = [{"word": f"w{i}", "start": i * 0.5, "end": i * 0.5 + 0.4} for i in range(W)]


def params():
    return Params(margin={f: 0.0 for f in E.ENV_FEATURES}, scale={f: 1.0 for f in E.ENV_FEATURES},
                  tau_high=0.5, tau_low=0.25)


def test_inside_envelope_is_zero():
    refs = [feats(seed=s) for s in range(4)]
    env = E.build(refs)
    dev = E.deviations(refs[0], env, params().margin, params().scale)
    assert all(np.allclose(v, 0) for v in dev.values())


def test_k1_reduces_to_single_reference():
    ref = feats(seed=1)
    env = E.build([ref])
    for f in E.ENV_FEATURES:
        assert np.allclose(env.lo[f], env.hi[f], equal_nan=True)
        assert np.allclose(env.lo[f], E.fwd(f, ref[f]), equal_nan=True)


def test_monotone_span_flagged_at_right_words():
    refs = [feats(seed=s) for s in range(4)]
    att = feats(seed=9)
    att["pitch_range"][4:8] = 0.5
    regs = detect(att, WORDS, E.build(refs), params())
    mono = [r for r in regs if r["type"] == "monotone"]
    assert len(mono) == 1 and mono[0]["w0"] == 4 and mono[0]["w1"] == 7


def test_style_inside_range_not_flagged():
    """A pause that one good reader also makes is style, not a flaw."""
    refs = [feats(seed=s) for s in range(4)]
    refs[2]["pause"][5] = 0.8
    att = feats(seed=7)
    att["pause"][5] = 0.7
    assert not [r for r in detect(att, WORDS, E.build(refs), params()) if "pause" in r["type"]]
    assert [r for r in detect(att, WORDS, E.build([refs[0]]), params()) if "pause" in r["type"]]


def test_hysteresis_and_merge():
    d = np.array([0, 0.3, 0.8, 0.3, 0.1, 0.9, 0, 0, 0, 1.0])
    assert hysteresis(d, 0.5, 0.25) == [(1, 5), (9, 9)]


def test_scores_bounded_and_monotone():
    p = params()
    a = scores([], WORDS, p)
    b = scores([{"type": "monotone", "start": 0, "end": 2, "d_mean": 1.0}], WORDS, p)
    assert a["pitch_variety"] == 10 and 0 <= b["pitch_variety"] < 10


def test_metrics():
    lab = [{"type": "pace", "start": 1.0, "end": 2.0}]
    assert iou(lab[0], {"start": 1.5, "end": 2.5}) == pytest.approx(1 / 3)
    row = score_clip(lab, [{"type": "pace", "start": 1.1, "end": 2.0}])
    assert row["match"] == 1 and row["onset_ms"][0] == pytest.approx(100)
    assert aggregate([row])["matching_score"] == 1.0
    assert score_clip(lab, [{"type": "monotone", "start": 1.0, "end": 2.0}])["match"] == 0


def test_injector_time_map():
    from cadence.inject import Clip
    c = Clip(np.zeros(16000 * 4, np.float32), WORDS)
    c.dur_spans.append((1.0, 2.0, 0.5))
    c.edits.append(("insert", 3.0, 0.7))
    assert c.tmap(0.5) == pytest.approx(0.5)
    assert c.tmap(2.0) == pytest.approx(1.5)
    assert c.tmap(3.5) == pytest.approx(3.5 - 0.5 + 0.7)


def _reader(tempo, seed, w=30):
    r = np.random.default_rng(seed)
    f = {k: np.zeros(w) for k in E.ENV_FEATURES + ["pitch"] if k not in E.REL_FEATURES}
    f["rate"] = tempo * (1 + r.normal(0, 0.03, w))
    f["pause"] = np.zeros(w)
    f["pitch_range"] = 6 + r.normal(0, 0.3, w)
    f["loud"] = r.normal(0, 0.3, w)
    f["prom_pitch"] = r.normal(-1, 0.2, w)
    f["prom_loud"] = r.normal(-1, 0.2, w)
    return f


def test_v2_relative_pace_catches_local_rush_v1_misses():
    """Good readers differ in overall tempo (3 to 5.4 syll/s); a slow reader rushing 6 words
    stays inside the absolute envelope but leaves the self-relative one."""
    refs = [_reader(t, s) for s, t in enumerate([3.0, 3.6, 4.2, 4.8, 5.4])]
    att = _reader(3.0, 99)
    att["rate"][10:16] *= 1.6  # local rush to 4.8 syll/s: inside the absolute range
    words = [{"word": f"w{i}", "start": i * 0.4, "end": i * 0.4 + 0.35} for i in range(30)]
    env = E.build(refs)
    base = dict(margin={f: 0.0 for f in E.ENV_FEATURES}, scale={f: 0.3 for f in E.ENV_FEATURES},
                tau={t: 1.0 for t in E.FLAW_TYPES})
    v1 = detect(att, words, env, Params(**base))
    v2 = detect(att, words, env, Params(**base, relative_channels=True, stress_floor=True))
    assert not [r for r in v1 if r["type"] == "pace"]
    hit = [r for r in v2 if r["type"] == "pace"]
    assert hit and hit[0]["w0"] >= 9 and hit[0]["w1"] <= 16


def test_stress_floor_ignores_imperceptible_peaks():
    refs = [_reader(4, s) for s in range(4)]
    for r in refs:
        r["prom_loud"][7] = 0.2  # every reader "peaks" by 0.2 dB: nobody hears that
    env = E.build(refs)
    assert env.stress(False)[1][7] and not env.stress(True)[1][7]


def test_emphasis_targets_perceptible_only():
    from cadence import inject
    W = 20
    words = [{"word": f"w{i}", "start": i * 0.4, "end": i * 0.4 + 0.35} for i in range(W)]
    f = {"pause": np.zeros(W), "prom_pitch": np.full(W, 2.0), "prom_loud": np.full(W, 2.0)}
    stress = np.zeros(W, bool)
    stress[6] = True  # one perceptible consensus point only
    spans = inject.choose_spans(words, f, stress, np.random.default_rng(0), stress_rule=2)
    assert spans["missed_emphasis"] == [(6, 6)]


def test_emphasis_rule_suppresses_fallback():
    from cadence import inject
    W = 20
    words = [{"word": f"w{i}", "start": i * 0.4, "end": i * 0.4 + 0.35} for i in range(W)]
    f = {"pause": np.zeros(W), "prom_pitch": np.full(W, 0.5), "prom_loud": np.full(W, 0.5)}
    stress = np.zeros(W, bool)
    stress[6] = True
    stress[10] = True
    s1 = inject.choose_spans(words, f, stress, np.random.default_rng(0), stress_rule=1)
    s2 = inject.choose_spans(words, f, stress, np.random.default_rng(0), stress_rule=2)
    assert len(s1["missed_emphasis"]) > 0
    assert s2["missed_emphasis"] == []


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


def _phrase_ref(seed, W=20, pause_idxs=(3, 7), pause_val=0.3):
    """Minimal ref dict with syl/dur/pitch and configurable pause boundaries."""
    r = np.random.default_rng(seed)
    syl = np.ones(W)
    dur = np.full(W, 0.25)
    pause = np.zeros(W)
    for idx in pause_idxs:
        pause[idx] = pause_val
    pitch = r.normal(0, 1, W)
    rate = syl / dur
    pitch_range = np.full(W, 6.0) + r.normal(0, 0.1, W)
    loud = r.normal(0, 0.3, W)
    prom_pitch = r.normal(-1, 0.2, W)
    prom_loud = r.normal(-1, 0.2, W)
    return {"syl": syl, "dur": dur, "pause": pause, "pitch": pitch,
            "rate": rate, "pitch_range": pitch_range, "loud": loud,
            "prom_pitch": prom_pitch, "prom_loud": prom_loud}


def test_deviations_phrase_gating():
    """phrase=False: phrase channels all zero; phrase=True: rel channels zero, longest phrase flagged.

    Uses 3 phrases of 4+4+12 words so the LONGEST phrase (12 words, words 8-19) is sped up.
    The phrase-median normalisation must be over phrases (not words) for rate_phr on phrase 2
    to exceed 1.0; word-weighted median would be dominated by phrase 2 and yield rate_phr = 1.0.
    """
    W = 20  # phrases: words 0-3 (4), 4-7 (4), 8-19 (12)
    refs = [_phrase_ref(s, W) for s in range(4)]
    env = E.build(refs)

    # (a) build stores phrase_id with 3 phrases (boundaries after words 3 and 7)
    assert env.phrase_id is not None and len(env.phrase_id) == W
    assert list(env.phrase_id[:4]) == [0, 0, 0, 0]
    assert list(env.phrase_id[4:8]) == [1, 1, 1, 1]
    assert all(env.phrase_id[8:] == 2)

    # attempt: phrase 2 (12 words, 8-19) compressed to dur=0.1 s/word.
    # phrase rates: phrase0=4.0, phrase1=4.0, phrase2=10.0
    # phrase median = 4.0 (mid of [4,4,10]) → rate_phr phrase2 = 2.5 > 1.0 ✓
    # (word-weighted median of [4]*8+[10]*12 would be 10.0 → rate_phr=1.0 — the old bug)
    att = _phrase_ref(99, W)
    att["dur"] = np.full(W, 0.25)
    att["dur"][8:] = 0.1

    p = params()

    # (b) phrase=False: phrase channels are all zero
    dev_off = E.deviations(att, env, p.margin, p.scale, relative=True, phrase=False)
    for key in [("rate_phr", +1), ("rate_phr", -1), ("pitch_spread_phr", -1)]:
        assert np.all(dev_off[key] == 0), f"phrase=False: expected zeros for {key}"

    # (c) phrase=True: rel channels zeroed; rate_phr+ > 0 on the 12-word sped-up phrase
    dev_on = E.deviations(att, env, p.margin, p.scale, relative=True, phrase=True)
    for key in [("rate_rel", +1), ("rate_rel", -1), ("pitch_range_rel", -1)]:
        assert np.all(dev_on[key] == 0), f"phrase=True: expected zeros for rel channel {key}"
    assert dev_on[("rate_phr", +1)][8:].max() > 0, "phrase=True: longest phrase sped up should flag rate_phr+"


def test_with_phrases_normalizes_by_phrase_median():
    """Normalization uses median over phrases (one value each), not over words.

    Two phrases of lengths 2 and 8 with rates 2.0 and 4.0 syl/s.
    Phrase-median = median([2.0, 4.0]) = 3.0 → rate_phr = 2/3 and 4/3.
    Word-weighted median would be 4.0 → rate_phr = 0.5 and 1.0 (the old bug).
    """
    pid = np.array([0, 0, 1, 1, 1, 1, 1, 1, 1, 1])  # phrase 0: 2 words, phrase 1: 8 words
    syl = np.ones(10)
    dur = np.concatenate([np.full(2, 0.5), np.full(8, 0.25)])  # rate0=2.0, rate1=4.0
    pitch = np.zeros(10)  # all-zero: spread = 0.0 (non-NaN, ≥2 voices per phrase)
    f = {"syl": syl, "dur": dur, "pitch": pitch,
         "rate": np.full(10, 4.0), "pitch_range": np.full(10, 6.0)}
    out = E.with_phrases(f, pid)
    assert np.allclose(out["rate_phr"][:2], 2.0 / 3.0), "phrase 0: rate_phr should be 2/3"
    assert np.allclose(out["rate_phr"][2:], 4.0 / 3.0), "phrase 1: rate_phr should be 4/3"


def test_margin_diffs_no_keyerror():
    """_margin_diffs must not raise KeyError even for records without syl/dur/phrase keys."""
    from cadence.evaluate import _margin_diffs
    W = 8
    pid = np.zeros(W, int)

    # records lacking syl/dur (pre-Task-2 format): phrase features will be NaN → diffs empty
    base = {k: np.ones(W) for k in E.ENV_FEATURES if k not in E.PHRASE_FEATURES}
    base["pitch"] = np.zeros(W)
    diffs_no_syl = _margin_diffs(base, base, pid)
    assert "rate_phr" in diffs_no_syl  # key must exist (may be empty list)

    # records WITH syl/dur: phrase features are finite → diffs non-empty
    full = dict(base)
    full["syl"] = np.ones(W)
    full["dur"] = np.full(W, 0.3)
    diffs_with_syl = _margin_diffs(full, full, pid)
    assert "rate_phr" in diffs_with_syl
