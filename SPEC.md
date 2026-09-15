# promptlab: Prompt Test Runner Specification

## 1. Executive Overview & System Architecture

promptlab is a command-line test harness designed to evaluate prompt engineering iterations through deterministic measurement. It addresses the core problem that prompts lack reliable test runners like code has, replacing subjective "vibes" assessment with objective, quantifiable metrics.

The system operates on a subprocess-only model invocation principle: it never imports or reimplements the target model (stubmodel.py), treating it as a black-box executable with a defined CLI contract. This ensures compatibility with any model binary that adheres to the same interface, enabling the judge's swapped-model test.

Core components:
- **Test Runner**: Executes suites against model invocations, evaluates assertions
- **Assertion Engine**: Implements eight core assertion types with composition capabilities
- **Flaky Detector**: Distinguishes pass/fail/flaky outcomes across multiple runs
- **Comparator**: Analyzes two reports to detect regressions, improvements, and changes
- **Doctor**: Validates environment and installation integrity
- **Reporter**: Generates machine-readable JSON reports and human-readable summaries

## 2. CLI Interface & Exit Codes Contract

### 2.1 promptlab run
Executes a test suite against the model.

```
promptlab run --suite <file> [--runs N] [--out report.json] [--report]
```

- `--suite <file>`: Path to suite JSON file (required)
- `--runs N`: Number of times to execute each case (overrides suite runs, default: 1)
- `--out report.json`: Write JSON report to file (if omitted, report goes to stdout)
- `--print`: Print human-readable summary to stderr (when --out is used) or stdout (when --out omitted)

### 2.2 promptlab compare
Compares two reports to detect changes between prompt versions.

```
promptlab compare --baseline <report.json> --candidate <report.json> [--out diff.json]
```

- `--baseline <report.json>`: Reference report (required)
- `--candidate <report.json>`: Experimental report (required)
- `--out diff.json`: Write comparison JSON to file (if omitted, output goes to stdout)

### 2.3 promptlab doctor
Validates environment and installation.

```
promptlab doctor
```

Takes no arguments. Exits with code 0 if all checks pass.

### 2.4 Exit Codes
All commands follow this exit code contract:
- `0`: Success (for run: all cases passed; for doctor: all checks passed; for compare: comparison completed)
- `1`: Bad usage or malformed input (suite file, report file, or command arguments)
- `2`: One or more cases failed (run only) - *this is a result, not an error*
- `3`: Model invocation failed (model not found, bad arguments to model, or prompt/input unreadable)
- `4`: Suite or report file unreadable (file not found, permission denied, or invalid JSON)

## 3. Suite File & Input Specification

### 3.1 Suite Format
Suite files are JSON documents with this exact structure:
```json
{
  "name": "suite-name",
  "prompt_file": "path/to/prompt.txt",
  "model": {
    "temperature": 0.0,
    "max_tokens": 256
  },
  "runs": 1,
  "cases": [
    {
      "id": "case-unique-id",
      "input": "string input" | {"file": "path/to/input.txt"},
      "assert": [
        {
          "type": "assertion-type",
          // assertion-specific fields
        }
      ]
    }
  ]
}
```

### 3.2 Field Definitions
- `name`: Suite identifier (string)
- `prompt_file`: Path to prompt file, relative to suite file location
- `model`: Object containing model parameters
  - `temperature`: Float (0.0 for deterministic behavior)
  - `max_tokens`: Integer (maximum tokens for model output)
- `runs`: Integer (default execution count per case, overridable by --runs)
- `cases`: Array of case objects
  - `id`: Unique case identifier (string)
  - `input`: Either a string directly or object `{"file": "path"}`
    - File paths are relative to suite file location, not working directory
  - `assert`: Array of assertion objects to evaluate against model output

### 3.3 Input Handling
- String inputs are used directly
- File inputs are read as UTF-8 text, trimmed of trailing newlines
- Missing input files produce exit code 3 with descriptive message
- Input file paths are resolved relative to the suite file's directory

