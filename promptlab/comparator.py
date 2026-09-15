"""Comparator for promptlab reports."""
import json
import os
import sys
from typing import Dict, List, Tuple, Any

def load_report(file_path: str) -> Dict[str, Any]:
    """Load JSON report from file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        sys.stderr.write(f"Report file not found: {file_path}\n")
        sys.exit(1)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"Invalid JSON in report file: {e}\n")
        sys.exit(1)
    except OSError as e:
        sys.stderr.write(f"Cannot read report file: {e}\n")
        sys.exit(4)

def compare_reports(baseline: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare two reports and return comparison dict.
    Validates that they are comparable (same suite, prompt_hash, model settings, runs).
    """
    # Basic validation
    if baseline.get("suite_name") != candidate.get("suite_name"):
        sys.stderr.write("Reports are from different suites\n")
        sys.exit(1)
    if baseline.get("prompt_hash") != candidate.get("prompt_hash"):
        sys.stderr.write("Reports have different prompt hashes\n")
        sys.exit(1)
    # Model settings
    base_model = baseline.get("model", {})
    cand_model = candidate.get("model", {})
    if base_model.get("temperature") != cand_model.get("temperature"):
        sys.stderr.write("Reports have different temperature settings\n")
        sys.exit(1)
    if base_model.get("max_tokens") != cand_model.get("max_tokens"):
        sys.stderr.write("Reports have different max_tokens settings\n")
        sys.exit(1)
    # Runs
    if baseline.get("runs") != candidate.get("runs"):
        sys.stderr.write("Reports have different runs settings\n")
        sys.exit(1)

    # Compute pass_rate_change: average pass rate across cases
    base_cases = baseline.get("cases", [])
    cand_cases = candidate.get("cases", [])
    if len(base_cases) != len(cand_cases):
        sys.stderr.write("Reports have different number of cases\n")
        sys.exit(1)
    # Map case id to case for alignment
    base_by_id = {c.get("id"): c for c in base_cases}
    cand_by_id = {c.get("id"): c for c in cand_cases}
    # Ensure same ids
    if set(base_by_id.keys()) != set(cand_by_id.keys()):
        sys.stderr.write("Reports have different case IDs\n")
        sys.exit(1)

    # Compute average pass rate
    base_pass_rates = [c.get("pass_rate", 0.0) for c in base_cases]
    cand_pass_rates = [c.get("pass_rate", 0.0) for c in cand_cases]
    base_avg = sum(base_pass_rates) / len(base_pass_rates) if base_pass_rates else 0.0
    cand_avg = sum(cand_pass_rates) / len(cand_pass_rates) if cand_pass_rates else 0.0
    pass_rate_change = cand_avg - base_avg

    # Compute percentage changes for totals
    base_totals = baseline.get("totals", {})
    cand_totals = candidate.get("totals", {})
    def pct_change(old, new):
        if old == 0:
            return 0.0 if new == 0 else float('inf')
        return ((new - old) / old) * 100.0
    tokens_in_change_pct = pct_change(base_totals.get("tokens_in", 0), cand_totals.get("tokens_in", 0))
    tokens_out_change_pct = pct_change(base_totals.get("tokens_out", 0), cand_totals.get("tokens_out", 0))
    wall_ms_change_pct = pct_change(base_totals.get("wall_ms", 0), cand_totals.get("wall_ms", 0))

    # Classify cases
    regressions = []
    improvements = []
    unchanged = []
    for case_id in base_by_id:
        base_case = base_by_id[case_id]
        cand_case = cand_by_id[case_id]
        base_pr = base_case.get("pass_rate", 0.0)
        cand_pr = cand_case.get("pass_rate", 0.0)
        if cand_pr < base_pr - 1e-9:  # small epsilon for floating point
            regressions.append(case_id)
        elif cand_pr > base_pr + 1e-9:
            improvements.append(case_id)
        else:
            unchanged.append(case_id)

    # Build comparison dict
    comparison = {
        "baseline_hash": baseline.get("prompt_hash", ""),
        "candidate_hash": candidate.get("prompt_hash", ""),
        "delta": {
            "pass_rate_change": pass_rate_change,
            "tokens_in_change_pct": tokens_in_change_pct,
            "tokens_out_change_pct": tokens_out_change_pct,
            "wall_ms_change_pct": wall_ms_change_pct,
        },
        "regressions": regressions,
        "improvements": improvements,
        "unchanged": unchanged,
    }
    return comparison

def generate_comparison_json(comparison: Dict[str, Any]) -> str:
    """Generate JSON string for comparison."""
    return json.dumps(comparison, indent=2)

def generate_comparison_human(comparison: Dict[str, Any]) -> str:
    """Generate human-readable summary for comparison."""
    lines = []
    lines.append(f"Baseline hash: {comparison.get('baseline_hash')}")
    lines.append(f"Candidate hash: {comparison.get('candidate_hash')}")
    delta = comparison.get("delta", {})
    lines.append(f"Pass rate change: {delta.get('pass_rate_change', 0.0):+.2f}")
    lines.append(f"Tokens in change: {delta.get('tokens_in_change_pct', 0.0):+.2f}%")
    lines.append(f"Tokens out change: {delta.get('tokens_out_change_pct', 0.0):+.2f}%")
    lines.append(f"Wall time change: {delta.get('wall_ms_change_pct', 0.0):+.2f}%")
    regressions = comparison.get("regressions", [])
    improvements = comparison.get("improvements", [])
    unchanged = comparison.get("unchanged", [])
    lines.append(f"Regressions: {len(regressions)}")
    lines.append(f"Improvements: {len(improvements)}")
    lines.append(f"Unchanged: {len(unchanged)}")
    if regressions:
        lines.append("Regression cases: " + ", ".join(regressions[:5]) + ("..." if len(regressions) > 5 else ""))
    if improvements:
        lines.append("Improvement cases: " + ", ".join(improvements[:5]) + ("..." if len(improvements) > 5 else ""))
    return "\n".join(lines)