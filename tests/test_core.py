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
    # pinned: phrase 10-19 is trimmed to the rushed words 12-16
    assert hit[0]["feature"] == "rate_phr" and (hit[0]["w0"], hit[0]["w1"]) == (12, 16)
    from cadence.detect import explain
    assert "phrase speaking rate relative to your own pace" in explain(hit[0], att, words, env)


def test_explain_phrase_region():
    from cadence.detect import explain
    refs = [_phr_reader(t, s) for s, t in enumerate([3.0, 3.6, 4.2, 4.8])]
    env = E.build(refs)
    att = E.with_phrases(_phr_reader(3.0, 7), env.phrase_id)
    words = [{"word": f"w{i}", "start": i * 0.4, "end": i * 0.4 + 0.35} for i in range(30)]
    r = {"type": "pace", "feature": "rate_phr", "side": 1, "w0": 12, "w1": 16, "start": 4.8, "end": 6.75}
    assert "x your own typical value" in explain(r, att, words, env)


def test_v3_phrase_channels_off_never_yields_phrase_regions():
    """Default Params (phrase_channels=False): v1/v2 output never names a phrase feature."""
    refs = [_phr_reader(t, s) for s, t in enumerate([3.0, 3.6, 4.2, 4.8, 5.4])]
    att = _phr_reader(3.0, 99)
    att["dur"][10:20] /= 1.8; att["rate"][10:20] *= 1.8
    att["pitch"][10:20] = 0.0
    words = [{"word": f"w{i}", "start": i * 0.4, "end": i * 0.4 + 0.35} for i in range(30)]
    env = E.build(refs)
    base = dict(margin={f: 0.0 for f in E.ENV_FEATURES}, scale={f: 0.3 for f in E.ENV_FEATURES},
                tau={t: 1.0 for t in E.FLAW_TYPES})
    for extra in ({}, {"relative_channels": True, "stress_floor": True}):
        assert Params(**base, **extra).phrase_channels is False
        for r in detect(att, words, env, Params(**base, **extra)):
            assert r["feature"] not in E.PHRASE_FEATURES


def test_v3_pitch_spread_phrase_flags_flattened_phrase_as_monotone():
    """Refs move pitch in every phrase; the attempt flattens phrase 2 (words 10-19)."""
    from cadence.detect import explain

    def reader(tempo, seed):
        f = _phr_reader(tempo, seed)
        f["pitch"] = np.random.default_rng(100 + seed).normal(0, 2.0, 30)
        return f

    refs = [reader(t, s) for s, t in enumerate([3.0, 3.6, 4.2, 4.8, 5.4])]
    att = reader(3.0, 99)
    att["pitch"][10:20] = 0.05 * np.random.default_rng(5).normal(0, 1, 10)  # nearly constant
    words = [{"word": f"w{i}", "start": i * 0.4, "end": i * 0.4 + 0.35} for i in range(30)]
    env = E.build(refs)
    margin, scale = {f: 0.0 for f in E.ENV_FEATURES}, {f: 0.3 for f in E.ENV_FEATURES}
    dev = E.deviations(att, env, margin, scale, relative=True, stress_floor=True, phrase=True)
    assert dev[("pitch_spread_phr", -1)][10:20].min() > 0
    p = Params(margin=margin, scale=scale, tau={t: 1.0 for t in E.FLAW_TYPES},
               relative_channels=True, stress_floor=True, phrase_channels=True)
    hit = [r for r in detect(att, words, env, p) if r["feature"] == "pitch_spread_phr"]
    assert hit and hit[0]["type"] == "monotone"
    # pinned: phrase 10-19 trimmed to words whose own pitch_range_rel is below the envelope
    assert (hit[0]["w0"], hit[0]["w1"]) == (12, 19)
    assert "phrase pitch movement relative to your own" in explain(hit[0], att, words, env)


def _v3_params():
    return Params(margin={f: 0.0 for f in E.ENV_FEATURES}, scale={f: 0.3 for f in E.ENV_FEATURES},
                  tau={t: 1.0 for t in E.FLAW_TYPES}, relative_channels=True, stress_floor=True,
                  phrase_channels=True)


