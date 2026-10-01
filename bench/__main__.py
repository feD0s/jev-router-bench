import argparse
import json
import sys
from pathlib import Path
from .core import check_freeze, inputs, validate_dataset, write_json
from .estimate import estimate
from .report import generate_report
from .runner import dry_run, live_run


def main():
    parser = argparse.ArgumentParser(description="Jev/GPT router benchmark. Offline by default.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    for name in ("dry-run", "estimate", "live"):
        p = sub.add_parser(name)
        p.add_argument("--split", choices=("dev", "final"), default="dev")
        if name != "estimate":
            p.add_argument("--out", type=Path, required=True, help="New run directory; existing paths rejected")
        if name in ("estimate", "live"):
            p.add_argument("--runs", type=int, default=1)
        if name == "live":
            p.add_argument("--approve-spend-usd", type=float, required=True,
                           help="Only after explicit owner budget approval; includes unknown-usage errors")
            p.add_argument("--max-requests", type=int, default=None)
        if name == "estimate":
            p.add_argument("--save", type=Path)
    p = sub.add_parser("report")
    p.add_argument("--dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "validate":
            result = validate_dataset()
            inputs()
            check_freeze()
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif args.command == "estimate":
            check_freeze()
            result = estimate(args.split, args.runs)
            if args.save:
                write_json(args.save, result)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif args.command == "report":
            result = generate_report(args.dir)
            print(f"Report generated: {args.dir / 'results-summary.md'} ({result['mode']})")
        else:
            validate_dataset()
            directory = dry_run(args.split, args.out) if args.command == "dry-run" else live_run(
                args.split, args.out, args.runs, args.approve_spend_usd, args.max_requests)
            generate_report(directory)
            manifest = json.loads((directory / "manifest.json").read_text())
            print(f"Saved {manifest['mode']} evidence: {directory}; status={manifest['status']}")
            if manifest["status"] != "complete":
                return 1
    except (ValueError, OSError) as exc:
        # Only our own validation messages; never stringify HTTP/key exceptions.
        print(str(exc) if isinstance(exc, ValueError) else type(exc).__name__, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