## 4. Architectural Design Decisions

### 4.1 Assertion Evaluation Model
Assertions are pure functions that take (model_output, assertion_config) and return:
- `passed`: Boolean indicating assertion satisfaction
- `failure_message`: String describing failure (empty if passed)
- `measured_value`: Optional actual value for reporting (e.g., token count)

This pure function model enables the curveball requirements for nested assertions (all_of, any_of, json_subset) without modifying the reporting mechanism.

### 4.2 Flaky Policy & Threshold
A case status is determined by pass rate across runs:
- `pass`: pass_rate == 1.0 (all runs passed)
- `fail`: pass_rate == 0.0 (all runs failed)
- `flaky`: 0.0 < pass_rate < 1.0 (mixed results)

This strict unanimity policy prevents silent degradation reporting and aligns with the requirement that "a case that passes 7 times out of 10 is not a passing case."

### 4.3 Fenced-JSON Decision
Fenced JSON (output wrapped in ```json ... ```) is considered valid JSON for assertion purposes. This decision ensures consistency between json_valid and json_field_equals assertions, as json_field_equals must operate on the parsed JSON content regardless of fencing.

### 4.4 Regression Definition
Any decrease in pass rate constitutes a regression, regardless of absolute pass/fail labels under the flaky policy. A pass rate moving from 1.0 to 0.99 is a regression that compare must detect and report, preventing silent accuracy erosion.

### 4.5 Failure Taxonomy
Failures are categorized by assertion type and captured with:
- `assertion_type`: Type that failed
- `expected`: Assertion expectation (value, pattern, etc.)
- `actual`: Truncated model output relevant to the failure
- `measured_value`: Specific measurement (tokens, field value, etc.) when applicable

### 4.6 Cost Accounting
Reports use totals across all runs for token and timing metrics:
- `tokens_in`: Sum of tokens_in across all runs
- `tokens_out`: Sum of tokens_out across all runs
- `wall_ms`: Sum of wall-clock time across all runs
This approach captures total cost rather than averaging, making cost-regressions visible.

## 5. Assertion Engine Specification

All assertions evaluate the model's JSON output object: `{"output": "...", "tokens_in": N, "tokens_out": M, "finish": "...", "latency_ms": T}`.

### 5.1 Core Assertions

#### contains
Passes when model output contains the specified substring.
- Fields: `value` (string), `optional ignore_case` (boolean)
- Semantics: Case-sensitive substring match unless ignore_case=true
- Example: `{ "type": "contains", "value": "error" }`

#### not_contains
Passes when model output does NOT contain the specified substring.
- Fields: `value` (string), `optional ignore_case` (boolean)
- Semantics: Inverse of contains
- Example: `{ "type": "not_contains", "value": "Sure" }`

#### equals
Passes when model output exactly equals the specified string.
- Fields: `value` (string), `optional normalize` (boolean)
- Semantics: Exact string match; when normalize=true, strips and collapses whitespace
- Example: `{ "type": "equals", "value": "42" }`

#### matches
Passes when model output matches the specified regular expression.
- Fields: `pattern` (string regex)
- Semantics: Uses Python's re module; invalid regex produces exit code 1
- Example: `{ "type": "matches", "pattern": "^\\d{3}-\\d{2}-\\d{4}$" }`

#### json_valid
Passes when model output parses as valid JSON.
- Fields: none
- Semantics: Attempts to parse output as JSON; fenced JSON (```json ... ```) is stripped before parsing per fenced-JSON decision
- Example: `{ "type": "json_valid" }`

#### json_field_equals
Passes when output parses as JSON and the specified field equals the expected value.
- Fields: `field` (dotted-path string), `value` (any JSON-compatible)
- Semantics: Resolves dotted path (e.g., "user.address.street"); missing paths fail; type-sensitive comparison
- Example: `{ "type": "json_field_equals", "field": "category", "value": "billing" }`

### 5.2 Resource Assertions

#### max_tokens
Passes when tokens_out is at or below the specified value.
- Fields: `value` (integer)
- Semantics: Uses the token rule: tokens = ceil(len(text) / 4); compares against model-reported tokens_out
- Example: `{ "type": "max_tokens", "value": 40 }`

#### finish_is
Passes when finish field equals the specified value.
- Fields: `value` (string: "stop", "length", or "refusal")
- Semantics: Exact string match on the finish field from model output
- Example: `{ "type": "finish_is", "value": "stop" }`

### 5.3 Curveball Assertions (Composition & Extensibility)

These assertions enable complex validation structures and were added via the curveball requirement at 14:00.

#### all_of
Passes when ALL child assertions pass.
- Fields: `assertions` (array of assertion objects)
- Semantics: Logical AND over child assertions; reports as single assertion in per-assertion counts
- Nesting: Can nest all_of/any_of/json_subset to any depth
- Example:
  ```json
  {
    "type": "all_of",
    "assertions": [
      { "type": "json_field_equals", "field": "status", "value": "success" },
      { "type": "max_tokens", "value": 100 }
    ]
  }
  ```

#### any_of
Passes when AT LEAST ONE child assertion passes.
- Fields: `assertions` (array of assertion objects)
- Semantics: Logical OR over child assertions; reports as single assertion in per-assertion counts
- Nesting: Can nest all_of/any_of/json_subset to any depth
- Example:
  ```json
  {
    "type": "any_of",
    "assertions": [
      { "type": "equals", "value": "yes" },
      { "type": "equals", "value": "y" }
    ]
  }
  ```

#### json_subset
Passes when output parses as JSON and contains all key/value pairs from the subset object at any nesting depth.
- Fields: `subset` (JSON object)
- Semantics: Recursively checks that every key in subset exists in output with equal value; ignores extra keys in output
- Nesting: Can be nested inside all_of/any_of; subset values can be objects for deep matching
- Example:
  ```json
  {
    "type": "json_subset",
    "subset": {
      "user": {
        "id": 123,
        "active": true
      },
      "status": "confirmed"
    }
  }
  ```

### 5.4 Assertion Evaluation Rules
- All assertions in a case are evaluated regardless of individual failures (no short-circuiting)
- Per-assertion counts track passes/failures across all runs
- Failures array contains detailed information for the first failing run (or a representative failure for flaky cases)
- Assertion evaluation is deterministic and side-effect free

## 6. Composition & Extensibility Engine

The assertion engine is designed around composability and extension:
- **Pure Function Base**: Each assertion type implements a pure function interface
- **Registry Pattern**: Assertion types are registered by name in a central registry
- **Composite Assertions**: all_of, any_of, and json_subset are themselves assertions that contain other assertions
- **Recursive Evaluation**: Composite assertions evaluate their children using the same engine
- **Reporting Integration**: Per-assertion counts work recursively - a failure in a nested assertion bubbles up as a single top-level assertion entry with detailed failure information
- **Extensibility Point**: New assertion types can be added by implementing the pure function interface and registering in the assertion registry without modifying core logic

This design satisfies the curveball requirement that teams with a registry and return value can add nesting in twenty minutes, while those with procedural assertion chains would need significant refactoring.

## 7. Reporting & Schema Integrity

### 7.1 Report Schema
Reports are JSON documents with this exact structure:
```json
{
  "suite": "suite-name",
  "prompt_file": "path/to/prompt.txt",
  "prompt_hash": "a19f40cc21b8",
  "runs": 3,
  "model": {
    "temperature": 0.4,
    "max_tokens": 256
  },
  "totals": {
    "cases": 20,
    "passed": 16,
    "failed": 3,
    "flaky": 1,
    "tokens_in": 4120,
    "tokens_out": 980,
    "wall_ms": 8640
  },
  "cases": [
    {
      "id": "c001",
      "status": "pass",
      "pass_rate": 1.0,
      "tokens_out_avg": 21,
      "assertions": [
        {
          "type": "json_valid",
          "passed": 3,
          "failed": 0
        }
      ],
      "failures": []
    }
  ]
}
```