def test_v3_phrase_trim_falls_back_to_full_phrase():
    """Phrase 10-19 is spoken faster (shorter durations) but every word's own rate_rel stays
    inside the refs' word-level envelope: no word to trim to, so the whole phrase is kept."""
    refs = [_phr_reader(t, s) for s, t in enumerate([3.0, 3.6, 4.2, 4.8, 5.4])]
    env = E.build(refs)
    att = _phr_reader(3.0, 0)  # same word rates as refs[0]
    att["dur"][10:20] /= 1.8
    words = [{"word": f"w{i}", "start": i * 0.4, "end": i * 0.4 + 0.35} for i in range(30)]
    p = _v3_params()
    wd = E.deviations(att, env, p.margin, p.scale, relative=True, stress_floor=True)
    assert not wd[("rate_rel", 1)][10:20].any()
    hit = [r for r in detect(att, words, env, p) if r["type"] == "pace"]
    assert hit and hit[0]["feature"] == "rate_phr" and (hit[0]["w0"], hit[0]["w1"]) == (10, 19)


def test_v3_phrase_trim_keeps_words_won_by_other_channels():
    """Only phrase-channel words are filtered by word-level rate_rel. Word 11 is won by the
    absolute slow-rate channel (rate_rel+ is 0 there) and must stay; words 14-16 are the
    rushed ones. Filtering every word would give (14, 16)."""
    refs = [_phr_reader(t, s) for s, t in enumerate([3.0, 3.6, 4.2, 4.8, 5.4])]
    env = E.build(refs)
    att = _phr_reader(3.0, 0)
    att["dur"][10:20] /= 1.8
    att["rate"][14:17] *= 1.8
    att["rate"][11] = 1.0
    words = [{"word": f"w{i}", "start": i * 0.4, "end": i * 0.4 + 0.35} for i in range(30)]
    p = _v3_params()
    d, ch = E.by_type(E.deviations(att, env, p.margin, p.scale, relative=True, stress_floor=True,
                                   phrase=True))["pace"]
    assert E.CHANNELS[ch[11]][:2] == ("rate", -1)
    hit = [r for r in detect(att, words, env, p) if r["type"] == "pace"]
    assert hit and hit[0]["feature"] == "rate_phr" and (hit[0]["w0"], hit[0]["w1"]) == (11, 16)


def test_t7_t8_registered():
    """T7 and T8 are in test_texts(); T7 has 12 sources each with a 40-char sha1;
    T7's text starts with 'Please call Stella'; T8 has librivox_ids containing 17632."""
    from cadence.data.texts import TEXTS, test_texts
    tids = test_texts()
    assert "T7" in tids, "T7 must be in test_texts()"
    assert "T8" in tids, "T8 must be in test_texts()"
    t7 = TEXTS["T7"]
    assert len(t7["sources"]) == 12, f"T7 must have 12 sources, got {len(t7['sources'])}"
    assert all(len(s["sha1"]) == 40 for s in t7["sources"]), "Every T7 source must have a 40-char sha1"
    assert t7["text"].startswith("Please call Stella"), "T7 text must start with 'Please call Stella'"
    t8 = TEXTS["T8"]
    assert 17632 in t8["librivox_ids"], "T8 must reference LibriVox book 17632"


# -- ship_decision tests ------------------------------------------------------

def _run(ms: float, fa: float) -> dict:
    """Minimal E.run()-shaped result for ship_decision tests."""
    return {"ladders": {"matching_score": ms}, "fa_per_min_good_pairs": fa}


def test_ship_decision_v3_wins_t1_and_two_held_out():
    """v3 beats v2 on T1 and on 2 held-out texts, no FA violation → ship v3."""
    from cadence.benchmark import ship_decision
    v3 = {"T1": _run(0.60, 0.5), "T2": _run(0.55, 0.8), "T3": _run(0.50, 1.0)}
    v2 = {"T1": _run(0.50, 0.4), "T2": _run(0.45, 0.9), "T3": _run(0.40, 1.1)}
    d = ship_decision(v3, v2)
    assert d["ship"] == "v3"
    assert d["t1"]["v3_wins"] is True
    assert set(d["wins"]) == {"T2", "T3"}
    assert d["losses"] == []
    assert d["fa_violations"] == []
    assert "v3 beats v2" in d["reason"]


def test_ship_decision_v3_wins_t1_but_only_one_held_out():
    """v3 beats v2 on T1 and on 1 held-out text only → ship v2 (need >= 2)."""
    from cadence.benchmark import ship_decision
    v3 = {"T1": _run(0.60, 0.5), "T2": _run(0.55, 0.8), "T3": _run(0.38, 1.0)}
    v2 = {"T1": _run(0.50, 0.4), "T2": _run(0.45, 0.9), "T3": _run(0.42, 1.1)}
    d = ship_decision(v3, v2)
    assert d["ship"] == "v2"
    assert d["t1"]["v3_wins"] is True
    assert d["wins"] == ["T2"]
    assert d["losses"] == ["T3"]
    assert "only 1" in d["reason"]


