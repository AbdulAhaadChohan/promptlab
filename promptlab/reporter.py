"""Report generation for promptlab."""
import json
import sys
from typing import Dict, List, Any

def generate_json_report(results: Dict[str, Any]) -> str:
    """
    Generate JSON report string from test runner results.
    """
    # Build JSON structure as per spec
    report = {
        "suite": results.get("suite_name", ""),
        "prompt_file": results.get("prompt_file", ""),
        "prompt_hash": results.get("prompt_hash", ""),
        "runs": results.get("runs", 0),
        "model": results.get("model", {"temperature": 0.0, "max_tokens": 0}),
        "totals": results.get("totals", {
            "cases": 0,
            "passed": 0,
            "failed": 0,
            "flaky": 0,
            "tokens_in": 0,
            "tokens_out": 0,
            "wall_ms": 0,
        }),
        "cases": [],
    }
    for case in results.get("cases", []):
        case_report = {
            "id": case.get("id", ""),
            "status": case.get("status", "pass"),
            "pass_rate": case.get("pass_rate", 0.0),
            "tokens_out_avg": case.get("tokens_out_avg", 0.0),
            "assertions": [],
            "failures": case.get("failures", []),
        }
        for assertion in case.get("assertions", []):
            case_report["assertions"].append({
                "type": assertion.get("type", ""),
                "passed": assertion.get("passed", 0),
                "failed": assertion.get("failed", 0),
            })
        report["cases"].append(case_report)
    # Ensure JSON is serialized with no trailing spaces, but keep readability? Spec doesn't require pretty print; but examples are pretty-printed.
    # We'll output with indent=2 for readability, but spec may accept any valid JSON.
    # To match spec examples, we'll indent.
    return json.dumps(report, indent=2)

def generate_human_report(results: Dict[str, Any]) -> str:
    """
    Generate human-readable summary string.
    """
    suite_name = results.get("suite_name", "")
    total = results.get("totals", {})
    cases_total = total.get("cases", 0)
    passed = total.get("passed", 0)
    flaky = total.get("flaky", 0)
    failed = total.get("failed", 0)
    tokens_in = total.get("tokens_in", 0)
    tokens_out = total.get("tokens_out", 0)
    wall_ms = total.get("wall_ms", 0)
    # Format wall_ms to seconds with 2 decimal places
    wall_sec = wall_ms / 1000.0
    lines = []
    lines.append(f"Suite: {suite_name}")
    lines.append(f"Passed: {passed}/{cases_total} ({passed/cases_total*100 if cases_total else 0:.1f}%)")
    lines.append(f"Flaky: {flaky}/{cases_total} ({flaky/cases_total*100 if cases_total else 0:.1f}%)")
    lines.append(f"Failed: {failed}/{cases_total} ({failed/cases_total*100 if cases_total else 0:.1f}%)")
    lines.append(f"Tokens In: {tokens_in:,} | Tokens Out: {tokens_out:,} | Wall Time: {wall_sec:.2f}s")
    # Worst cases: sort cases by pass_rate ascending, take up to 3
    cases = results.get("cases", [])
    # Exclude passed cases? spec shows worst cases include passed? Actually they show cases with pass_rate < 1.0.
    # We'll take all cases, sort by pass_rate ascending, then take first 3.
    sorted_cases = sorted(cases, key=lambda c: c.get("pass_rate", 1.0))
    worst = sorted_cases[:3]
    if worst:
        lines.append("Worst Cases:")
        for c in worst:
            cid = c.get("id", "")
            pr = c.get("pass_rate", 0.0)
            # List assertion types that have failures? spec shows assertions: json_valid etc.
            # We'll gather assertion types where failed > 0
            assertion_parts = []
            for a in c.get("assertions", []):
                if a.get("failed", 0) > 0:
                    assertion_parts.append(a.get("type", ""))
            if not assertion_parts:
                # If no failed assertions but case is flaky or failed? maybe show all assertions?
                assertion_parts = [a.get("type", "") for a in c.get("assertions", [])]
            assertions_str = ", ".join(assertion_parts) if assertion_parts else ""
            lines.append(f"  {cid}: pass_rate={pr:.2f} (assertions: {assertions_str})")
    return "\n".join(lines)