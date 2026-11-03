"""Public ServiceCraft command line interface."""

import argparse
import json
import subprocess
from pathlib import Path

from . import __version__
from .evaluator import evaluate
from .batch import Profile, run_batch


def main(argv=None):
    parser = argparse.ArgumentParser(description="ServiceCraft empirical Dagster evaluation")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("eval", help="Evaluate a generated Dagster submission")
    command.add_argument("candidate", type=Path)
    command.add_argument("--inputs", required=True, type=Path)
    command.add_argument("--spec", required=True, type=Path)
    command.add_argument("--report-dir", required=True, type=Path)
    command.add_argument("--profile", type=Path, help="Evaluator-owned runtime profile JSON")
    command.add_argument(
        "--metadata",
        type=json.loads,
        default={},
        help="JSON object with method, model, track, repetition, attempt, etc.",
    )
    batch = commands.add_parser(
        "batch", help="Run a frozen experiment manifest with trusted controls"
    )
    batch.add_argument("manifest", type=Path)
    batch.add_argument("--output", required=True, type=Path)
    batch.add_argument("--resume", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "batch":
        try:
            result = run_batch(args.manifest, args.output, resume=args.resume)
        except (ValueError, OSError, subprocess.SubprocessError) as exc:
            parser.exit(2, f"Batch setup error: {exc}\n")
        print(json.dumps(result, indent=2))
        return (
            2
            if result["unavailable"]
            else 0
            if result["complete_successes"] == result["scheduled"]
            else 1
        )
    if not isinstance(args.metadata, dict):
        parser.error("--metadata must be a JSON object")
    try:
        options = (
            {"runtime_profile": Profile.model_validate_json(args.profile.read_text()).model_dump()}
            if args.profile
            else {}
        )
        result = evaluate(
            args.candidate, args.inputs, args.spec, args.report_dir, args.metadata, **options
        )
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Evaluation setup error: {exc}\n")
    print(json.dumps(result, indent=2))
    success = result["scores"]["complete_success"]
    return 0 if success == 1 else 2 if success is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
