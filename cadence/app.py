"""Gradio dashboard: upload, envelope overlay, flaw cards, A/B playback,
dataset explorer and evidence screen (spec sections 6 and 9)."""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import gradio as gr
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from . import audio
from .align import words_of
from .data.texts import CONTEXT, MIN_GOOD, SPEECHES, TEXTS, display_text
from .detect import DIMENSIONS
from .pipeline import REFS, ROOT, analyze, good_set, load_record

LADDERS = ROOT / "data" / "ladders"
RESULTS = ROOT / "results" / "results.json"
TYPE_COLOR = {
    "pace": "#d97706", "missing_pause": "#2563eb", "misplaced_pause": "#7c3aed",
    "monotone": "#dc2626", "missed_emphasis": "#db2777", "volume_fade": "#0d9488",
}
LANE_TITLE = {"pitch_range": "Pitch range (st)", "rate": "Rate (syll/s)",
              "loud": "Loudness (dB re median)", "pause": "Pause after word (s)"}
TEXT_CHOICES = [f"{k}: {v['title']}" for k, v in TEXTS.items()]


def _analyzable(tid: str) -> bool:
    try:
        return len(good_set(tid)) >= MIN_GOOD
    except FileNotFoundError:
        return False


# Analyze offers the speeches first (T4 by default, see DEFAULT_CHOICE), research texts on request, and only texts with an envelope (T5 waits for takes)
SPEECH_CHOICES = [c for c in TEXT_CHOICES if c.split(":")[0] in SPEECHES and _analyzable(c.split(":")[0])]
RESEARCH_CHOICES = [c for c in TEXT_CHOICES if c.split(":")[0] not in SPEECHES and _analyzable(c.split(":")[0])]
ANALYZE_CHOICES = SPEECH_CHOICES + RESEARCH_CHOICES
# T4 by default: under the shipped (v2) detector it gives good speakers the fewest false flags
# (0.24/min vs 1.47 for T3) with the higher Matching Score (40% vs 35%); see results/results.md
DEFAULT_CHOICE = next(c for c in SPEECH_CHOICES if c.startswith("T4"))
PENDING = [f"{t}: {TEXTS[t]['title']}" for t in SPEECHES if not _analyzable(t)]


def text_choices(show_research: bool, current: str):
    choices = SPEECH_CHOICES + (RESEARCH_CHOICES if show_research else [])
    return gr.update(choices=choices, value=current if current in choices else DEFAULT_CHOICE)
CSS = """
.cad-passage {font-family: Georgia, 'Times New Roman', serif; font-size: 18px; line-height: 1.65;
  white-space: pre-line; background: var(--block-background-fill); border: 1px solid var(--border-color-primary);
  border-left: 4px solid var(--color-accent); border-radius: 10px; padding: 18px 22px;
  color: var(--body-text-color);}
@media (max-width: 640px) {.cad-passage {font-size: 15.5px; line-height: 1.55; padding: 14px 14px;}}
@media (min-width: 900px) {.cad-sticky {position: sticky; top: 12px; align-self: flex-start;}}
.cad-meta {font-size: 14px; color: var(--body-text-color-subdued); margin: 4px 0 10px;}
.cad-step {font-weight: 600; font-size: 16px; margin: 2px 0 6px;}
.cad-note {font-size: 12.5px; color: var(--body-text-color-subdued); line-height: 1.5;}
"""


