"""Suite JSON parsing and validation."""
import json
import os
import re
import sys
from typing import Any, Dict, List, Tuple, Optional

KNOWN_ASSERTION_TYPES = {
    "contains",
    "not_contains",
    "equals",
    "matches",
    "json_valid",
    "json_field_equals",
    "max_tokens",
    "finish_is",
    "all_of",
    "any_of",
    "json_subset",
}

def load_suite(suite_path: str) -> Dict[str, Any]:
    """
    Load and validate suite JSON file.
    Returns the suite dict with resolved input strings.
    Exits with appropriate error codes and messages to stderr on failure.
    """
    # Resolve suite path
    suite_path = os.path.abspath(suite_path)
    if not os.path.isfile(suite_path):
        sys.stderr.write(f"Suite file not found: {suite_path}\n")
        sys.exit(1)
    try:
        with open(suite_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"Invalid JSON in suite file: {e}\n")
        sys.exit(1)
    except OSError as e:
        sys.stderr.write(f"Cannot read suite file: {e}\n")
        sys.exit(4)  # unreadable file

    # Top-level structure
    if not isinstance(data, dict):
        sys.stderr.write("Suite file must be a JSON object\n")
        sys.exit(1)

    required_top = ["name", "prompt_file", "model", "runs", "cases"]
    for field in required_top:
        if field not in data:
            sys.stderr.write(f"Missing required field: {field}\n")
            sys.exit(1)

    # name: string
    if not isinstance(data["name"], str):
        sys.stderr.write("Field 'name' must be a string\n")
        sys.exit(1)

    # prompt_file: string, resolve relative to suite directory
    prompt_file = data["prompt_file"]
    if not isinstance(prompt_file, str):
        sys.stderr.write("Field 'prompt_file' must be a string\n")
        sys.exit(1)
    suite_dir = os.path.dirname(suite_path)
    prompt_path = os.path.join(suite_dir, prompt_file)
    if not os.path.isfile(prompt_path):
        sys.stderr.write(f"Prompt file not found: {prompt_path}\n")
        sys.exit(4)
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_content = f.read()
    except OSError as e:
        sys.stderr.write(f"Cannot read prompt file: {e}\n")
        sys.exit(4)
    data["prompt_file"] = prompt_path
    data["prompt_content"] = prompt_content  # store for later use

    # model: dict with temperature (float) and max_tokens (int)
    model = data["model"]
    if not isinstance(model, dict):
        sys.stderr.write("Field 'model' must be an object\n")
        sys.exit(1)
    if "temperature" not in model or "max_tokens" not in model:
        sys.stderr.write("Model must contain 'temperature' and 'max_tokens'\n")
        sys.exit(1)
    try:
        temp = float(model["temperature"])
        max_tok = int(model["max_tokens"])
    except (ValueError, TypeError):
        sys.stderr.write("Model temperature must be float, max_tokens must be integer\n")
        sys.exit(1)
    model["temperature"] = temp
    model["max_tokens"] = max_tok

    # runs: integer >=1
    runs = data["runs"]
    if not isinstance(runs, int):
        sys.stderr.write("Field 'runs' must be an integer\n")
        sys.exit(1)
    if runs < 1:
        sys.stderr.write("Field 'runs' must be >= 1\n")
        sys.exit(1)

    # cases: list
    cases = data["cases"]
    if not isinstance(cases, list):
        sys.stderr.write("Field 'cases' must be an array\n")
        sys.exit(1)

    # Validate each case
    seen_ids = set()
    for idx, case in enumerate(cases):
        if not isinstance(case, dict):
            sys.stderr.write(f"Case at index {idx} must be an object\n")
            sys.exit(1)
        # id
        if "id" not in case:
            sys.stderr.write(f"Case at index {idx} missing 'id'\n")
            sys.exit(1)
        case_id = case["id"]
        if not isinstance(case_id, str):
            sys.stderr.write(f"Case id at index {idx} must be a string\n")
            sys.exit(1)
        if case_id in seen_ids:
            sys.stderr.write(f"Duplicate case id: {case_id}\n")
            sys.exit(1)
        seen_ids.add(case_id)

        # input
        if "input" not in case:
            sys.stderr.write(f"Case '{case_id}' missing 'input'\n")
            sys.exit(1)
        inp = case["input"]
        resolved_input: str
        if isinstance(inp, str):
            resolved_input = inp
        elif isinstance(inp, dict) and "file" in inp:
            file_path = inp["file"]
            if not isinstance(file_path, str):
                sys.stderr.write(f"Case '{case_id}' input.file must be a string\n")
                sys.exit(1)
            input_path = os.path.join(suite_dir, file_path)
            if not os.path.isfile(input_path):
                sys.stderr.write(f"Input file not found for case '{case_id}': {input_path}\n")
                sys.exit(4)
            try:
                with open(input_path, "r", encoding="utf-8") as f:
                    content = f.read()
                # trim trailing newlines
                resolved_input = content.rstrip("\n\r")
            except OSError as e:
                sys.stderr.write(f"Cannot read input file for case '{case_id}': {e}\n")
                sys.exit(4)
        else:
            sys.stderr.write(f"Case '{case_id}' input must be string or {{'file': 'path'}}\n")
            sys.exit(1)
        case["input"] = resolved_input  # replace with resolved string

        # assert: list
        if "assert" not in case:
            sys.stderr.write(f"Case '{case_id}' missing 'assert'\n")
            sys.exit(1)
        assertions = case["assert"]
        if not isinstance(assertions, list):
            sys.stderr.write(f"Case '{case_id}' assert must be an array\n")
            sys.exit(1)
        # Validate each assertion
        for a_idx, assertion in enumerate(assertions):
            if not isinstance(assertion, dict):
                sys.stderr.write(f"Case '{case_id}' assertion at index {a_idx} must be an object\n")
                sys.exit(1)
            if "type" not in assertion:
                sys.stderr.write(f"Case '{case_id}' assertion at index {a_idx} missing 'type'\n")
                sys.exit(1)
            a_type = assertion["type"]
            if a_type not in KNOWN_ASSERTION_TYPES:
                sys.stderr.write(f"Case '{case_id}' unknown assertion type: {a_type}\n")
                sys.exit(1)
            # Type-specific validation
            if a_type == "matches":
                if "pattern" not in assertion:
                    sys.stderr.write(f"Case '{case_id}' matches assertion missing 'pattern'\n")
                    sys.exit(1)
                pattern = assertion["pattern"]
                if not isinstance(pattern, str):
                    sys.stderr.write(f"Case '{case_id}' matches pattern must be string\n")
                    sys.exit(1)
                try:
                    re.compile(pattern)
                except re.error as e:
                    sys.stderr.write(f"Case '{case_id}' invalid regex pattern: {e}\n")
                    sys.exit(1)
            elif a_type == "json_field_equals":
                if "field" not in assertion or "value" not in assertion:
                    sys.stderr.write(f"Case '{case_id}' json_field_equals missing 'field' or 'value'\n")
                    sys.exit(1)
                if not isinstance(assertion["field"], str):
                    sys.stderr.write(f"Case '{case_id}' json_field_equals field must be string\n")
                    sys.exit(1)
                # value can be any JSON-compatible; we'll accept any
            elif a_type == "contains" or a_type == "not_contains" or a_type == "equals":
                if "value" not in assertion:
                    sys.stderr.write(f"Case '{case_id}' {a_type} missing 'value'\n")
                    sys.exit(1)
                if not isinstance(assertion["value"], str):
                    sys.stderr.write(f"Case '{case_id}' {a_type} value must be string\n")
                    sys.exit(1)
                if a_type == "equals" and "normalize" in assertion:
                    if not isinstance(assertion["normalize"], bool):
                        sys.stderr.write(f"Case '{case_id}' equals normalize must be boolean\n")
                        sys.exit(1)
            elif a_type == "max_tokens":
                if "value" not in assertion:
                    sys.stderr.write(f"Case '{case_id}' max_tokens missing 'value'\n")
                    sys.exit(1)
                try:
                    val = int(assertion["value"])
                except (ValueError, TypeError):
                    sys.stderr.write(f"Case '{case_id}' max_tokens value must be integer\n")
                    sys.exit(1)
                assertion["value"] = val
            elif a_type == "finish_is":
                if "value" not in assertion:
                    sys.stderr.write(f"Case '{case_id}' finish_is missing 'value'\n")
                    sys.exit(1)
                val = assertion["value"]
                if not isinstance(val, str):
                    sys.stderr.write(f"Case '{case_id}' finish_is value must be string\n")
                    sys.exit(1)
                if val not in ("stop", "length", "refusal"):
                    sys.stderr.write(f"Case '{case_id}' finish_is value must be 'stop', 'length', or 'refusal'\n")
                    sys.exit(1)
            elif a_type == "all_of" or a_type == "any_of" or a_type == "json_subset":
                if "assertions" not in assertion:
                    sys.stderr.write(f"Case '{case_id}' {a_type} missing 'assertions'\n")
                    sys.exit(1)
                subassertions = assertion["assertions"]
                if not isinstance(subassertions, list):
                    sys.stderr.write(f"Case '{case_id}' {a_type} assertions must be an array\n")
                    sys.exit(1)
                # Recursively validate subassertions (we could call same validation but we'll just check type)
                for sub_idx, subassert in enumerate(subassertions):
                    if not isinstance(subassert, dict):
                        sys.stderr.write(f"Case '{case_id}' {a_type} subassertion at index {sub_idx} must be an object\n")
                        sys.exit(1)
                    if "type" not in subassert:
                        sys.stderr.write(f"Case '{case_id}' {a_type} subassertion at index {sub_idx} missing 'type'\n")
                        sys.exit(1)
                    sub_type = subassert["type"]
                    if sub_type not in KNOWN_ASSERTION_TYPES:
                        sys.stderr.write(f"Case '{case_id}' unknown assertion type in {a_type}: {sub_type}\n")
                        sys.exit(1)
                    # For matches in subassertions, validate pattern
                    if sub_type == "matches":
                        if "pattern" not in subassert:
                            sys.stderr.write(f"Case '{case_id}' subassertion matches missing 'pattern'\n")
                            sys.exit(1)
                        pat = subassert["pattern"]
                        if not isinstance(pat, str):
                            sys.stderr.write(f"Case '{case_id}' subassertion matches pattern must be string\n")
                            sys.exit(1)
                        try:
                            re.compile(pat)
                        except re.error as e:
                            sys.stderr.write(f"Case '{case_id}' invalid regex pattern in subassertion: {e}\n")
                            sys.exit(1)
            # other types have no extra fields beyond those already checked

    # Attach resolved prompt_file path and content already stored
    data["prompt_file"] = prompt_path
    data["prompt_content"] = prompt_content
    return data