# promptlab Implementation Plan

## 1. Architectural Decisions Overview

Based on the SPEC.md, the following key architectural decisions have been made:

### 1.1 Kuzey-Only Model Invocation Principle
The system will never import or reimplement the target model, treating it as a black-box executable with a defined CLI contract.

### 1.2 Subprocess Execution with Strict Safeguards
All model calls execute via subprocess with a 30-second timeout, exiting with code 3 on failure.

### 1.3 Pure Function Assertion Model
Assertions are pure functions taking (model_output, assertion_config) and returning (passed, failure_message, measured_value).

### 1.4 Strict Flaky Policy (Unanimity Required)
A case passes only if all runs pass (pass_rate == 1.0); fails if all runs fail (pass_rate == 0.0); flaky otherwise.

### 1.5 Fenced-JSON Validation
Fenced JSON (```json ... ```) is considered valid for assertion purposes.

### 1.6 Regression Definition
Any decrease in pass rate constitutes a regression, regardless of absolute pass/fail labels.

### 1.6 Cost Accounting Approach
Metrics use sums across all runs rather than averages to make cost-regressions visible.

### 1.7 Composability and Extensibility Engine
Assertion engine built around pure functions, registry pattern, composite assertions, and recursive evaluation.

## 2. Component Implementation Plan

### 2.1 Test Runner
- Execute test suites by iterating through cases
- For each case, execute model invocations per the runs count
- Evaluate assertions against each model output
- Track pass/fail/flaky status per case
- Aggregate results across all cases

### 2.2 Assertion Engine
- Implement core assertion types: contains, not_contains, equals, matches, json_valid, json_field_equals
- Implement resource assertions: max_tokens, finish_is
- Implement composite assertions: all_of, any_of, json_subset
- Build registry for assertion types
- Implement pure function interface for all assertions
- Support nesting of composite assertions to any depth
- Ensure deterministic, side-effect-free evaluation

### 2.3 Flaky Detector
- Calculate pass rate for each case across runs
- Classify cases as pass (1.0), fail (0.0), or flaky (0.0 < rate < 1.0)
- Track assertion-level pass/fail counts

### 2.4 Comparator
- Load two reports
- Compare pass rates case-by-case
- Identify regressions (decreased pass rate), improvements (increased pass rate), unchanged
- Calculate percentage changes in aggregate metrics (tokens_in, tokens_out, wall_ms)

### 2.5 Doctor
- Validate environment: Python availability, required packages
- Check installation integrity
- Verify subprocess model invocation works
- Return appropriate exit codes

### 2.6 Reporter
- Generate JSON report with exact schema specified
- Calculate SHA-256 hash of prompt file (first 12 hex chars)
- Aggregate metrics across cases and runs
- Format human-readable summary
- Implement stream routing rules (stdout/stderr based on --out flag)

## 3. Technical Implementation Details

### 3.1 Language Choice
Python 3.8+ selected for:
- Excellent subprocess handling
- Built-in JSON support
- Regular expression library (re)
- Cross-platform compatibility
- Rich ecosystem for testing

### 3.2 Project Structure
- `/src/main.py`: CLI entry point with command dispatch
- `/src/runner.py`: Test runner implementation
- `/src/assertions.py`: Assertion engine and types
- `/src/compare.py`: Report comparison logic
- `/src/doctor.py`: Environment validation
- `/src/reporter.py`: JSON and human-readable report generation
- `/suites/`: Directory for test suite JSON files
- `/prompts/`: Directory for prompt text files
- `history/prompts/`: Prompt History Records (automatically generated)
- `history/adr/`: Architecture Decision Records (to be created)

### 3.3 Key Implementation Notes
- **Subprocess Timeout**: Use threading.Timer or similar for cross-platform 30-second timeout
- **JSON Parsing**: Strip fenced JSON markers (```json\n and \n```) before parsing
- **Token Calculation**: Implement tokens = ceil(len(text) / 4) as specified
- **Error Handling**: Distinguish between bad usage (exit code 1) and model invocation failure (exit code 3)
- **Determinism**: At temperature 0.0, ensure byte-identical reports except timing fields
- **Stream Routing**: Carefully manage stdout/stderr based on --out and --report flags per specification

## 4. Dependencies and External Interfaces

### 4.1 Model Interface
- Expects model binary at configurable path
- Accepts arguments: --prompt <file> --input <string> --temperature <float> --max-tokens <int>
- Returns JSON object on stdout: {"output": "...", "tokens_in": N, "tokens_out": M, "finish": "...", "latency_ms": T}
- Exits with code 0 on success, non-zero on failure

### 4.2 File Format Dependencies
- Suite files: JSON format as specified
- Prompt files: Plain text, UTF-8 encoding
- Input files (when referenced): Plain text, UTF-8 encoding, trimmed trailing newlines
- Report files: JSON format as specified

## 5. Risk Assessment and Mitigation

### 5.1 Model Binary Compatibility Risk
- Mitigation: Define clear CLI contract in SPEC.md; validate during doctor check
- Impact: High - core to subprocess-only principle

### 5.2 Performance Risk from Subprocess Overhead
- Mitigation: Consider result caching as stretch goal; batch executions where safe
- Impact: Medium - affects execution speed but not correctness

### 5.3 Correctness Risk in Assertion Engine
- Mitigation: Comprehensive unit testing; property-based testing for edge cases
- Impact: High - core functionality

### 5.4 Security Risk from Arbitrary Model Execution
- Mitigation: Document that users must trust model binaries; no sandboxing implemented
- Impact: Low - trust boundary is explicit

## 6. Implementation Milestones

### Milestone 1: Core Infrastructure
- CLI framework with command parsing
- Subprocess model invocation with timeout
- Basic test runner execution
- Exit code handling

### Milestone 2: Assertion Engine
- Core assertion types implementation
- Registry pattern
- Pure function interface
- Basic assertion evaluation

### Milestone 3: Composite Assertions
- all_of, any_of, json_subset implementation
- Nesting support
- Recursive evaluation
- Reporting integration

### Milestone 4: Flaky Detection and Reporting
- Pass/fail/flaky classification
- Per-assertion statistics
- JSON report generation
- Human-readable summary

### Milestone 5: Comparison and Doctor
- Report comparison logic
- Environment validation
- Final polish and testing

## 7. Open Questions and Decisions Needed

### 7.1 Model Binary Location
- How should users specify the model binary path?
  - Option A: Environment variable (PROMPTLAB_MODEL_BINARY)
  - Option B: Command-line flag (--model-binary)
  - Option C: Config file (~/.promptlab/config)
- Decision needed: [To be determined]

### 7.2 Temporary File Handling
- Should we create temporary files for complex inputs?
  - Currently, inputs are passed directly via --input argument
  - For very large inputs, might need file-based approach
- Decision: Stick to --input argument as specified; document limitations

### 7.3 Progress Reporting
- Should we show progress during execution?
  - Not specified in requirements
  - Could add verbose flag as enhancement
- Decision: Not required for MVP; consider as stretch goal

## 8. Acceptance Criteria

### 8.1 Minimum Viable Product
- `promptlab doctor` validates environment
- `promptlab run` executes suites and produces correct JSON reports
- `promptlab compare` detects changes between reports
- All exit codes work as specified
- Assertion engine supports all required types
- Flaky policy implemented correctly

### 8.2 Quality Requirements
- Code follows Python best practices
- Comprehensive unit test coverage
- Deterministic output at temperature 0.0 (except timing)
- Clear error messages matching specification