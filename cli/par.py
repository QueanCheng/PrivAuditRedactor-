"""
Command-line interface entry points for batch processing and report export.

This script intentionally mirrors common UNIX CLI conventions to make usage
familiar to sysadmins.
"""

# Human note: example invocation in docs/README.md


import argparse, sys
from pathlib import Path
from par_core.service import process_file
from par_core.db import export_chain_html, export_chain_html_with_stats

def cmd_redact(args):
    p = Path(args.input)
    out = Path(args.output)
    out.mkdir(exist_ok=True, parents=True)
    if p.is_file():
        res = process_file(p, user=args.user, strategy=args.strategy)
        (out / p.name).write_text(res["redacted"], encoding="utf-8")
        print(f"[OK] {p} -> {out/p.name} findings={len(res['findings'])} op_id={res['op_id']}")
    else:
        total = 0
        for f in p.glob("**/*"):
            if f.is_file() and f.suffix.lower() in {".txt",".md",".csv",".log",".json"}:
                res = process_file(f, user=args.user, strategy=args.strategy)
                (out / f.name).write_text(res["redacted"], encoding="utf-8")
                total += 1
        print(f"[BATCH] processed={total} -> {out}")

def cmd_report(args):
    dest = Path(args.output)
    dest.parent.mkdir(exist_ok=True, parents=True)
    export_chain_html(dest)
    print(f"[REPORT] {dest}")

def build_parser():
    ap = argparse.ArgumentParser(prog="par", description="PrivAuditRedactor CLI")
    sp = ap.add_subparsers()

    ap_red = sp.add_parser("redact", help="Redact a file or a folder")
    ap_red.add_argument("--input", required=True)
    ap_red.add_argument("--output", required=True)
    ap_red.add_argument("--user", default="cli")
    ap_red.add_argument("--strategy", default="smart", choices=["smart","full"])
    ap_red.set_defaults(func=cmd_redact)

    ap_rep = sp.add_parser("report", help="Export audit chain HTML")
    ap_rep.add_argument("--output", required=True)
    ap_rep.set_defaults(func=cmd_report)
    ap_rep_stat = sp.add_parser('report-stats', help='Export audit chain HTML with stats')
    ap_rep_stat.add_argument('--output', required=True)
    ap_rep_stat.set_defaults(func=lambda args: export_chain_html_with_stats(args.output))

    return ap

def main(argv=None):
    argv = argv or sys.argv[1:]
    ap = build_parser()
    args = ap.parse_args(argv)
    if hasattr(args, "func"):
        return args.func(args)
    else:
        ap.print_help()

if __name__ == "__main__":
    main()
