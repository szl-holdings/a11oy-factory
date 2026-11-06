from __future__ import annotations

import argparse
import json

from .compiler import compile_cell
from .distribution_common import FactoryError
from .distro_cli import add_distribution_parser, run_distribution_command
from .jobs import search_jobs
from .organs import act, roadmap


def _act_payload(raw: str) -> dict:
    """Parse ``act --payload``; malformed or non-object input fails closed.

    The payload digest is recorded in the act receipt, so silently replacing
    bad input with ``{}`` would receipt something the caller never sent.
    """
    try:
        payload = json.loads(raw or "{}")
    except json.JSONDecodeError as exc:
        raise FactoryError(
            "invalid_json",
            "--payload must be a JSON object.",
            details={"line": exc.lineno, "column": exc.colno, "message": exc.msg},
        ) from exc
    if not isinstance(payload, dict):
        raise FactoryError(
            "invalid_payload",
            "--payload must be a JSON object.",
            details={"type": type(payload).__name__},
        )
    return payload


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
            payload = _act_payload(args.payload)
        except FactoryError as exc:
            print(json.dumps(exc.as_dict(), indent=2, sort_keys=True))
            return 2
        rec = act(args.cell, payload)
        print(json.dumps(rec, indent=2))
        return 0 if rec.get("ok") else 2

    rec = compile_cell(args.cell, signal=args.signal)
    print(json.dumps(rec.as_dict(), indent=2))
    return 0 if rec.decision == "ALLOW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
