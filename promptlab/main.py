#!/usr/bin/env python3
"""
promptlab command-line interface.
"""
import argparse
import json
import sys
import os
from promptlab import doctor
from promptlab import test_runner
from promptlab import reporter
from promptlab import comparator

def _handle_run(args):
    """Handle promptlab run command."""
    # Load suite (will validate and exit on error)
    suite = test_runner.load_suite(args.suite) if hasattr(test_runner, 'load_suite') else None
    if suite is None:
        # Fallback: we'll import load_suite from test_runner
        from .test_runner import load_suite
        suite = load_suite(args.suite)
    # Determine overrides
    runs_override = args.runs if args.runs is not None else None
    temp_override = args.temperature if args.temperature is not None else None
    max_toks_override = args.max_tokens if args.max_tokens is not None else None
    # Run suite
    results = test_runner.run_suite(
        suite,
        runs_override=runs_override,
        temperature_override=temp_override,
        max_tokens_override=max_toks_override,
        model_binary=getattr(args, 'model_binary', 'stubmodel.py'),
    )
    # Generate reports
    json_report = reporter.generate_json_report(results)
    human_report = reporter.generate_human_report(results)
    # Stream routing
    if args.out:
        # Write JSON to file
        try:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(json_report)
        except OSError as e:
            sys.stderr.write(f"Cannot write JSON report to {args.out}: {e}\n")
            sys.exit(1)
        # Human report goes to stderr if --requested
        if args.report:
            sys.stderr.write(human_report + "\n")
    else:
        # No --out: JSON to stdout
        if args.report:
            # Human report to stderr, JSON to stdout
            sys.stderr.write(human_report + "\n")
            sys.stdout.write(json_report + "\n")
        else:
            # Only JSON to stdout
            sys.stdout.write(json_report + "\n")
    # Determine exit code based on case statuses
    totals = results.get("totals", {})
    failed = totals.get("failed", 0)
    flaky = totals.get("flaky", 0)
    if failed > 0 or flaky > 0:
        # Exit code 2: one or more cases failed or flaky
        sys.exit(2)
    else:
        sys.exit(0)

def _handle_compare(args):
    """Handle promptlab compare command."""
    # Load reports
    baseline = comparator.load_report(args.baseline)
    candidate = comparator.load_report(args.candidate)
    # Compare
    comparison = comparator.compare_reports(baseline, candidate)
    # Generate output
    json_out = comparator.generate_comparison_json(comparison)
    human_out = comparator.generate_comparison_human(comparison)
    # Stream routing similar to run
    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(json_out)
        except OSError as e:
            sys.stderr.write(f"Cannot write comparison JSON to {args.out}: {e}\n")
            sys.exit(1)
        if args.report:
            sys.stderr.write(human_out + "\n")
    else:
        if args.report:
            sys.stderr.write(human_out + "\n")
            sys.stdout.write(json_out + "\n")
        else:
            sys.stdout.write(json_out + "\n")
    # Compare command always exits with 0 if comparison completed (unless error)
    sys.exit(0)

def _handle_doctor(args):
    """Handle promptlab doctor command."""
    exit_code = doctor.doctor()
    sys.exit(exit_code)

def main():
    parser = argparse.ArgumentParser(
        prog="promptlab",
        description="Prompt evaluation and comparison tool",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s 0.1.0",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # run command
    run_parser = subparsers.add_parser("run", help="Run a test suite")
    run_parser.add_argument(
        "--suite",
        required=True,
        help="Path to suite JSON file",
    )
    run_parser.add_argument(
        "--runs",
        type=int,
        help="Number of runs per case (overrides suite runs)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        help="Sampling temperature (overrides suite temperature)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        help="Maximum tokens to generate (overrides suite max-tokens)",
    )
    run_parser.add_argument(
        "--out",
        metavar="FILE",
        help="Write JSON report to FILE (if omitted, JSON goes to stdout)",
    )
    run_parser.add_argument(
        "--report",
        action="store_true",
        help="Output human-readable summary (always goes to stderr)",
    )
    # Note: model binary could be made configurable; for now use default

    # compare command
    compare_parser = subparsers.add_parser("compare", help="Compare two test suite runs")
    compare_parser.add_argument(
        "--baseline",
        required=True,
        help="Path to baseline report JSON file",
    )
    compare_parser.add_argument(
        "--candidate",
        required=True,
        help="Path to candidate report JSON file",
    )
    compare_parser.add_argument(
        "--out",
        metavar="FILE",
        help="Write comparison JSON to FILE (if omitted, JSON goes to stdout)",
    )
    compare_parser.add_argument(
        "--report",
        action="store_true",
        help="Output human-readable summary (always goes to stderr)",
    )

    # doctor command
    subparsers.add_parser("doctor", help="Validate environment and installation")

    args = parser.parse_args()

    if args.command == "run":
        _handle_run(args)
    elif args.command == "compare":
        _handle_compare(args)
    elif args.command == "doctor":
        _handle_doctor(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()