def test_ship_decision_fa_cap_exceeded():
    """v3 beats v2 on T1 and 2 held-out texts, but exceeds FA cap on one text where v2 is ok → ship v2."""
    from cadence.benchmark import ship_decision
    v3 = {"T1": _run(0.60, 0.5), "T2": _run(0.55, 2.5), "T3": _run(0.50, 0.8)}
    v2 = {"T1": _run(0.50, 0.4), "T2": _run(0.45, 1.5), "T3": _run(0.40, 0.9)}
    # T2: v2 FA=1.5 <= 2.0, v3 FA=2.5 > 2.0 → FA violation
    d = ship_decision(v3, v2)
    assert d["ship"] == "v2"
    assert d["fa_violations"] == ["T2"]
    assert "FA cap" in d["reason"]


def test_ship_decision_v3_loses_t1_wins_all_held_out():
    """v3 loses T1 even though it wins all held-out texts → ship v2."""
    from cadence.benchmark import ship_decision
    v3 = {"T1": _run(0.45, 0.5), "T2": _run(0.55, 0.8), "T3": _run(0.50, 1.0)}
    v2 = {"T1": _run(0.50, 0.4), "T2": _run(0.45, 0.9), "T3": _run(0.40, 1.1)}
    d = ship_decision(v3, v2)
    assert d["ship"] == "v2"
    assert d["t1"]["v3_wins"] is False
    assert set(d["wins"]) == {"T2", "T3"}
    assert "does not beat" in d["reason"]


def test_ship_decision_none_nan_handling():
    """Non-finite v3 MS counts as a loss; non-finite v3 FA (where v2 is ok) counts as a violation."""
    import math
    from cadence.benchmark import ship_decision
    # T2: v3 MS = NaN (loss), v3 FA = NaN (FA violation since v2 FA = 0.9 <= 2.0)
    # T3: normal v3 win
    v3 = {"T1": _run(0.60, 0.5), "T2": _run(float("nan"), float("nan")), "T3": _run(0.50, 1.0)}
    v2 = {"T1": _run(0.50, 0.4), "T2": _run(0.45, 0.9), "T3": _run(0.40, 1.1)}
    d = ship_decision(v3, v2)
    assert d["ship"] == "v2"
    assert "T2" in d["losses"]
    assert "T2" in d["fa_violations"]
    # T3 is a win (v3 0.50 > v2 0.40) but only 1 win total (T2 is a loss)
    assert d["wins"] == ["T3"]


# -- report_configs tests -----------------------------------------------------

def test_report_configs_ship_v3():
    """When ship=v3 (phrase=True): B1 and all ablations share phrase=True; v1 has phrase=False; other=v2."""
    import dataclasses
    from cadence import evaluate as E
    from cadence.benchmark import report_configs
    ship = E.Config(phrase=True)
    other = E.Config()
    methods, ablations = report_configs(ship, other)
    # B2 is SHIP
    assert methods["B2 envelope (K=all), ours"] == ship
    # B1 carries phrase=True (same as SHIP)
    b1 = methods["B1 single reference (K=1)"]
    assert b1.phrase is True and b1.k == 1
    # No K=all in ablations
    assert "K=all" not in ablations
    # v1 row has phrase disabled
    v1 = ablations["v1 detector (frozen design)"]
    assert v1.phrase is False and v1.relative is False and v1.stress_floor is False
    # Other candidate row present and equals OTHER
    assert "other candidate: v2 detector (no phrase channels)" in ablations
    assert ablations["other candidate: v2 detector (no phrase channels)"] == other
    # All ablation rows derived from ship carry phrase=True (except v1 and other)
    for name, cfg in ablations.items():
        if name not in ("v1 detector (frozen design)", "other candidate: v2 detector (no phrase channels)"):
            assert cfg.phrase is True, f"{name}: expected phrase=True"


def test_report_configs_ship_v2():
    """When ship=v2 (phrase=False): B1 has phrase=False; v1 row has phrase=False; other=v3."""
    import dataclasses
    from cadence import evaluate as E
    from cadence.benchmark import report_configs
    ship = E.Config()  # v2
    other = E.Config(phrase=True)  # v3
    methods, ablations = report_configs(ship, other)
    assert methods["B2 envelope (K=all), ours"] == ship
    b1 = methods["B1 single reference (K=1)"]
    assert b1.phrase is False and b1.k == 1
    assert "K=all" not in ablations
    assert "other candidate: v3 detector (phrase channels)" in ablations
    assert ablations["other candidate: v3 detector (phrase channels)"] == other
    # v1 row has phrase=False (already False for v2 ship, but explicit replace keeps it off)
    v1 = ablations["v1 detector (frozen design)"]
    assert v1.phrase is False and v1.relative is False and v1.stress_floor is False