def overlay(rep: dict) -> go.Figure:
    lanes = ["pitch_range", "rate", "loud", "pause"]
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.04,
                        subplot_titles=[LANE_TITLE[l] for l in lanes])
    w = rep["words"]
    t = np.array([(x["start"] + x["end"]) / 2 for x in w])
    labels = [x["word"] for x in w]
    for i, lane in enumerate(lanes, 1):
        L = rep["lanes"][lane]
        lo = np.array([np.nan if v is None else v for v in L["lo"]], float)
        hi = np.array([np.nan if v is None else v for v in L["hi"]], float)
        val = np.array([np.nan if v is None else v for v in L["value"]], float)
        fig.add_trace(go.Scatter(x=t, y=hi, mode="lines", line=dict(width=0, shape="hvh"),
                                 showlegend=False, hoverinfo="skip"), row=i, col=1)
        fig.add_trace(go.Scatter(x=t, y=lo, mode="lines", fill="tonexty", line=dict(width=0, shape="hvh"),
                                 fillcolor="rgba(100,116,139,0.25)",
                                 name=f"good renditions (K={rep['k']})", showlegend=i == 1,
                                 hoverinfo="skip"), row=i, col=1)
        fig.add_trace(go.Scatter(x=t, y=val, mode="lines+markers", line=dict(color="#111827", width=1.5),
                                 marker=dict(size=4), text=labels, name="your delivery", showlegend=i == 1,
                                 hovertemplate="%{text}: %{y:.2f}<extra></extra>"), row=i, col=1)
    for r in rep["regions"]:
        fig.add_vrect(x0=r["start"], x1=r["end"], fillcolor=TYPE_COLOR[r["type"]], opacity=0.22,
                      line_width=0, row="all", col=1)
    for s in rep["stress_points"]:
        fig.add_vline(x=t[s], line=dict(color="#db2777", width=1, dash="dot"), row=1, col=1)
    fig.update_layout(height=720, margin=dict(l=40, r=20, t=40, b=30), template="plotly_white",
                      legend=dict(orientation="h", y=1.06), hovermode="x unified")
    fig.update_xaxes(title_text="time (s)", row=4, col=1)
    return fig


def cards(rep: dict) -> str:
    if not rep["regions"]:
        return "<p>No region falls outside the range of the good renditions.</p>"
    out = []
    for i, r in enumerate(rep["regions"], 1):
        c = TYPE_COLOR[r["type"]]
        out.append(
            f"<div style='border-left:5px solid {c};padding:8px 12px;margin:8px 0;"
            f"background:rgba(0,0,0,0.03);border-radius:6px'>"
            f"<b>#{i} {r['type'].replace('_', ' ')}</b> &middot; severity {r['severity']:.1f} "
            f"&middot; d = {r['d_mean']:.2f}<br>{r['explanation']}</div>")
    return "".join(out) + f"<p style='font-size:12px;opacity:.7'>Severity scale: {rep['severity_scale']}</p>"


def score_table(rep: dict) -> list[list]:
    return [[d.replace("_", " "), rep["scores"][d]] for d in DIMENSIONS]


def _segment(x: np.ndarray, a: float, b: float, pad: float = 0.3):
    i, j = max(0, int((a - pad) * audio.SR)), min(len(x), int((b + pad) * audio.SR))
    return audio.SR, (np.clip(x[i:j], -1, 1) * 32767).astype(np.int16)


def to_playable_wav(file):
    """Transcode an upload to 16-bit PCM WAV so every browser can play it.

    WhatsApp voice notes (.opus, Ogg-Opus) do not play in Safari, and Python serves .m4a as
    audio/mp4a-latm, which browsers refuse; the player then sits at 0:00. Analysis decodes
    any format with ffmpeg, so this only affects playback.
    """
    if not file or str(file).lower().endswith(".wav"):
        return file
    out = Path(tempfile.mkdtemp()) / (Path(file).stem + ".wav")
    try:
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(file), "-ac", "1",
                        "-ar", "44100", "-c:a", "pcm_s16le", str(out)], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        raise gr.Error(f"Could not read this audio file: {e.stderr.decode(errors='ignore')[-200:]}")
    return str(out)


def passage(text_choice: str) -> str:
    """Title, context, the full transcript (with line breaks) and the expected duration."""
    import html
    tid = text_choice.split(":")[0]
    t = TEXTS[tid]
    n = len(words_of(t["text"]))
    durs = []
    try:
        for g in good_set(tid):
            durs.append(json.loads((REFS / tid / f"{g}.json").read_text())["meta"]["duration"])
    except FileNotFoundError:
        pass
    took = (f" &middot; expected duration about {int(np.median(durs))} s (good speakers: "
            f"{int(min(durs))}&ndash;{int(max(durs))} s)") if durs else ""
    kind = "Speech" if tid in SPEECHES else "Research benchmark text"
    return (f"<div class='cad-step'>1. Deliver this entire passage, from the first word to the last</div>"
            f"<div class='cad-meta'><b>{kind}: {html.escape(t['title'])}</b>, {html.escape(t['author'])}<br>"
            f"{html.escape(CONTEXT.get(tid, ''))}<br>{n} words{took} &middot; do not read the title</div>"
            f"<div class='cad-passage'>{html.escape(display_text(tid))}</div>")


def run_analysis(file, text_choice, k, mode="Consensus envelope (B2, default)"):
    if file is None:
        raise gr.Error("Upload or record a delivery first.")
    tid = text_choice.split(":")[0]
    from .align import TextNotFound
    try:
        rep, rec = analyze(file, tid, k=1 if mode.startswith("Single") else (int(k) if k else None))
    except TextNotFound as e:
        raise gr.Error(f"{e} Text: {TEXTS[tid]['title']}.")
    out = Path(tempfile.mkdtemp()) / f"cadence_report_{rep['hash']}.json"
    out.write_text(json.dumps(rep, indent=1, sort_keys=True))
    choices = [f"#{i} {r['type']} ({r['start']:.1f}-{r['end']:.1f} s)" for i, r in enumerate(rep["regions"], 1)]
    state = {"rep": rep, "x": rec["x"], "tid": tid}
    n = len(rep["regions"])
    how = ("the single top-ranked good rendition (B1)" if rep["k"] == 1
           else f"the range of {rep['k']} good renditions (B2)")
    summary = (f"### Result: {n} flagged region{'s' if n != 1 else ''}\n"
               f"Compared with {how} of *{TEXTS[tid]['title']}*. "
               + ("Pick a region below to hear yourself next to a good reader." if n else
                  "Every word stayed inside the range of the good renditions."))
    return (gr.update(visible=True), summary, overlay(rep), cards(rep), score_table(rep), str(out),
            f"Output hash: `{rep['hash']}` (identical input gives identical output)",
            gr.update(choices=choices, value=choices[0] if choices else None), state)


def ab_play(choice, state):
    if not choice or not state:
        return None, None, ""
    rep = state["rep"]
    r = rep["regions"][int(choice.split()[0][1:]) - 1]
    you = _segment(state["x"], r["start"], r["end"])
    ref_id = rep["references"][0]
    ref = load_record(REFS / state["tid"] / ref_id)
    w0, w1 = ref["words"][r["w0"]], ref["words"][min(r["w1"] + 1, len(ref["words"]) - 1) if "pause" in r["type"] else r["w1"]]
    good = _segment(ref["x"], w0["start"], w1["end"])
    return you, good, f"B = top-ranked good rendition ({ref['meta'].get('reader', ref_id)}), same words."


# -- demo -------------------------------------------------------------------------

DEMO_TID = "T3"


def demo_case() -> dict | None:
    f = ROOT / "data" / "demo" / f"demo_{DEMO_TID}.json"
    return json.loads(f.read_text()) if f.exists() else None


def demo_intro() -> str:
    d = demo_case()
    if not d:
        return "Run `uv run cadence demo` to select the demo case from computed results."
    lab = d["label"]
    from .labels import EDIT
    from .inject import SEVERITY
    sub = lab.get("subtype")
    key = f"pace_{sub}" if lab["type"] == "pace" else lab["type"]
    edit = EDIT[key].format(p=SEVERITY[key][lab["severity"] - 1])
    return (f"### Same words, two deliveries\n"
            f"**A (reference):** {d['source_speaker']} reading *{TEXTS[d['text_id']]['title']}* "
            f"({d['source_licence']}).\n\n"
            f"**B (flawed):** the same recording with one known, labelled modification:\n\n"
            f"| Flaw | Severity | Words | Time in clip B | Exact edit |\n|---|---|---|---|---|\n"
            f"| {lab['type'].replace('_', ' ')}{' (' + sub + ')' if sub else ''} | {lab['severity']} of 5 | "
            f"{lab['w0'] + 1}-{lab['w1'] + 1}: \"{d['label_words']}\" | {lab['start']:.2f}-{lab['end']:.2f} s | {edit} |\n\n"
            f"Clip B is compared with the other good renditions only (A is excluded from the envelope). "
            f"A deviation from strong references marks a *potential* delivery issue, not proof of poor speaking.")


def _other_flags(rep: dict, hit: dict, d: dict) -> str:
    """Other flags on clip B, marking those the untouched recording A also gets (its own style)."""
    src = d.get("b2_flags_on_untouched_source", [])
    out = []
    for g in rep["regions"]:
        if g is hit:
            continue
        on_a = any(g["type"] == s["type"] and g["w0"] <= s["w1"] + 1 and s["w0"] <= g["w1"] + 1 for s in src)
        out.append(f"{g['type'].replace('_', ' ')} at words {g['w0'] + 1}-{g['w1'] + 1}"
                   + (" (also flagged on A: the reader's own style, not the edit)" if on_a else " (not on A)"))
    return ("Other flags on clip B: " + "; ".join(out) + ".") if out else "No other flags on clip B."


def run_demo():
    d = demo_case()
    if not d:
        raise gr.Error("No demo case yet: run `uv run cadence demo`.")
    from .metrics import iou
    rep, rec = analyze(ROOT / d["flawed_wav"], d["text_id"], locate=False, exclude=(d["source_id"],))
    lab = d["label"]
    same = [(iou(lab, r), r) for r in rep["regions"] if r["type"] == lab["type"]]
    v, r = max(same, key=lambda x: x[0]) if same else (0.0, None)
    verdict = (f"**Verified live:** Cadence flagged **{r['type'].replace('_', ' ')}** at {r['start']:.2f}-{r['end']:.2f} s; "
               f"the label is {lab['start']:.2f}-{lab['end']:.2f} s (onset error {abs(r['start'] - lab['start']) * 1000:.0f} ms, "
               f"offset error {abs(r['end'] - lab['end']) * 1000:.0f} ms, IoU {v:.2f}: "
               f"{'a match (type correct and IoU >= 0.5)' if v >= 0.5 else 'NOT a match'}). "
               + _other_flags(rep, r, d)
               if r else "**Not detected in this run.** The demo case no longer matches; rerun `cadence demo`.")
    rows = []
    for name, m in d["methods"].items():
        reg = m["region"]
        rows.append([name, "yes" if m["matched"] else "no", m["iou"],
                     f"{reg['start']:.2f}-{reg['end']:.2f} s" if reg else "no flag of this type",
                     ", ".join(sorted(set(m["types_overlapping_label"]))) or "-", m["n_flags"]])
    choices = [f"#{i} {g['type']} ({g['start']:.1f}-{g['end']:.1f} s)" for i, g in enumerate(rep["regions"], 1)]
    state = {"rep": rep, "x": rec["x"], "tid": d["text_id"]}
    return (verdict, overlay(rep), cards(rep), score_table(rep), rows,
            gr.update(choices=choices, value=choices[0] if choices else None), state)


# -- dataset explorer -----------------------------------------------------------

def ladder_options(text_choice):
    tid = text_choice.split(":")[0]
    man = LADDERS / tid / "manifest.json"
    if not man.exists():
        return gr.update(choices=[], value=None)
    ids = sorted({c["id"].rsplit("_L", 1)[0] for c in json.loads(man.read_text()) if c["kind"] == "ladder"})
    return gr.update(choices=ids, value=ids[0] if ids else None)


