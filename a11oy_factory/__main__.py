from __future__ import annotations

import argparse
import json

from .compiler import compile_cell
from .distro_cli import add_distribution_parser, run_distribution_command
from .jobs import search_jobs
from .organs import act, roadmap


def main() -> int:
    parser = argparse.ArgumentParser(prog="a11oy-factory")
    sub = parser.add_subparsers(dest="cmd", required=True)

    compile_parser = sub.add_parser(
        "compile",
        help="Compile a decision cell (Lyte admitted; N1–N27 STARTED, BLOCKED).",
    )
    compile_parser.add_argument("--cell", required=True)
    compile_parser.add_argument("--signal", default="")

    search_parser = sub.add_parser("search", help="Search cited jobs versus SZL organs.")
    search_parser.add_argument(
        "--q",
        default="",
        help="Catalog query (vllm, mcp, spiffe, nemo, playwright, cedar, ...).",
    )

    sub.add_parser("roadmap", help="List STARTED fail-closed organs (not LIVE).")

    act_parser = sub.add_parser("act", help="Run a fail-closed organ. Frontiers halt.")
    act_parser.add_argument("--cell", required=True)
    act_parser.add_argument("--payload", default="{}", help="JSON payload")

    add_distribution_parser(sub)
    args = parser.parse_args()

    if args.cmd == "distro":
        return run_distribution_command(args)
    if args.cmd == "search":
        print(json.dumps(search_jobs(args.q), indent=2))
        return 0
    if args.cmd == "roadmap":
        print(json.dumps(roadmap(), indent=2))
        return 0
    if args.cmd == "act":
        try:
            payload = json.loads(args.payload or "{}")
        except json.JSONDecodeError:
            payload = {}
        rec = act(args.cell, payload if isinstance(payload, dict) else {})
        print(json.dumps(rec, indent=2))
        return 0 if rec.get("ok") else 2

    rec = compile_cell(args.cell, signal=args.signal)
    print(json.dumps(rec.as_dict(), indent=2))
    return 0 if rec.decision == "ALLOW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
