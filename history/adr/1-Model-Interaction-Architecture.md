# ADR-1: Model Interaction Architecture

> **Scope**: Document decision clusters, not individual technology choices. Group related decisions that work together (e.g., "Frontend Stack" not separate ADRs for framework, styling, deployment).

- **Status:** Proposed
- **Date:** 2026-09-16
- **Feature:** main
- **Context:** The system needs to interact with various language model black-box executables through a well-defined interface while ensuring reliable execution, proper error handling, and clean output routing for integration into automated workflows.

## Decision

- **Subprocess-Only Model Invocation Principle**: Never import or reimplement the target model; treat it as a black-box executable with defined CLI contract
- **Subprocess Execution Contract**: All model calls execute via subprocess with exact argument structure: `python <model_binary> --prompt <prompt_file> --input <resolved_input> --temperature <temp> --max-tokens <max_tokens>`
- **Execution Safeguards**: Apply strict 30-second timeout per subprocess; exit with code 3 (Model Invocation Failure) on timeout, exception, or non-zero exit status
- **Stream Routing Rule**: 
  - If `--out report.json` provided: human-readable report (from `--or` flag) printed to `stderr`
  - If `--out` omitted: raw JSON report to `stdout`, `--report` summary (if requested) to `stderr`
- **Exit Codes Contract**:
  - 0: Success (all cases passed for run; all checks passed for doctor; comparison completed for compare)
  - 1: Bad usage or malformed input (suite file, report file, or command arguments)
  - 2: One or more cases failed (run only) - *this is a result, not an error*
  - 3: Model invocation failed (model not found, bad arguments to model, or prompt/input unreadable)
  - 4: Suite or report file unreadable (file not found, permission denied, or invalid JSON)
- **Suite Parsing Edge Cases**:
  - Empty Suite (`"cases": []`): Valid suite; runs without error; report with zero total metrics; exits with code 0
  - Empty Assertions (`"assert": []`): Case marked as `pass` if model invocation completes with exit code 0 (`pass_rate: 1.0`)

## Consequences

### Positive
- **Compatibility**: Works with any model binary adhering to the CLI contract, enabling the judge's swapped-model test
- **Reliability**: Timeout and error handling prevent hanging processes and unclear failure states
- **Clarity**: Distinct exit codes allow calling programs to automatically distinguish error types
- **Usability**: Stream routing prevents output corruption while enabling both machine-readable and human-readable output
- **Robustness**: Well-defined edge case handling ensures predictable behavior for boundary conditions
- **Integration**: Clean separation of concerns facilitates use in CI/CD pipelines and automated workflows

### Negative
- **Performance Overhead**: Subprocess invocation adds overhead compared to direct library calls
- **Interface Inflexibility**: Changing the CLI contract breaks compatibility with existing model binaries
- **Error Code Limitations**: Fixed set of exit codes may not capture all possible error scenarios with desired granularity
- **Stream Routing Complexity**: Logic for routing output based on flags adds implementation complexity
- **Black Box Limitations**: Cannot access internal model state or intermediate computations for richer analysis

## Alternatives Considered

- **Direct Import/Reimplementation**:
  - Import model libraries directly or reimplement model logic
  - Why rejected: Would break subprocess-only principle; prevent swapped-model testing; create compatibility burden for every model variant
  
- **Alternative IPC Mechanisms**:
  - Use sockets, shared memory, or message queues instead of subprocess
  - Why rejected: Significantly more complex; loses simplicity and broad compatibility of subprocess approach
  
- **Different Timeout Values**:
  - Shorter or longer timeouts, or make configurable
  - Why rejected: 30 seconds provides balance between catching hangs and allowing sufficient time for complex prompts; making configurable adds complexity for little gain
  
- **Alternative Error Code Schemes**:
  - Use exception hierarchy or detailed error objects
  - Why rejected: Exit codes are standard for CLI tools; specification requires specific codes for tool integration
  
- **Different Stream Routing**:
  - Always send all output to stdout or stderr
  - Make routing fully configurable via flags/environment
  - Why rejected: Would break specification requirements and reduce usability for common use cases

## References

- Feature Spec: specs/main/spec.md
- Implementation Plan: specs/main/plan.md
- Related ADRs: 
- Evaluator Evidence: