# promptlab Project Constitution

## Core Principles

### 1. Spec-Driven Development (SDD)
- **Primacy of Specification**: The SPEC.md file is the single source of truth for all behavioral contracts
- **Spec-First Commitment**: First repository commit must contain SPEC.md with zero implementation code
- **Evolution Protocol**: When design changes, update SPEC.md before modifying any code
- **Verification**: Compliance checked via `git log --reverse --stat` to ensure spec precedes implementation

### 2. Subprocess-Only Model Interaction
- **Black-Box Principle**: Never import, copy, or reimplement the target model (stubmodel.py)
- **Exact CLI Contract**: All model calls execute via subprocess with precise argument structure:
  `python <model_binary> --prompt <prompt_file> --input <resolved_input> --temperature <temp> --max-tokens <max_tokens>`
- **Compatibility Guarantee**: Works with any model binary adhering to the same interface
- **Judge's Swapped-Model Test**: Enables evaluation with different model binaries during assessment

### 3. Deterministic & Reliable Measurement
- **Byte-Identical Output**: At temperature 0.0, repeated runs produce identical reports (excluding timing fields)
- **Timing Field Isolation**: `wall_ms` and `tokens_out_avg` are explicitly allowed to vary
- **Clean Diffs**: Isolating timing ensures meaningful comparison of prompt changes
- **Execution Safeguards**: 30-second timeout per subprocess prevents hanging processes

### 4. Comprehensive Flaky Handling
- **Unanimity Required**: Case status determined by pass rate across runs:
  - `pass`: pass_rate == 1.0 (all runs passed)
  - `fail`: pass_rate == 0.0 (all runs failed)
  - `flaky`: 0.0 < pass_rate < 1.0 (mixed results)
- **Anti-Degradation**: Prevents silent accuracy erosion; a case passing 7/10 runs is NOT considered passing
- **Per-Asset Accounting**: Tracks passes/failures for each assertion across all runs
- **Actionable Failures**: Captures expectation, actual output (truncated), and measured values

### 5. Exact Specification Compliance
- **Precise Schemas**: Suite files, reports, and comparison outputs must match defined JSON structures exactly
- **Strict Validation**: Malformed inputs produce Exit Code 1 with descriptive messages (never tracebacks)
- **Exit Code Contract**:
  - 0: Success (all cases passed / all checks passed / comparison completed)
  - 1: Bad usage/malformed input (checked before execution)
  - 4: Unreadable files (checked during file resolution)
  - 3: Model invocation failures (timeout, exceptions, non-zero exit)
  - 2: Test cases failed/flaky (evaluation result, not error)
- **Precedence Hierarchy**: 1 → 4 → 3 → 2 → 0 for simultaneous errors

### 6. Context Engineering Excellence
- **Required Artifacts**: All deliverables must include:
  - `CLAUDE.md`: Context file driving Claude Code development (graded)
  - `PROMPTS.md`: Five most important development prompts with analysis
  - `USAGE.md`: LLM-agent-focused usage guide with exit code guidance
  - `JOURNAL.md`: Responses to five mandatory reflective questions
- **Transparency**: Artifacts ensure visibility into development process and decision-making

### 7. Measurement Integrity
- **Source Constraint**: All measurements must come exclusively from promptlab reports
- **Comparison Validity**: Requires identical suite, model settings, and run counts
- **Accuracy Metric**: Gain measured as delta in pass_rate averaged across cases
- **Cost Measurement**: Percentage change in total tokens_in and tokens_out
- **Honest Assessment**: Failed experiment documentation (one unhelpful change) is required and graded

### 8. Assertion Engine Excellence
- **Pure Function Model**: Assertions are side-effect-free functions returning (passed, failure_message, measured_value)
- **Extensibility**: New assertion types added via registry without modifying core logic
- **Composition Support**: `all_of` (AND), `any_of` (OR), `json_subset` (structural equality) with any-depth nesting
- **Deterministic Evaluation**: Consistent results regardless of assertion order or nesting depth
- **Rich Reporting**: Per-assertion counts work recursively; failures detail specific child assertions

## Code Standards Derived From This Constitution

### Quality
- Deterministic output at temperature 0.0 (except timing fields)
- No crash reaches user; all errors produce one-line messages and correct exit codes
- Strict validation prevents tracebacks from reaching users
- Exit codes enable reliable automation and CI/CD integration

### Testing
- Unit test suite covers assertion evaluation, suite parsing, flaky classification, compare logic
- `python -m unittest` must pass from fresh clone
- Tests avoid direct dependencies on stubmodel.py (use mocks or subprocess only)
- Fresh clone verification: `doctor` → `run --suite suites/smoke.json` → `python -m unittest` in <5 minutes

### Performance
- Total-cost accounting (sums across runs) makes cost-regressions visible
- 30-second timeout balances complexity detection with hang prevention
- Stream routing prevents stdout corruption while enabling machine/human-readable output

### Security
- No network access; everything is local
- No hardcoded secrets or tokens; use environment variables and documentation
- Subprocess isolation prevents supply chain attacks via model binary

### Architecture
- Composition over inheritance: Assertion engine built on pure function registry
- Separation of concerns: Test runner, assertion engine, flaky detector, comparator, doctor, reporter
- Extensibility points: New assertion types via interface implementation and registration
- Reporting integration: Failures in nested assertions bubble up with contextual details