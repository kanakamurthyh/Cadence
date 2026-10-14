"""Human ground truth (spec section 8): listening test and reader ranking.

Listening test: each listener rates one ladder per flaw type on the calibration
text (6 types x 5 severities + 6 clean null-edit clips = 36 clips, about 15 min)
on a 0-4 scale, "how much worse than the clean version", in a random order
seeded by the listener's name. Responses: data/listening/responses.csv.

Reader ranking: each rater scores every reader on a 20 s excerpt (1-10); scores
become ranks, and the mean rank picks the good set (data/rankings/<T>.csv).
"""
from __future__ import annotations

import csv
import hashlib
import json
import random
from datetime import UTC, datetime

import gradio as gr
import numpy as np

from .data.texts import TEXTS
from .pipeline import REFS, ROOT

LADDERS = ROOT / "data" / "ladders"
LISTEN = ROOT / "data" / "listening"
RANK = ROOT / "data" / "rankings"
CALIB = "T1"
EXCERPT_S = 20.0


def listening_trials() -> list[dict]:
    man = json.loads((LADDERS / CALIB / "manifest.json").read_text())
    by_id = {c["id"]: c for c in man}
    trials = []
    for c in man:
        if c["kind"] == "ladder" and ("_s0_" in c["id"]):
            # one ladder per type: pace uses the rushed ladder
            if c["id"].startswith(f"{CALIB}_pace-dragging"):
                continue
            trials.append({"clip": c["id"], "type": c["labels"][0]["type"], "level": c["labels"][0]["severity"],
                           "clean": f"{CALIB}_null_{c['source']}"})
    types = sorted({t["type"] for t in trials})
    src = next(c["source"] for c in man if c["kind"] == "ladder")
    for t in types:  # clean-vs-clean catch trials, one per type
        trials.append({"clip": f"{CALIB}_null_{src}", "type": t, "level": 0, "clean": f"{CALIB}_null_{src}"})
    assert all(t["clip"] in by_id for t in trials)
    return trials


def _norm(name: str) -> str:
    """One spelling per person: trimmed, single spaces, case-insensitive."""
    return " ".join(name.split()).lower()


def ladder_source() -> str:
    """The T1 rendition the listening clips were made from; responses are tied to it."""
    man = json.loads((LADDERS / CALIB / "manifest.json").read_text())
    return next(c["source"] for c in man if c["kind"] == "ladder")


def _order(name: str, n: int) -> list[int]:
    rng = random.Random(int(hashlib.sha256(_norm(name).encode()).hexdigest()[:8], 16))
    idx = list(range(n))
    rng.shuffle(idx)
    return idx


def _wav(cid: str) -> str:
    return str(LADDERS / CALIB / f"{cid}.wav")


def _segment_files(trial: dict) -> tuple[str, str]:
    """Play only the flawed region (+-2 s) of both clips so a trial takes ~20 s."""
    import soundfile as sf

    from .audio import SR
    man = {c["id"]: c for c in json.loads((LADDERS / CALIB / "manifest.json").read_text())}
    out = LISTEN / "segments"
    out.mkdir(parents=True, exist_ok=True)
    ref_trial = next(t for t in listening_trials() if t["type"] == trial["type"] and t["level"] > 0)
    lab = man[ref_trial["clip"]]["labels"][0]
    paths = []
    for cid in (trial["clean"], trial["clip"]):
        p = out / f"{ladder_source()}__{cid}__{trial['type']}.wav"
        if not p.exists():
            x, _ = sf.read(_wav(cid), dtype="float32")
            if cid.startswith(f"{CALIB}_null"):
                a, b = man[ref_trial["clip"]]["labels"][0]["w0"], lab["w1"]
                src = json.loads((LADDERS / CALIB / f"{cid}.json").read_text())["words"]
                s, e = src[a]["start"], src[b]["end"]
            else:
                lab2 = man[cid]["labels"][0]
                s, e = lab2["start"], lab2["end"]
            i, j = max(0, int((s - 2) * SR)), min(len(x), int((e + 2) * SR))
            sf.write(p, x[i:j], SR)
        paths.append(str(p))
    return paths[0], paths[1]


