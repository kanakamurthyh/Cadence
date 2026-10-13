"""Gradio dashboard: upload, envelope overlay, flaw cards, A/B playback,
dataset explorer and evidence screen (spec sections 6 and 9)."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import gradio as gr
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from . import audio
from .data.texts import TEXTS
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


def run_analysis(file, text_choice, k):
    if file is None:
        raise gr.Error("Upload or record a delivery first.")
    tid = text_choice.split(":")[0]
    rep, rec = analyze(file, tid, k=int(k) if k else None)
    out = Path(tempfile.mkdtemp()) / f"cadence_report_{rep['hash']}.json"
    out.write_text(json.dumps(rep, indent=1, sort_keys=True))
    choices = [f"#{i} {r['type']} ({r['start']:.1f}-{r['end']:.1f} s)" for i, r in enumerate(rep["regions"], 1)]
    state = {"rep": rep, "x": rec["x"], "tid": tid}
    return (overlay(rep), cards(rep), score_table(rep), str(out), f"Output hash: `{rep['hash']}`",
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
    with gr.Blocks(title="Cadence", theme=gr.themes.Soft()) as ui:
        gr.Markdown("# Cadence\nA word is flagged only when your delivery leaves the range that several "
                    "strong renditions of the same text occupy. Every flag comes with measured numbers.")
        with gr.Tab("Analyze"):
            with gr.Row():
                with gr.Column(scale=1):
                    text = gr.Dropdown(TEXT_CHOICES, value=TEXT_CHOICES[1], label="Text")
                    upload = gr.Audio(sources=["upload", "microphone"], type="filepath", label="Your delivery")
                    k = gr.Slider(1, 6, value=6, step=1, label="Good renditions in the envelope (K)")
                    go_btn = gr.Button("Analyze", variant="primary")
                    hashmd = gr.Markdown()
                    scores_df = gr.Dataframe(headers=["dimension", "score (0-10)"], label="Rubric")
                    report_file = gr.File(label="JSON report")
                with gr.Column(scale=2):
                    plot = gr.Plot(label="Envelope overlay")
            flaw_html = gr.HTML()
            with gr.Row():
                region = gr.Dropdown([], label="A/B playback: pick a flagged region")
            with gr.Row():
                a_play = gr.Audio(label="A: you", interactive=False)
                b_play = gr.Audio(label="B: good rendition", interactive=False)
            ab_note = gr.Markdown()
            state = gr.State()
            go_btn.click(run_analysis, [upload, text, k],
                         [plot, flaw_html, scores_df, report_file, hashmd, region, state])
            region.change(ab_play, [region, state], [a_play, b_play, ab_note])
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
