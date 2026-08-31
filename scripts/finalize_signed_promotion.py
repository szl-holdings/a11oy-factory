#!/usr/bin/env python3
"""Finalize the stable-channel verdict after keyless signature verification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from a11oy_factory.assurance import AssuranceError
from a11oy_factory.signed_promotion import (
    finalize_stable_verdict,
    verify_signed_promotion,
)


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssuranceError("INVALID_JSON", f"{path} must contain a JSON object")
    return value


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--initial-stable-verdict", type=Path, required=True)
    parser.add_argument("--subject", type=Path, required=True)
    parser.add_argument("--sigstore-proof", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    verdict = finalize_stable_verdict(
        _read(args.initial_stable_verdict),
        _read(args.subject),
        _read(args.sigstore_proof),
    )
    if not verify_signed_promotion(verdict):
        raise AssuranceError("SIGNED_VERDICT_INVALID", "Generated signed promotion digest is invalid")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(verdict, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(verdict, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssuranceError as exc:
        print(json.dumps(exc.as_dict(), indent=2, sort_keys=True))
        raise SystemExit(2)
