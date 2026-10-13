import numpy as np
import pytest

from cadence import envelope as E
from cadence.detect import Params, detect, hysteresis, scores
from cadence.metrics import aggregate, iou, score_clip

W = 12


def feats(rate=4.0, pause=0.0, rng_=6.0, loud=0.0, seed=0):
    r = np.random.default_rng(seed)
    f = {k: np.zeros(W) for k in E.ENV_FEATURES + ["pitch"]}
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
