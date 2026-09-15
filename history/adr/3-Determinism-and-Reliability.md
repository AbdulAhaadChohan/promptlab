# ADR-3: Determinism and Reliability

> **Scope**: Document decision clusters, not individual technology choices. Group related decisions that work together (e.g., "Frontend Stack" not separate ADRs for framework, styling, deployment).

- **Status:** Proposed
- **Date:** 2026-09-16
- **Feature:** main
- **Context:** Need to ensure that prompt engineering experiments produce reliable, reproducible results that enable valid comparison and iteration, while acknowledging that timing variations are inherent and expected in subprocess execution.

## Decision

- **Determinism Guarantee**: At temperature 0.0, running the same suite twice produces byte-identical reports except for:
  - The `wall_ms` field in the `totals` section
  - Individual case `tokens_out_avg` values
- **Timing Field Isolation**: Timing fields (`wall_ms` in totals and `tokens_out_avg` in cases) are explicitly isolated to ensure that non-timing fields remain byte-identical across runs
- **Implementation Approach**: Ensure all non-timing computations are deterministic; only timing-related measurements vary due to system load and subprocess execution variance

## Consequences

### Positive
- **Reproducible Experiments**: Enables valid comparison of prompt iterations by eliminating non-timing variability
- **Clean Diffs**: Byte-identical reports (except timing) allow clear visual and tool-based comparison of changes
- **Trustworthy Measurements**: Engineers can trust that differences in non-timing fields reflect actual changes in prompt behavior
- **Valid Regression Detection**: Isolating timing prevents false regressions/improvements due to system load variations
- **Scientific Rigor**: Supports methodical prompt engineering approach based on measurable, repeatable experiments
- **Debugging Aid**: When non-timing fields differ, engineers know the difference is due to actual prompt/model behavior changes

### Negative
- **Timing Variability Acceptance**: Requires users to understand and accept that timing fields will naturally vary
- **Complexity in Implementation**: Requires careful separation of deterministic and timing-sensitive code paths
- **Limited Determinism Scope**: Does not guarantee identical timing, which may be important for some performance-sensitive use cases
- **Potential Misunderstanding**: Users might expect full byte-identity and be confused by timing differences
- **Implementation Burden**: Requires vigilance to ensure no non-deterministic elements creep into non-timing fields

## Alternatives Considered

- **Full Determinism Including Timing**:
  - Attempt to control or eliminate all timing variations
  - Why rejected: Impossible to guarantee in general due to system load, process scheduling, and environmental factors
  
- **No Determinism Guarantee**:
  - Accept full non-determinism and document limitations
  - Why rejected: Would undermine the value proposition of objective, quantifiable prompt evaluation
  
- **Deterministic Timing with Mocking**:
  - Replace timing functions with deterministic mocks during testing
  - Why rejected: Would not reflect real-world performance; defeats purpose of measuring actual execution time
  
- **Timing Field Exclusion**:
  - Omit timing fields from reports entirely
  - Why rejected: Timing information is valuable for performance analysis and cost estimation
  
- **Different Isolation Approach**:
  - Isolate different fields or use different strategies for ensuring comparability
  - Why rejected: Current approach correctly identifies the sources of non-determinism (wall-clock time and per-run token averaging)

## References

- Feature Spec: specs/main/spec.md
- Implementation Plan: specs/main/plan.md
- Related ADRs: 1-Model-Interaction-Architecture, 2-Assertion-and-Evaluation-Architecture
- Evaluator Evidence: