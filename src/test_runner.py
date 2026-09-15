"""Test runner for executing suites and applying flaky policy."""
import json
import time
import sys
import os
from typing import Dict, List, Tuple, Any, Optional
from .model_invoker import invoke_model
from .assertion_engine import _dispatch_assertion
from .suite_parser import load_suite

def run_suite(
    suite: Dict[str, Any],
    runs_override: Optional[int] = None,
    temperature_override: Optional[float] = None,
    max_tokens_override: Optional[int] = None,
    model_binary: str = "stubmodel.py",
) -> Dict[str, Any]:
    """
    Execute test suite and return results ready for reporting.
    """
    # Determine runs
    runs = runs_override if runs_override is not None else suite["runs"]
    if runs < 1:
        raise ValueError("runs must be >=1")

    # Determine model parameters
    model_temp = suite["model"]["temperature"]
    model_max_toks = suite["model"]["max_tokens"]
    if temperature_override is not None:
        model_temp = temperature_override
    if max_tokens_override is not None:
        model_max_toks = max_tokens_override

    prompt_file = suite["prompt_file"]
    # Read prompt content
    try:
        with open(prompt_file, "r", encoding="utf-8") as f:
            prompt_content = f.read()
    except OSError as e:
        raise RuntimeError(f"Cannot read prompt file: {e}")
    # Compute prompt hash (first 12 hex chars of SHA-256)
    import hashlib
    prompt_hash = hashlib.sha256(prompt_content.encode('utf-8')).hexdigest()[:12]

    # Per-case storage
    case_results = []
    total_cases = len(suite["cases"])
    total_passed = 0
    total_failed = 0
    total_flaky = 0
    total_tokens_in = 0
    total_tokens_out = 0
    total_wall_ms = 0

    for case in suite["cases"]:
        case_id = case["id"]
        case_input = case["input"]  # resolved string
        assertions = case["assert"]

        # Per-run tracking
        run_passed = [False] * runs  # whether all assertions passed in this run
        # Per-assertion counts across runs
        assertion_pass_counts = {a["type"]: 0 for a in assertions}
        assertion_fail_counts = {a["type"]: 0 for a in assertions}
        # For first failure details (across all runs)
        first_failure = None
        first_failure_run_idx = None
        # Accumulate tokens and wall time
        case_tokens_in_sum = 0
        case_tokens_out_sum = 0
        case_wall_ms_sum = 0

        for run_idx in range(runs):
            # Invoke model
            start = time.time()
            exit_code, stdout, stderr = invoke_model(
                binary=model_binary,
                prompt_file=prompt_file,
                input_content=case_input,
                temperature=model_temp,
                max_tokens=model_max_toks,
            )
            end = time.time()
            wall_ms = int((end - start) * 1000)

            # Parse model output JSON (if any) for assertions
            model_output = {"output": stdout.strip(), "tokens_in": 0, "tokens_out": 0, "finish": "unknown", "latency_ms": wall_ms}
            stripped = stdout.strip()
            if stripped.startswith("```json") and stripped.endswith("```"):
                lines = stripped.splitlines()
                if len(lines) >= 3:
                    stripped = "\n".join(lines[1:-1])
                else:
                    stripped = stripped[7:-3]
            stripped = stripped.strip()
            if stripped:
                try:
                    parsed = json.loads(stripped)
                    model_output.update(parsed)
                except json.JSONDecodeError:
                    pass

            tokens_in = model_output.get("tokens_in", 0)
            tokens_out = model_output.get("tokens_out", 0)
            # finish from model_output
            finish = model_output.get("finish", "unknown")
            case_tokens_in_sum += tokens_in
            case_tokens_out_sum += tokens_out
            case_wall_ms_sum += wall_ms

            # Evaluate assertions for this run
            run_all_passed = True
            for config in assertions:
                passed, _, _ = _dispatch_assertion(model_output, config)
                if not passed:
                    run_all_passed = False
                    # Update per-assertion fail count
                    a_type = config.get("type")
                    assertion_fail_counts[a_type] = assertion_fail_counts.get(a_type, 0) + 1
                    # Capture first failure if not yet set
                    if first_failure is None:
                        # Determine expected
                        expected = None
                        if "value" in config:
                            expected = config["value"]
                        elif "pattern" in config:
                            expected = config["pattern"]
                        elif "field" in config:
                            expected = config["field"]
                        elif "subset" in config:
                            expected = config["subset"]
                        elif "assertions" in config:
                            expected = config["assertions"]
                        else:
                            expected = None
                        first_failure = {
                            "assertion": config,
                            "expected": expected,
                            "actual": model_output.get("output", "")[:100],
                            "measured_value": None,  # we could compute but skip for now
                            "run_index": run_idx,
                        }
                        # For composite assertions, we could enhance later
                else:
                    # Update per-assertion pass count
                    a_type = config.get("type")
                    assertion_pass_counts[a_type] = assertion_pass_counts.get(a_type, 0) + 1
            if run_all_passed:
                run_passed[run_idx] = True

        # After all runs, compute case status
        passed_runs = sum(run_passed)
        pass_rate = passed_runs / runs if runs > 0 else 0.0
        if pass_rate == 1.0:
            case_status = "pass"
            total_passed += 1
        elif pass_rate == 0.0:
            case_status = "fail"
            total_failed += 1
        else:
            case_status = "flaky"
            total_flaky += 1

        # Compute assertions summary for reporting
        assertions_summary = []
        for config in assertions:
            a_type = config.get("type")
            passed = assertion_pass_counts.get(a_type, 0)
            failed = assertion_fail_counts.get(a_type, 0)
            assertions_summary.append({
                "type": a_type,
                "passed": passed,
                "failed": failed,
            })

        # Compute average tokens_out per run for this case
        tokens_out_avg = case_tokens_out_sum / runs if runs > 0 else 0

        case_results.append({
            "id": case_id,
            "status": case_status,
            "pass_rate": pass_rate,
            "tokens_out_avg": tokens_out_avg,
            "assertions": assertions_summary,
            "failures": [first_failure] if first_failure is not None else [],
        })

        # Update totals
        total_tokens_in += case_tokens_in_sum
        total_tokens_out += case_tokens_out_sum
        total_wall_ms += case_wall_ms_sum

    # Build final results
    results = {
        "suite_name": suite.get("name", ""),
        "prompt_file": prompt_file,
        "prompt_hash": prompt_hash,
        "runs": runs,
        "model": {"temperature": model_temp, "max_tokens": model_max_toks},
        "totals": {
            "cases": total_cases,
            "passed": total_passed,
            "failed": total_failed,
            "flaky": total_flaky,
            "tokens_in": total_tokens_in,
            "tokens_out": total_tokens_out,
            "wall_ms": total_wall_ms,
        },
        "cases": case_results,
    }
    return results