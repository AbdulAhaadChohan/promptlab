#!/usr/bin/env python3
"""
promptlab command-line interface.
"""
import argparse
import sys
from . import __version__

def main():
    parser = argparse.ArgumentParser(
        prompt="promptlab",
        description="Prompt evaluation and comparison tool",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
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
        "--input",
        help="Path to input file (overrides suite input)",
    )
    run_parser.add_argument(
        "--runs",
        type=int,
        help="Number of runs per case (overrides suite runs)",
    )
    run_parser.add_argument(
        "--temperature",
        type=float,
        help="Sampling temperature (overrides suite temperature)",
    )
    run_parser.add_argument(
        "--max-tokens",
        type=int,
        help="Maximum tokens to generate (overrides suite max-tokens)",
    )
    run_parser.add_argument(
        "--out",
        choices=["json", "human"],
        default="human",
        help="Output format for machine-readable results",
    )
    run_parser.add_argument(
        "--report",
        choices=["json", "human"],
        default="human",
        help="Output format for human-readable report",
    )

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
        choices=["json", "human"],
        default="human",
        help="Output format for machine-readable comparison",
    )
    compare_parser.add_argument(
        "--report",
        choices=["json", "human"],
        default="human",
        help="Output format for human-readable comparison report",
    )

    # doctor command
    subparsers.add_parser("doctor", help="Validate environment and installation")

    args = parser.parse_args()

    if args.command == "run":
        print(f"Running suite: {args.suite}")
        # TODO: implement run command
        return 0
    elif args.command == "compare":
        print(f"Comparing baseline: {args.baseline} with candidate: {args.candidate}")
        # TODO: implement compare command
        return 0
    elif args.command == "doctor":
        print("Doctor check: environment looks good")
        # TODO: implement doctor command
        return 0
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())