### 7.2 Field Definitions
- `suite`: Name from suite file
- `prompt_file`: Path from suite file
- `prompt_hash`: First 12 hex characters of SHA-256 of prompt file bytes
- `runs`: Actual number of executions per case (from --runs or suite runs)
- `model`: Model parameters used for this report
- `totals`: Aggregate statistics across all cases
  - `cases`: Total number of cases
  - `passed`: Cases with status = pass
  - `failed`: Cases with status = fail
  - `flaky`: Cases with status = flaky
  - `tokens_in`: Sum of tokens_in across all runs and cases
  - `tokens_out`: Sum of tokens_out across all runs and cases
  - `wall_ms`: Sum of wall-clock time across all runs and cases (ms)
- `cases`: Array of case result objects
  - `id`: Case identifier
  - `status`: "pass", "fail", or "flaky" per flaky policy
  - `pass_rate`: Float between 0.0 and 1.0 inclusive
  - `tokens_out_avg`: Average tokens_out per run for this case
  - `assertions`: Per-assertion statistics
    - `type`: Assertion type
    - `passed`: Number of runs this assertion passed
    - `failed`: Number of runs this assertion failed
  - `failures`: Array containing failure information (empty if pass)
    - Each failure object includes:
      - `assertion`: The assertion object that failed
      - `expected`: Expected value per assertion semantics
      - `actual`: Truncated relevant portion of model output
      - `measured_value`: Specific measurement when applicable (tokens, field value, etc.)
      - `run_index`: Which run produced this failure (0-based)

### 7.3 Determinism Guarantee
At temperature 0.0, running the same suite twice produces byte-identical reports except for the `wall_ms` field in `totals` and individual case `tokens_out_avg` values. Timing fields are isolated to ensure clean diffs.

### 7.4 Human-Readable Output
The `--report` flag (or stdout when `--out` omitted) produces a concise summary:
```
Suite: classify-smoke
Passed: 16/20 (80.0%)
Flaky: 1/20 (5.0%)
Failed: 3/20 (15.0%)
Tokens In: 4,120 | Tokens Out: 980 | Wall Time: 8.64s
Worst Cases:
  c007: pass_rate=0.3 (assertions: json_valid)
  c012: pass_rate=0.6 (assertions: max_tokens, finish_is)
  c003: pass_rate=0.8 (assertions: json_field_equals)
```

## 8. Prompt Engineering & Optimization Track

### 8.1 Improvement Process
Using promptlab as the measurement instrument, teams iterate on prompts to achieve measurable gains:
1. Establish baseline report with starter prompt (prompts/classify_v1.txt)
2. Hypothesize improvement based on prompt engineering principles
3. Modify prompt and generate candidate report
4. Use compare to quantify change (accuracy delta, cost delta)
5. Document iteration in IMPROVEMENT.md
6. Repeat until satisfactory improvement achieved (minimum four iterations)

### 8.2 IMPROVEMENT.md Structure
```markdown
# Prompt Improvement Log

## Baseline Report
[Summary of baseline report from prompts/classify_v1.txt]

## Iteration 1: [Change Description]
- Change: [What was modified in the prompt]
- Prediction: [Expected effect on accuracy and cost]
- Result: [Actual compare output showing accuracy and cost changes]
- Verdict: [Whether prediction was correct and why]

## Iteration 2: [Change Description]
- Change: [What was modified in the prompt]
- Prediction: [Expected effect on accuracy and cost]
- Result: [Actual compare output showing accuracy and cost changes]
- Verdict: [Whether prediction was correct and why]

[Continue for minimum four iterations]

## Final Assessment
- Total accuracy gain: [X.XX]
- Total cost change: [Y% tokens, Z% time]
- Key learnings: [What prompt engineering techniques proved effective]
- Failed experiment: [Documentation of one change that did not help, as required]
```