def ladder_play(text_choice, ladder):
    tid = text_choice.split(":")[0]
    if not ladder:
        return [None] * 7 + [""]
    man = {c["id"]: c for c in json.loads((LADDERS / tid / "manifest.json").read_text())}
    src = man[f"{ladder}_L1"]["source"]
    orig = str(REFS / tid / f"{src}.wav")
    null = str(LADDERS / tid / f"{tid}_null_{src}.wav")
    lv = [str(LADDERS / tid / f"{ladder}_L{i}.wav") for i in range(1, 6)]
    labs = [man[f"{ladder}_L{i}"]["labels"][0] for i in range(1, 6)]
    info = "\n".join(f"- severity {l['severity']}: {l['type']} param={l['param']} "
                     f"words {l['w0'] + 1}-{l['w1'] + 1}, {l['start']:.2f}-{l['end']:.2f} s" for l in labs)
    return [orig, null] + lv + [info]


# -- evidence -------------------------------------------------------------------

def evidence() -> tuple[str, go.Figure | None]:
    if not RESULTS.exists():
        return "Run `cadence evaluate` to produce results/results.json.", None
    res = json.loads(RESULTS.read_text())
    md = (ROOT / "results" / "results.md").read_text() if (ROOT / "results" / "results.md").exists() else ""
    fig = go.Figure()
    for name, pts in res.get("sweep", {}).get("T2", {}).items():
        fig.add_trace(go.Scatter(x=[p["fa_per_min"] for p in pts], y=[p["matching_score"] for p in pts],
                                 mode="lines+markers", name=name,
                                 text=[f"tau={p['tau']}" for p in pts]))
    fig.update_layout(template="plotly_white", height=380, title="T2: Matching Score vs false alarms on good-vs-good pairs",
                      xaxis_title="false alarms per minute (good renditions, leave one out)",
                      yaxis_title="Matching Score (type + IoU >= 0.5)")
    return md, fig


