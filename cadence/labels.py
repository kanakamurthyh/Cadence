"""Machine-readable labels for every synthetic clip, plus automated validation.

`cadence labels` writes data/labels/labels.jsonl and labels.csv (one row per label,
plus one row per clean reference and per null-edit control) and
data/labels/validation.json. Nothing here changes audio or scoring.

Validation (each check reported, never silently fixed):
  bounds     0 <= start < end <= audio duration; 0 <= w0 <= w1 < number of words
  timemap    label edges agree with an independent re-alignment of the modified audio
  duration   clip length - source length equals the edit's expected change (stretch, cut, insert)
  direction  the flaw's feature moved the intended way, beyond the null-edit margin m_f
  clicks     no sample-level discontinuity at cut/insert joins beyond the clip's own 99.9th pct
  null       null-edit controls have no labels and keep the source length
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import soundfile as sf

from .data.texts import TEXTS
from .envelope import fwd
from .inject import SEVERITY
from .pipeline import PARAMS, REFS, ROOT

LADDERS = ROOT / "data" / "ladders"
OUT = ROOT / "data" / "labels"
FEATURE = {"pace": "rate", "missing_pause": "pause", "misplaced_pause": "pause", "monotone": "pitch_range",
           "missed_emphasis": "prom_pitch", "volume_fade": "loud"}
DIRECTION = {"pace_rushed": +1, "pace_dragging": -1, "missing_pause": -1, "misplaced_pause": +1,
             "monotone": -1, "missed_emphasis": -1, "volume_fade": -1}
EDIT = {
    "pace_rushed": "PSOLA duration factor {p} over the span (pitch kept)",
    "pace_dragging": "PSOLA duration factor {p} over the span (pitch kept)",
    "missing_pause": "{p:.0%} of the boundary silence removed (10 ms crossfade)",
    "misplaced_pause": "{p} s of room tone inserted between the words (10 ms crossfades)",
    "monotone": "pitch compressed toward the span median, {p:.0%} of range kept (PSOLA)",
    "missed_emphasis": "pitch and loudness peak flattened to the neighbours' level, {p:.0%} kept (PSOLA + gain)",
    "volume_fade": "gain ramp to {p} dB over the first quarter of the span, held to its end",
}
TOL_TIMEMAP_S = 0.10   # CTC aligner tolerance; MFA reports 24 ms mean
TOL_DURATION_S = 0.03


def _json(path: Path) -> dict:
    return json.loads(path.read_text())


def _duration(wav: Path) -> float:
    i = sf.info(str(wav))
    return i.frames / i.samplerate


def _span_value(feats: dict, f: str, w0: int, w1: int) -> float | None:
    v = np.asarray([np.nan if x is None else x for x in feats[f][w0:w1 + 1]], float)
    return None if not np.isfinite(v).any() else float(np.nanmean(v))


def _expected_delta(flaw, src_words) -> float:
    typ, lvl, w0, w1 = flaw
    p = SEVERITY[typ][lvl - 1]
    if typ.startswith("pace"):
        a, b = src_words[w0]["start"], src_words[w1]["end"]
        return (p - 1) * (b - a)
    xf = 160 / 16000  # each crossfade join overlaps its two pieces by 10 ms (inject._crossfade_join)
    if typ == "misplaced_pause":
        return p - 2 * xf
    if typ == "missing_pause":
        s, e = src_words[w0]["end"], src_words[w0 + 1]["start"]
        keep = max(0.01, (1 - p) * (e - s))
        return -((e - s) - keep) - xf
    return 0.0


def _clicks(wav: Path, times: list[float]) -> list[float]:
    """Ratio of the local max second difference at each join to the clip's 99.9th percentile."""
    x, sr = sf.read(str(wav), dtype="float32")
    d2 = np.abs(np.diff(x, 2))
    ref = np.percentile(d2, 99.9) + 1e-9
    out = []
    for t in times:
        i = int(t * sr)
        w = d2[max(0, i - int(0.01 * sr)): i + int(0.01 * sr)]
        out.append(float(w.max() / ref) if len(w) else 0.0)
    return out