### 8.3 Measurement Integrity
- All measurements must come from promptlab reports
- Comparisons must use the same suite, model settings, and run counts
- Accuracy gain is measured as delta in pass_rate averaged across cases
- Cost is measured as percentage change in tokens_in and tokens_out
- The failed experiment documentation is graded component requiring honest assessment

## 9. Context Engineering & Deliverables Inventory

### 9.1 Required Context Files
All deliverables must include these context engineering artifacts:

#### CLAUDE.md
The context file used to drive Claude Code during development. Graded for quality and appropriateness.

#### PROMPTS.md
Documentation of the five most important prompts used during development:
```
1. [Prompt text]
   - Response: [Key portion of model response]
   - Change: [What you modified and why]
   - Effect: [Impact on development velocity or quality]

2. [Prompt text]
   - Response: [Key portion of model response]
   - Change: [What you modified and why]
   - Effect: [Impact on development velocity or quality]

[Continue for five prompts]
```

#### USAGE.md
Documentation written for an LLM agent that will run harness without human watching:
```
# promptlab Usage Guide

## Commands

### promptlab run
- What it does: Executes test suite against model
- When to use: Validating prompt changes, regression testing
- When NOT to use: Production model serving (this is a test tool only)
- Exit codes:
  - 0: All cases passed
  - 1: Bad usage/malformed suite
  - 2: One or more cases failed (expected outcome)
  - 3: Model invocation failed
  - 4: Suite file unreadable
- Agent action: On exit code 2, analyze failures and consider prompt improvement

### promptlab compare
- What it does: Compares two reports to detect changes
- When to use: Measuring prompt improvement, A/B testing
- When NOT to use: Comparing unrelated experiments
- Warnings: Triggered when comparing reports with different prompt_hash or model settings
- Agent action: Review compare output for regressions vs. improvements

### promptlab doctor
- What it does: Validates environment and installation
- When to use: Initial setup, troubleshooting
- Exit codes: 0 (healthy) or non-zero (specific issue identified)
- Agent action: Address any reported issues before proceeding
```

#### JOURNAL.md
Responses to five required questions:
1. Three decisions we made, and what we rejected in each case.
2. The hardest bug we hit, and how we found the root cause.
3. Something Claude Code got confidently wrong, and how we caught it.
4. What we would do differently with four more hours.
5. Who did what -- per person.

## 10. Verification & Definition of Done

### 10.1 Unit Testing Requirements
- Test suite for harness itself using Python unittest
- Must cover: assertion evaluation, suite parsing, flaky classification, compare logic
- `python -m unittest` must pass from fresh clone
- Tests must not import or depend on stubmodel.py (mock or subprocess only)

### 10.2 Starter Verification
Fresh clone must satisfy in under five minutes:
1. `promptlab doctor` runs successfully
2. `promptlab run --suite suites/smoke.json` executes without error
3. `python -m unittest` passes

### 10.3 Spec-Driven Development Enforcement
- First commit contains SPEC.md and no implementation code (verified via `git log --reverse --stat`)
- When design changes, update SPEC.md before code changes
- SPEC.md serves as the single source of truth for behavioral contracts

### 10.4 Stretch Goals (Optional Enhancements)
- Parallel case execution with deterministic report ordering
- Result cache keyed on prompt hash, input, and model settings
- HTML report format (--format html)
- Statistical honesty: confidence intervals on pass rates with low-run warnings

## Conclusion

This specification establishes promptlab as a rigorous, measurement-driven tool for prompt engineering that replaces subjective evaluation with objective, deterministic assessment. By enforcing spec-first development, subprocess-only model invocation, and comprehensive flaky handling, it ensures teams gain genuine insight into prompt quality rather than comforting illusions.

The inclusion of compositional assertions via the curveball requirement demonstrates the architecture's extensibility, while the required context artifacts ensure transparency in the development process itself.