def build_ui() -> gr.Blocks:
    theme = gr.themes.Soft(font=["ui-sans-serif", "-apple-system", "system-ui", "Segoe UI", "sans-serif"])
    with gr.Blocks(title="Cadence", theme=theme, css=CSS) as ui:
        gr.Markdown("# Cadence\nA word is flagged only when your delivery leaves the range that several "
                    "strong renditions of the same text occupy. Every flag comes with measured numbers.")
        with gr.Tab("Analyze"):
            with gr.Row(equal_height=False):
                with gr.Column(scale=3, min_width=320):
                    text = gr.Dropdown(SPEECH_CHOICES, value=DEFAULT_CHOICE, label="Speech",
                                       info=("Pending: " + "; ".join(PENDING) + " (needs 4 good recordings)")
                                       if PENDING else None)
                    research = gr.Checkbox(False, label="Show research benchmark texts (poetry)")
                    to_read = gr.HTML(passage(DEFAULT_CHOICE))
                with gr.Column(scale=2, min_width=300, elem_classes="cad-sticky"):
                    gr.HTML("<div class='cad-step'>2. Record it (or upload a recording)</div>")
                    upload = gr.Audio(sources=["microphone", "upload"], type="filepath", format="wav",
                                      label="Your delivery", show_label=False)
                    gr.HTML("<div class='cad-note'>Click <b>Record</b>, allow the microphone, read the whole "
                            "passage, then <b>Stop</b>. Quiet room, about 30 cm from the mic. The microphone "
                            "works on http://localhost or https only (not on a LAN IP). Uploads of any format "
                            "(WhatsApp .opus, .m4a, .mp3) are converted automatically.</div>")
                    gr.HTML("<div class='cad-step' style='margin-top:14px'>3. Analyze</div>")
                    go_btn = gr.Button("Analyze my delivery", variant="primary", size="lg")
                    with gr.Accordion("Comparison method", open=False):
                        mode = gr.Radio(["Consensus envelope (B2, default)", "Single best reference (B1 fallback)"],
                                        value="Consensus envelope (B2, default)", show_label=False,
                                        info="B1 compares with the top-ranked good reader only, with its own "
                                             "calibrated thresholds. On the untouched test text (T6) B1 was "
                                             "more reliable than B2; see the Evidence tab.")
                        k = gr.Slider(2, 6, value=6, step=1, label="Good renditions in the envelope (K)")
            with gr.Column(visible=False) as results:
                summary = gr.Markdown()
                with gr.Row(equal_height=False):
                    with gr.Column(scale=1, min_width=260):
                        scores_df = gr.Dataframe(headers=["dimension", "score (0-10)"], label="Rubric scores",
                                                 interactive=False)
                    with gr.Column(scale=2, min_width=320):
                        flaw_html = gr.HTML()
                plot = gr.Plot(label="Your delivery (line) against the good renditions (grey band)")
                region = gr.Dropdown([], label="A/B playback: pick a flagged region")
                with gr.Row():
                    a_play = gr.Audio(label="A: you", interactive=False)
                    b_play = gr.Audio(label="B: good rendition, same words", interactive=False)
                ab_note = gr.Markdown()
                with gr.Accordion("JSON report and reproducibility hash", open=False):
                    hashmd = gr.Markdown()
                    report_file = gr.File(label="JSON report")
            state = gr.State()
            upload.upload(to_playable_wav, upload, upload)  # .upload only fires on user uploads: no loop
            upload.stop_recording(to_playable_wav, upload, upload)
            text.change(passage, text, to_read)
            research.change(text_choices, [research, text], text)
            go_btn.click(run_analysis, [upload, text, k, mode],
                         [results, summary, plot, flaw_html, scores_df, report_file, hashmd, region, state])
            region.change(ab_play, [region, state], [a_play, b_play, ab_note])
        with gr.Tab("Demo"):
            d = demo_case()
            gr.Markdown(demo_intro())
            with gr.Row():
                gr.Audio(str(ROOT / d["source_wav"]) if d else None, label="A: reference delivery",
                         interactive=False)
                gr.Audio(str(ROOT / d["flawed_wav"]) if d else None, label="B: same recording, labelled flaw",
                         interactive=False)
            demo_btn = gr.Button("Run Cadence on B", variant="primary")
            demo_verdict = gr.Markdown()
            demo_cmp = gr.Dataframe(headers=["method", "matches label", "IoU", "region of that type",
                                             "flag types over the label", "flags on clip"],
                                    label="Same clip, three methods (benchmark run, parameters fitted on T1)",
                                    interactive=False)
            with gr.Row(equal_height=False):
                with gr.Column(scale=1, min_width=260):
                    demo_scores = gr.Dataframe(headers=["dimension", "score (0-10)"], label="Rubric scores",
                                               interactive=False)
                with gr.Column(scale=2, min_width=320):
                    demo_cards = gr.HTML()
            demo_plot = gr.Plot(label="Clip B (line) against the good renditions (grey band)")
            demo_region = gr.Dropdown([], label="A/B playback: pick a flagged region")
            with gr.Row():
                demo_a = gr.Audio(label="B at the flag", interactive=False)
                demo_b = gr.Audio(label="good rendition, same words", interactive=False)
            demo_note = gr.Markdown()
            demo_state = gr.State()
            demo_btn.click(run_demo, None, [demo_verdict, demo_plot, demo_cards, demo_scores, demo_cmp,
                                            demo_region, demo_state])
            demo_region.change(ab_play, [demo_region, demo_state], [demo_a, demo_b, demo_note])
        with gr.Tab("Dataset explorer"):
            dtext = gr.Dropdown(TEXT_CHOICES, value=TEXT_CHOICES[1], label="Text")
            ladder = gr.Dropdown([], label="Ladder")
            with gr.Row():
                orig = gr.Audio(label="original", interactive=False)
                null = gr.Audio(label="null-edit copy (same processing, no change)", interactive=False)
            with gr.Row():
                lv = [gr.Audio(label=f"severity {i}", interactive=False) for i in range(1, 6)]
            linfo = gr.Markdown()
            dtext.change(ladder_options, dtext, ladder)
            ui.load(ladder_options, dtext, ladder)
            ladder.change(ladder_play, [dtext, ladder], [orig, null, *lv, linfo])
        with gr.Tab("Evidence"):
            ev_md = gr.Markdown()
            ev_plot = gr.Plot()
            ui.load(evidence, None, [ev_md, ev_plot])
    return ui


def main():
    build_ui().launch(server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    main()
