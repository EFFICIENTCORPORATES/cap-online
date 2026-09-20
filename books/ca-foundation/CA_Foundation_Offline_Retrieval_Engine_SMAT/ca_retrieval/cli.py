from __future__ import annotations
import argparse
import json
from pathlib import Path
from .engine import RetrievalEngine
from .query import PRESETS, spec_from_preset


def default_data_folder() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "parsed_md"


def build_parser():
    p = argparse.ArgumentParser(description="Offline deterministic retrieval from CA Foundation Beautified Markdown files.")
    p.add_argument("--data", default=str(default_data_folder()), help="Folder containing parsed/beautified Markdown files.")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--query", help='Deterministic text query, e.g. "Give me all MCQs from Chapter 3".')
    group.add_argument("--preset", choices=sorted(list(PRESETS) + ["everything"]), help="Built-in retrieval preset.")
    p.add_argument("--paper", type=int)
    p.add_argument("--module", type=int)
    p.add_argument("--chapter", type=int)
    p.add_argument("--unit", type=int)
    p.add_argument("--topic")
    p.add_argument("--with-answers", action="store_true", help="Join available paired answers/solutions using pair_key.")
    p.add_argument("--output", "-o", help="Output Markdown path. If omitted, prints to screen.")
    p.add_argument("--keep-internal-comments", action="store_true")
    p.add_argument("--stats", action="store_true", help="Show corpus statistics.")
    p.add_argument("--validate-data", action="store_true", help="Validate loaded metadata/block integrity.")
    p.add_argument("--write-index", help="Write a compact JSON metadata index.")
    p.add_argument("--interactive", action="store_true", help="Open terminal interactive mode.")
    return p


def apply_filters(spec, args):
    for name in ["paper", "module", "chapter", "unit", "topic"]:
        v = getattr(args, name)
        if v is not None:
            setattr(spec, name, v)
    if args.with_answers:
        spec.include_answers = True
    return spec


def interactive(engine: RetrievalEngine):
    print("\nCA Foundation Offline Retrieval Engine")
    print("Type a request in normal simple English, or 'exit'.")
    print("Examples:")
    print("  Give me all MCQs")
    print("  Give me all MCQs from Chapter 3 with answers")
    print("  Give me only Illustration questions from Chapter 2 without solutions")
    print("  Give me everything from Unit 4")
    print("  Give me all questions from Paper 1 Module 2")
    while True:
        try:
            q = input("\nQuery> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if q.lower() in {"exit", "quit", "q"}:
            return
        if not q:
            continue
        spec, blocks = engine.query_text(q)
        rc=engine.result_counts(blocks,spec)
        print(f"Matched {rc['source_items']} source items ({rc['returned_blocks']} returned blocks). Output filename (blank = preview):")
        out = input("Output> ").strip()
        md = engine.compile(spec)
        if out:
            Path(out).write_text(md, encoding="utf-8")
            print(f"Saved: {Path(out).resolve()}")
        else:
            print("\n" + md[:6000])
            if len(md) > 6000:
                print("\n...[preview truncated; save to a file for full output]...")


def main(argv=None):
    args = build_parser().parse_args(argv)
    engine = RetrievalEngine(args.data)

    if args.stats:
        print(json.dumps(engine.stats(), ensure_ascii=False, indent=2))
        return 0
    if args.validate_data:
        report = engine.validate()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["ok"] else 2
    if args.write_index:
        p = engine.write_index(args.write_index)
        print(f"Index written: {p.resolve()}")
        return 0
    if args.interactive or (not args.query and not args.preset):
        interactive(engine)
        return 0

    if args.query:
        spec = apply_filters(__import__("ca_retrieval.query", fromlist=["parse_natural_query"]).parse_natural_query(args.query), args)
    else:
        spec = apply_filters(spec_from_preset(args.preset), args)
    md = engine.compile(spec, keep_internal_comments=args.keep_internal_comments)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        blocks=engine.query(spec); rc=engine.result_counts(blocks,spec)
        print(f"Saved {rc['source_items']} source items ({rc['returned_blocks']} returned blocks) to: {out.resolve()}")
    else:
        print(md)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