def build(texts: list[str] | None = None) -> dict:
    params = _json(PARAMS) if PARAMS.exists() else {"margin": {}}
    margin = params.get("margin", {})
    rows, problems = [], []
    checks = Counter()
    dist = defaultdict(list)
    for tid in texts or list(TEXTS):
        man_p = LADDERS / tid / "manifest.json"
        if not man_p.exists():
            continue
        man = _json(man_p)
        sources = {c["source"] for c in man if c["kind"] != "null"}
        for src in sorted(sources):
            meta = _json(REFS / tid / f"{src}.json")["meta"]
            rows.append({"clip_id": src, "audio_file": f"data/refs/{tid}/{src}.wav", "text_id": tid,
                         "text_title": TEXTS[tid]["title"], "reference_id": src, "speaker": meta.get("reader"),
                         "kind": "clean_reference", "is_clean": True, "is_null_edit": False,
                         "licence": meta.get("licence"), "provenance": meta.get("provenance") or meta.get("url")})
        for c in man:
            wav = LADDERS / tid / f"{c['id']}.wav"
            rec = _json(wav.with_suffix(".json"))
            src = _json(REFS / tid / f"{c['source']}.json")
            smeta = src["meta"]
            dur = _duration(wav)
            src_dur = _duration(REFS / tid / f"{c['source']}.wav")
            W = len(rec["words"])
            base = {"audio_file": f"data/ladders/{tid}/{c['id']}.wav", "clip_id": c["id"], "text_id": tid,
                    "text_title": TEXTS[tid]["title"], "reference_id": c["source"], "speaker": smeta.get("reader"),
                    "kind": c["kind"], "licence": smeta.get("licence"),
                    "provenance": smeta.get("provenance") or smeta.get("url"), "duration_s": round(dur, 4)}
            if c["kind"] == "null":
                ok = not c["labels"] and abs(dur - src_dur) <= TOL_DURATION_S
                checks["null " + ("ok" if ok else "FAIL")] += 1
                if not ok:
                    problems.append(f"{c['id']}: null-edit control has labels or changed length ({dur - src_dur:+.3f} s)")
                rows.append({**base, "is_clean": True, "is_null_edit": True, "flaw_type": "none",
                             "transformation": "PSOLA resynthesis with unmodified pitch and duration tiers"})
                continue
            exp = sum(_expected_delta(f, src["words"]) for f in c["flaws"])
            ok = abs((dur - src_dur) - exp) <= TOL_DURATION_S
            checks["duration " + ("ok" if ok else "FAIL")] += 1
            if not ok:
                problems.append(f"{c['id']}: length change {dur - src_dur:+.3f} s, expected {exp:+.3f} s")
            for lab, flaw in zip(c["labels"], c["flaws"]):
                typ, lvl, w0, w1 = flaw
                p = SEVERITY[typ][lvl - 1]
                row = {**base, "is_clean": False, "is_null_edit": False, "flaw_type": lab["type"],
                       "flaw_subtype": typ, "severity_injected": lvl, "severity_perceived": None,
                       "start_s": lab["start"], "end_s": lab["end"], "word_start": lab["w0"], "word_end": lab["w1"],
                       "words": " ".join(w["word"] for w in src["words"][lab["w0"]:lab["w1"] + 1]),
                       "parameter": p, "transformation": EDIT[typ].format(p=p)}
                # bounds
                b_ok = 0 <= lab["start"] < lab["end"] <= dur + 1e-3 and 0 <= lab["w0"] <= lab["w1"] < W
                checks["bounds " + ("ok" if b_ok else "FAIL")] += 1
                if not b_ok:
                    problems.append(f"{c['id']}: label out of bounds {lab}")
                # time map vs independent re-alignment of the modified audio
                cw = rec["words"]
                if typ == "misplaced_pause":
                    # where did the silence land? the largest measured pause near w0
                    near = [j for j in (w0 - 1, w0, w0 + 1) if 0 <= j < W - 1]
                    j = max(near, key=lambda k: (rec["feats"]["pause"][k] or 0))
                    err = max(abs(lab["start"] - cw[j]["end"]), abs(lab["end"] - cw[j + 1]["start"]))
                    row["word_attribution_offset"] = j - w0
                    a_ok = j == w0
                    checks["attribution " + ("ok" if a_ok else "OFF")] += 1
                    if not a_ok and lvl >= 3:
                        problems.append(f"{c['id']}: silence measured after word {j}, label says word {w0} "
                                        f"(time span correct within {err * 1000:.0f} ms; source boundary had no gap)")
                else:
                    err = max(abs(lab["start"] - cw[lab["w0"]]["start"]), abs(lab["end"] - cw[lab["w1"]]["end"]))
                row["timemap_err_s"] = round(err, 4)
                t_ok = err <= TOL_TIMEMAP_S
                checks["timemap " + ("ok" if t_ok else "FAIL")] += 1
                if not t_ok and lvl >= 3:
                    problems.append(f"{c['id']}: label edges {err * 1000:.0f} ms from the re-aligned words")
                # direction of the measured change
                f = FEATURE[lab["type"]]
                if typ in ("missing_pause", "misplaced_pause"):
                    k = w0 + row.get("word_attribution_offset", 0)
                    a0 = _span_value(src["feats"], f, k, k)
                    a1 = _span_value(rec["feats"], f, k, k)
                else:
                    a0 = _span_value(src["feats"], f, w0, w1)
                    a1 = _span_value(rec["feats"], f, w0, w1)
                row.update(feature=f, original_value=a0, modified_value=a1)
                if a0 is not None and a1 is not None:
                    delta = float(fwd(f, np.array(a1)) - fwd(f, np.array(a0)))
                    measurable = DIRECTION[typ] * delta > margin.get(f, 0.0)
                    row["delta_comparison_domain"] = round(delta, 4)
                    row["measurable"] = bool(measurable)
                    dist[(typ, lvl)].append(DIRECTION[typ] * delta)
                    checks["direction " + ("ok" if measurable else "weak")] += 1
                    if lvl == 5 and not measurable:
                        problems.append(f"{c['id']}: severity-5 {typ} did not move {f} beyond the margin")
                # clicks at joins
                if typ in ("missing_pause", "misplaced_pause"):
                    joins = [lab["start"], lab["end"]] if typ == "misplaced_pause" else \
                        [(cw[w0]["end"] + cw[w0 + 1]["start"]) / 2]
                    ratio = max(_clicks(wav, joins))
                    row["join_click_ratio"] = round(ratio, 3)
                    c_ok = ratio <= 1.0
                    checks["clicks " + ("ok" if c_ok else "FAIL")] += 1
                    if not c_ok:
                        problems.append(f"{c['id']}: discontinuity at a join ({ratio:.2f}x the clip's 99.9th pct)")
                rows.append(row)
    severity = {f"{t} L{l}": {"n": len(v), "median_change": round(float(np.median(v)), 4),
                              "measurable_frac": round(float(np.mean(np.array(v) > 0)), 2)}
                for (t, l), v in sorted(dist.items())}
    return {"rows": rows, "checks": dict(checks), "problems": problems, "severity_distribution": severity}


def main(texts: list[str] | None = None) -> dict:
    res = build(texts)
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "labels.jsonl").open("w") as fh:
        for r in res["rows"]:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    keys = sorted({k for r in res["rows"] for k in r})
    with (OUT / "labels.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(res["rows"])
    summary = {k: res[k] for k in ("checks", "problems", "severity_distribution")}
    summary["rows"] = len(res["rows"])
    (OUT / "validation.json").write_text(json.dumps(summary, indent=1, sort_keys=True))
    print(json.dumps({"rows": summary["rows"], "checks": res["checks"], "problems": len(res["problems"])}, indent=1))
    for p in res["problems"][:40]:
        print(" -", p)
    return summary