RESPONSE_FIELDS = ["listener", "clip", "type", "level", "rating", "source", "time"]


def responses(current_only: bool = True) -> list[dict]:
    """Listening responses; by default only those made on the current T1 ladders."""
    f = LISTEN / "responses.csv"
    if not f.exists():
        return []
    rows = list(csv.DictReader(f.open()))
    if current_only:
        src = ladder_source()
        rows = [r for r in rows if r.get("source") == src]
    return rows


def save_response(name, i, rating):
    LISTEN.mkdir(parents=True, exist_ok=True)
    trials = listening_trials()
    if i >= len(trials):
        return
    t = trials[_order(name, len(trials))[i]]
    f = LISTEN / "responses.csv"
    new = not f.exists()
    with f.open("a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(RESPONSE_FIELDS)
        w.writerow([_norm(name), t["clip"], t["type"], t["level"], int(rating), ladder_source(),
                    datetime.now(UTC).isoformat(timespec="seconds")])


def perceived_by_level() -> dict[tuple[str, int], float]:
    """Mean listener rating (0-4) per (flaw type, injected level), current ladders only."""
    out = {}
    rows = responses()
    for typ in {r["type"] for r in rows}:
        for L in range(1, 6):
            v = [int(r["rating"]) for r in rows if r["type"] == typ and int(r["level"]) == L]
            if v:
                out[(typ, L)] = float(np.mean(v))
    return out


def summarize_listening() -> dict:
    """Mean perceived severity per type and level, lowest audible level, Spearman."""
    from .metrics import spearman
    rows = responses()
    if not rows:
        stale = len(responses(current_only=False))
        return {"status": "pending: no responses yet" if not stale else
                f"pending: {stale} responses were made on older ladders and are ignored"}
    listeners = sorted({r["listener"] for r in rows})
    complete = [l for l in listeners if sum(r["listener"] == l for r in rows) >= len(listening_trials())]
    out = {"status": f"{len(complete)} complete listeners ({len(listeners)} started)",
           "listeners": listeners, "complete_listeners": complete, "by_type": {}}
    for typ in sorted({r["type"] for r in rows}):
        rr = [r for r in rows if r["type"] == typ]
        lv = {}
        for L in range(0, 6):
            v = [int(r["rating"]) for r in rr if int(r["level"]) == L]
            if v:
                lv[L] = {"mean": float(np.mean(v)), "n": len(v), "heard": float(np.mean([x >= 1 for x in v]))}
        audible = next((L for L in range(1, 6) if L in lv and lv[L]["heard"] > 0.5), None)
        out["by_type"][typ] = {
            "levels": lv, "lowest_audible_level": audible,
            "spearman_injected_vs_perceived": spearman([int(r["level"]) for r in rr], [int(r["rating"]) for r in rr]),
        }
    return out


def reader_excerpts(tid: str) -> list[tuple[str, str]]:
    import soundfile as sf

    from .audio import SR
    out = RANK / "excerpts" / tid
    out.mkdir(parents=True, exist_ok=True)
    items = []
    for p in sorted(q for q in (REFS / tid).glob("*.wav")):
        q = out / p.name
        if not q.exists():
            x, _ = sf.read(p, dtype="float32")
            sf.write(q, x[: int(EXCERPT_S * SR)], SR)
        items.append((p.stem, str(q)))
    rng = random.Random(tid)
    rng.shuffle(items)
    return items


def save_ranking(tid: str, rater: str, ratings: list) -> str:
    if not rater or not rater.strip():
        raise gr.Error("Enter your name before saving.")
    rater = _norm(rater)
    items = reader_excerpts(tid)
    RANK.mkdir(parents=True, exist_ok=True)
    f = RANK / f"{tid}_ratings.csv"
    new = not f.exists()
    with f.open("a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["rater", "id", "rating"])
        for (rid, _), r in zip(items, ratings):
            w.writerow([rater.strip(), rid, r])
    # ratings -> ranks per rater -> data/rankings/<T>.csv (consumed by build_refs.select)
    rows = list(csv.DictReader(f.open()))
    raters = sorted({r["rater"] for r in rows})
    ids = sorted({r["id"] for r in rows})
    ranks = {}
    for ra in raters:
        sc = {r["id"]: float(r["rating"]) for r in rows if r["rater"] == ra}
        order = sorted(sc, key=lambda i: -sc[i])
        ranks[ra] = {i: order.index(i) + 1 for i in order}
    with (RANK / f"{tid}.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", *raters])
        for i in ids:
            w.writerow([i, *[ranks[ra].get(i, "") for ra in raters]])
    return f"Saved {len(items)} ratings from {rater} ({len(raters)} raters so far). Rerun `cadence refs` to update the good set."


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Cadence human studies") as ui:
        with gr.Tab("Listening test"):
            gr.Markdown("Play **clean**, then **test**. Rate how much worse the test clip sounds than the clean "
                        "one: 0 = no difference, 4 = much worse. 36 trials, about 15 minutes. Use headphones.")
            name = gr.Textbox(label="Your name")
            idx = gr.State(0)
            start = gr.Button("Start / resume")
            prog = gr.Markdown()
            with gr.Row():
                clean = gr.Audio(label="clean", interactive=False)
                test = gr.Audio(label="test", interactive=False)
            rating = gr.Radio([0, 1, 2, 3, 4], label="How much worse is the test clip?")
            nxt = gr.Button("Save and next", variant="primary")

            def show(nm, i):
                trials = listening_trials()
                if i >= len(trials):
                    return None, None, "**Done - thank you!**", i
                t = trials[_order(nm, len(trials))[i]]
                c, x = _segment_files(t)
                return c, x, f"Trial {i + 1} of {len(trials)}", i

            def resume(nm):
                if not nm.strip():
                    raise gr.Error("Enter your name first.")
                done = sum(1 for r in responses() if r["listener"] == _norm(nm))
                return show(nm, done)

            def advance(nm, i, r):
                if i >= len(listening_trials()):
                    return (*show(nm, i), None)
                if r is None:
                    raise gr.Error("Pick a rating.")
                save_response(nm, i, r)
                return (*show(nm, i + 1), None)

            start.click(resume, name, [clean, test, prog, idx])
            nxt.click(advance, [name, idx, rating], [clean, test, prog, idx, rating])
        with gr.Tab("Rank readers"):
            gr.Markdown(f"Score every reader's first {EXCERPT_S:.0f} s from 1 (weak) to 10 (excellent delivery).")
            tid = gr.Dropdown(list(TEXTS), value="T1", label="Text")
            rater = gr.Textbox(label="Your name")
            n_max = 30
            players, sliders = [], []
            for i in range(n_max):
                with gr.Row(visible=False) as row:
                    players.append((row, gr.Audio(label=f"reader {i + 1}", interactive=False),
                                    gr.Slider(1, 10, value=5, step=1, label="score")))
            done = gr.Markdown()
            btn = gr.Button("Save my scores", variant="primary")

            def load(t):
                items = reader_excerpts(t)
                ups = []
                for i, (row, au, sl) in enumerate(players):
                    vis = i < len(items)
                    ups += [gr.update(visible=vis), items[i][1] if vis else None, 5]
                return ups

            outs = [c for trip in players for c in trip]
            tid.change(load, tid, outs)
            ui.load(load, tid, outs)
            btn.click(lambda t, r, *s: save_ranking(t, r, list(s)[: len(reader_excerpts(t))]),
                      [tid, rater, *[p[2] for p in players]], done)
    return ui


def main():
    build_ui().launch(server_name="0.0.0.0", server_port=7861)
