"""Cache the demo files locally (spec section 9: no network needed on stage).

data/demo/T2_rushed_and_dropped_pause.wav: a reader outside the good set, with a
    rushed final stanza and a dropped pause injected (stand-in until a teammate
    records the live take).
data/demo/T3_monotone.wav: a T3 reader outside the good set, monotone mid-speech.
data/demo/style_pair.json: two good T2 readers who pause in different places;
    lists what the single-reference baseline and the envelope flag on each.
"""
import json

from cadence import audio, inject
from cadence.detect import detect
from cadence.evaluate import envelope_for, record, selection
from cadence.pipeline import REFS, ROOT, load_params, load_record

DEMO = ROOT / "data" / "demo"


def non_good(tid, i=0):
    sel = selection(tid)
    return [r for r in sel["ranking"] if r not in sel["good"]][i]


def words_matching(words, phrase):
    toks = phrase.lower().split()
    ws = [w["word"].lower() for w in words]
    for i in range(len(ws) - len(toks) + 1):
        if ws[i:i + len(toks)] == toks:
            return i, i + len(toks) - 1
    raise ValueError(phrase)


def main():
    DEMO.mkdir(parents=True, exist_ok=True)
    # T2: rushed "And miles to go before I sleep" (second time) + dropped pause after "keep"
    rid = non_good("T2")
    r = load_record(REFS / "T2" / rid)
    c = inject.Clip(r["x"], r["words"])
    w0 = len(r["words"]) - 7
    inject.add_flaw(c, "pace_rushed", 4, w0, len(r["words"]) - 2)
    k = words_matching(r["words"], "promises to keep")[1]
    if r["feats"]["pause"][k] >= 0.15:
        inject.add_flaw(c, "missing_pause", 5, k, k + 1)
    audio.save(DEMO / "T2_rushed_and_dropped_pause.wav", c.render())
    (DEMO / "T2_rushed_and_dropped_pause.labels.json").write_text(
        json.dumps({"source": rid, "labels": inject.finalize_labels(c)}, indent=1))

    rid3 = non_good("T3")
    r3 = load_record(REFS / "T3" / rid3)
    c3 = inject.Clip(r3["x"], r3["words"])
    a, b = words_matching(r3["words"], "the world will little note")
    inject.add_flaw(c3, "monotone", 4, a, b + 3)
    audio.save(DEMO / "T3_monotone.wav", c3.render())
    (DEMO / "T3_monotone.labels.json").write_text(
        json.dumps({"source": rid3, "labels": inject.finalize_labels(c3)}, indent=1))

    # style pair: good T2 readers judged leave-one-out by K=1 vs K=all
    p = load_params()
    p1 = json.loads((ROOT / "results" / "results.json").read_text())["params"]["K=1"] \
        if (ROOT / "results" / "results.json").exists() else None
    from cadence.detect import Params
    p1 = Params(**p1) if p1 else p
    rows = []
    for g in selection("T2")["good"]:
        words, feats, _ = record("ref", "T2", g)
        single = detect(feats, words, envelope_for("T2", g, 1, "level"), p1)
        env = detect(feats, words, envelope_for("T2", g, None, "level"), p)
        rows.append({"reader": g, "single_reference_flags": len(single), "envelope_flags": len(env),
                     "single_pause_flags": [(x["type"], words[x["w0"]]["word"]) for x in single if "pause" in x["type"]]})
    rows.sort(key=lambda r: (r["envelope_flags"], -r["single_reference_flags"]))
    (DEMO / "style_pair.json").write_text(json.dumps(rows, indent=1))
    print(json.dumps(rows[:3], indent=1))


if __name__ == "__main__":
    main()
