"""Doctor command for environment and installation validation."""
import sys
import os
import subprocess
import shutil

def doctor() -> int:
    """
    Validate environment and installation.
    Returns exit code (0 for success, non-zero for failure).
    """
    checks = []
    # 1. Python version
    try:
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 10):
            checks.append(("Python version >=3.10 required", False, f"Found {version.major}.{version.minor}"))
        else:
            checks.append(("Python version >=3.10", True, f"{version.major}.{version.minor}.{version.micro}"))
    except Exception as e:
        checks.append(("Python version check", False, str(e)))

    # 2. Model binary presence and executability
    # We'll check for stubmodel.py in the current directory or PATH
    model_binary = "stubmodel.py"
    # Look for it in the same directory as this script or in PATH
    found = False
    # Check current working directory
    if os.path.isfile(model_binary) and os.access(model_binary, os.X_OK):
        found = True
    else:
        # Check in PATH
        if shutil.which(model_binary):
            found = True
    if not found:
        # Maybe it's a python script that doesn't need executable bit; we'll check readability
        if os.path.isfile(model_binary) and os.access(model_binary, os.R_OK):
            found = True
    if found:
        checks.append(("Model binary present and readable", True, model_binary))
    else:
        checks.append(("Model binary present and readable", False, model_binary))

    # 3. Suite discoverability: check if we can find any suite files in suites/ directory
    suite_dir = os.path.join(os.path.dirname(__file__), "..", "suites")
    suite_dir = os.path.abspath(suite_dir)
    if os.path.isdir(suite_dir):
        # Check for at least one .json file
        has_suite = False
        for entry in os.listdir(suite_dir):
            if entry.endswith(".json"):
                has_suite = True
                break
        if has_suite:
            checks.append(("Suite directory accessible with JSON suites", True, suite_dir))
        else:
            checks.append(("Suite directory accessible with JSON suites", False, f"No .json files found in {suite_dir}"))
    else:
        checks.append(("Suite directory accessible with JSON suites", False, f"Directory not found: {suite_dir}"))

    # 4. Assertion type registry: ensure we can import assertion_engine and known types are present
    try:
        # Add src to path if needed
        sys.path.insert(0, os.path.dirname(__file__))
        from .assertion_engine import _ASSERTION_FUNCS
        expected_types = {"contains", "not_contains", "equals", "matches", "json_valid", "json_field_equals", "max_tokens", "finish_is", "all_of", "any_of", "json_subset"}
        missing = expected_types - set(_ASSERTION_FUNCS.keys())
        if not missing:
            checks.append(("Assertion type registry complete", True, f"{len(_ASSERTION_FUNCS)} types"))
        else:
            checks.append(("Assertion type registry complete", False, f"Missing types: {missing}"))
    except Exception as e:
        checks.append(("Assertion type registry complete", False, f"Import error: {e}"))

    # 5. Test runner import
    try:
        from .test_runner import run_suite
        checks.append(("Test runner importable", True, ""))
    except Exception as e:
        checks.append(("Test runner importable", False, str(e)))

    # 6. Reporter import
    try:
        from .reporter import generate_json_report, generate_human_report
        checks.append(("Reporter importable", True, ""))
    except Exception as e:
        checks.append(("Reporter importable", False, str(e)))

    # 7. Comparator import
    try:
        from .comparator import load_report, compare_reports
        checks.append(("Comparator importable", True, ""))
    except Exception as e:
        checks.append(("Comparator importable", False, str(e)))

    # Output results
    all_passed = True
    for name, ok, detail in checks:
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_passed = False
        sys.stderr.write(f"[{status}] {name}")
        if detail:
            sys.stderr.write(f" - {detail}")
        sys.stderr.write("\n")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(doctor())