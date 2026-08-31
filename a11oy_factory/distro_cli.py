"""CLI wiring for the A11oy distribution compiler."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .distribution import (
    FactoryError,
    build_plan,
    catalog_summary,
    generate_provenance,
    generate_spdx,
    materialize_artifacts,
    read_json,
    resolve_distribution,
    validate_catalog,
    validate_profile,
    verify_distribution,
    write_bundle,
)


def add_distribution_parser(subparsers: Any) -> None:
    distro = subparsers.add_parser(
        "distro",
        help="Compile an integrity-locked AI distribution bundle.",
    )
    commands = distro.add_subparsers(dest="distro_cmd", required=True)

    validate = commands.add_parser("validate", help="Validate a catalog and profile.")
    _catalog_profile_args(validate)

    summary = commands.add_parser("summary", help="Summarize a catalog.")
    summary.add_argument("--catalog", default="factory/catalog.json")

    resolve = commands.add_parser("resolve", help="Resolve a profile into a deterministic lock.")
    _catalog_profile_args(resolve)
    resolve.add_argument("--out", help="Optional lock output path.")

    plan = commands.add_parser("plan", help="Generate a non-executing build plan.")
    _catalog_profile_args(plan)
    plan.add_argument("--out", help="Optional plan output path.")

    sbom = commands.add_parser("sbom", help="Generate an SPDX 2.3 SBOM.")
    _catalog_profile_args(sbom)
    sbom.add_argument("--out", help="Optional SBOM output path.")

    attest = commands.add_parser("attest", help="Generate an in-toto/SLSA provenance statement.")
    _catalog_profile_args(attest)
    attest.add_argument("--out", help="Optional provenance output path.")

    bundle = commands.add_parser("bundle", help="Write lock, plan, SBOM, provenance, and verification.")
    _catalog_profile_args(bundle)
    bundle.add_argument("--out-dir", default="dist/factory")

    verify = commands.add_parser("verify", help="Re-resolve and verify a factory bundle.")
    _catalog_profile_args(verify)
    verify.add_argument("--lock", required=True)
    verify.add_argument("--sbom")
    verify.add_argument("--provenance")

    materialize = commands.add_parser(
        "materialize",
        help="Explicitly download digest-pinned artifacts without executing them.",
    )
    materialize.add_argument("--lock", required=True)
    materialize.add_argument("--out-dir", default="dist/artifacts")
    materialize.add_argument("--component", action="append", default=[])
    materialize.add_argument("--timeout", type=float, default=60.0)


def run_distribution_command(args: argparse.Namespace) -> int:
    try:
        command = args.distro_cmd
        if command == "summary":
            result = catalog_summary(read_json(args.catalog))
        elif command == "materialize":
            result = materialize_artifacts(
                read_json(args.lock),
                args.out_dir,
                component_ids=args.component,
                timeout_s=args.timeout,
            )
        else:
            catalog = read_json(args.catalog)
            profile = read_json(args.profile)
            if command == "validate":
                validate_catalog(catalog)
                validate_profile(profile, catalog)
                result = {
                    "ok": True,
                    "decision": "ALLOW",
                    "catalog": args.catalog,
                    "profile": args.profile,
                    "summary": catalog_summary(catalog),
                }
            elif command == "resolve":
                result = resolve_distribution(catalog, profile)
                _maybe_write(args.out, result)
            elif command == "plan":
                result = build_plan(resolve_distribution(catalog, profile))
                _maybe_write(args.out, result)
            elif command == "sbom":
                result = generate_spdx(resolve_distribution(catalog, profile))
                _maybe_write(args.out, result)
            elif command == "attest":
                result = generate_provenance(resolve_distribution(catalog, profile))
                _maybe_write(args.out, result)
            elif command == "bundle":
                result = write_bundle(catalog, profile, args.out_dir)
            elif command == "verify":
                lock = read_json(args.lock)
                sbom = read_json(args.sbom) if args.sbom else None
                provenance = read_json(args.provenance) if args.provenance else None
                result = verify_distribution(catalog, profile, lock, sbom=sbom, provenance=provenance)
            else:
                raise FactoryError("unknown_command", f"Unknown distro command: {command}")
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 0 if result.get("ok", result.get("decision") != "BLOCKED") else 2
    except FactoryError as exc:
        print(json.dumps(exc.as_dict(), indent=2, sort_keys=True, ensure_ascii=False))
        return 2


def _catalog_profile_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--catalog", default="factory/catalog.json")
    parser.add_argument("--profile", default="factory/profiles/vllm-cpu-amd64.json")


def _maybe_write(path: str | None, document: dict[str, Any]) -> None:
    if not path:
        return
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
