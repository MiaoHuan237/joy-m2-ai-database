"""Thin local entry point; no model calls or publication capability."""
import argparse
import json
from pathlib import Path
from joy_m2.ingest.automation import run_cycle


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    result = run_cycle(args.config, args.repo)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result.get('failed') else 0


if __name__ == '__main__':
    raise SystemExit(main())
