from __future__ import annotations

import argparse
import json
from pathlib import Path

from .baseline import verify_baseline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="joy-m2")
    subparsers = parser.add_subparsers(dest="command", required=True)
    verify = subparsers.add_parser("verify-baseline", help="verify the protected V1.18 release")
    verify.add_argument(
        "release_dir",
        nargs="?",
        type=Path,
        default=Path("releases/V1.18"),
        help="baseline directory (default: releases/V1.18)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "verify-baseline":
        result = verify_baseline(args.release_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if result["status"] == "PASS" else 1
    raise AssertionError(f"unhandled command: {args.command}")
