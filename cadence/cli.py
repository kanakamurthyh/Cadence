"""cadence <command>: one entry point for the whole pipeline."""
import argparse
import json
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main(argv=None):
    ap = argparse.ArgumentParser(prog="cadence")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fetch", help="download LibriVox readings")
    sub.add_parser("refs", help="crop, align and measure every reading; pick the good set")
    sub.add_parser("ladders", help="build synthetic ladders and null-edit controls")
    b = sub.add_parser("evaluate", help="calibrate on T1, evaluate on T2/T3, write results/")
    b.add_argument("--no-ablations", action="store_true")
    sub.add_parser("all", help="fetch -> refs -> ladders -> evaluate")
    a = sub.add_parser("analyze", help="analyze one recording, print the JSON report")
    a.add_argument("audio")
    a.add_argument("--text", default="T2")
    a.add_argument("--k", type=int)
    a.add_argument("--out")
    sub.add_parser("status", help="check which human-data steps are done and consistent")
    sub.add_parser("natural", help="check teammate takes + annotations, evaluate natural flaws")
    c = sub.add_parser("compare", help="compare current results with a frozen baseline")
    c.add_argument("--baseline", default="results/baseline_2026-10-13")
    sub.add_parser("app", help="Gradio dashboard on :7860")
    sub.add_parser("human", help="listening test and reader ranking on :7861")
    sub.add_parser("api", help="FastAPI on :8000")
    args = ap.parse_args(argv)

    def script(name):
        sys.argv = [name]
        runpy.run_path(str(ROOT / "scripts" / name), run_name="__main__")

    if args.cmd in ("fetch", "all"):
        script("fetch_librivox.py")
    if args.cmd in ("refs", "all"):
        script("build_refs.py")
    if args.cmd in ("ladders", "all"):
        script("build_ladders.py")
    if args.cmd in ("evaluate", "all"):
        from .benchmark import main as bench
        bench(ablations=not getattr(args, "no_ablations", False))
    if args.cmd == "analyze":
        from .pipeline import analyze
        rep, _ = analyze(args.audio, args.text, k=args.k)
        s = json.dumps(rep, indent=1, sort_keys=True)
        Path(args.out).write_text(s) if args.out else print(s)
    if args.cmd == "status":
        from .status import main as status
        status()
    if args.cmd == "natural":
        from .natural import main as natural
        natural()
    if args.cmd == "compare":
        from .compare import main as compare
        compare(args.baseline)
    if args.cmd == "app":
        from .app import main as app
        app()
    if args.cmd == "human":
        from .human import main as human
        human()
    if args.cmd == "api":
        import uvicorn
        uvicorn.run("cadence.api:app", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
