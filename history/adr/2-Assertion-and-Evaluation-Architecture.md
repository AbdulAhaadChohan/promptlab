# ADR-2: Assertion and Evaluation Architecture

> **Scope**: Document decision clusters, not individual technology choices. Group related decisions that work together (e.g., "Frontend Stack" not separate ADRs for framework, styling, deployment).

- **Status:** Proposed
- **Date:** 2026-09-16
- **Feature:** main
- **Context:** Need to evaluate prompt engineering iterations through deterministic, extensible assertion mechanisms that support complex validation requirements while providing clear, actionable feedback on test results.

## Decision

- **Assertion Evaluation Model**: Assertions are pure functions taking (model_output, assertion_config) returning (passed: boolean, failure_message: string, measured_value: optional)
- **Flaky Policy (Unanimity Required)**: Case status determined by pass rate across runs: pass (1.0), fail (0.0), flaky (0.0 < rate < 1.0)
- **Fenced-JSON Handling**: Fenced JSON (```json ... ```) considered valid JSON for assertion purposes (stripped before parsing)
- **Regression Definition**: Any decrease in pass rate constitutes a regression, regardless of absolute pass/fail labels
- **Failure Taxonomy**: Failures categorized by assertion type with captured expectation, actual output (truncated), and measured value when applicable
- **Cost Accounting Approach**: Reports use sums across all runs for token/timing metrics (not averages)
- **Core Assertion Types**: contains, not_contains, equals, matches, json_valid, json_field_equals
- **Resource Assertion Types**: max_tokens, finish_is
- **Composite Assertions**: all_of (AND), any_of (OR), json_subset (structural equality)
- **Assertion Engine Design**: Pure function base, registry pattern, composite assertions, recursive evaluation, reporting integration
- **Report Schema**: Exact JSON structure with suite, prompt_file, prompt_hash, runs, model, totals, and detailed cases/assertions data
- **Human-Readable Output**: Concise summary showing pass/flaky/fail rates, token/timing totals, and worst cases
- **Comparison JSON**: Schema detecting regressions (decreased pass rate), improvements (increased pass rate), unchanged cases, and percentage delta metrics

## Consequences

### Positive
- **Extensibility**: New assertion types added via pure function interface and registry without modifying core logic (satisfies curveball requirement)
- **Composability**: Complex validation built from primitive assertions with logical operators and structural matching
- **Determinism**: Pure functions ensure side-effect-free evaluation; deterministic output at temperature 0.0 (except timing)
- **Clear Semantics**: Unanimous flaky policy prevents silent degradation; fenced-JSON consistency avoids confusion
- **Actionable Feedback**: Detailed failure information (expectation, actual, measured value) enables rapid debugging
- **Cost Visibility**: Sum-based accounting makes cost-regressions visible in comparisons
- **Rich Reporting**: Detailed JSON and human-readable outputs support both machine processing and human consumption
- **Comparison Utility**: Clear detection of regressions/improvements enables prompt engineering iteration

### Negative
- **Performance Overhead**: Pure function composition and recursive evaluation may have slight performance cost vs. procedural chains
- **Learning Curve**: Users must learn assertion types and composition patterns
- **Complexity**: Composite assertions and nested structures increase mental model complexity
- **Strict Flaky Policy**: May be too strict for some use cases where occasional failures are acceptable
- **Sum-Based Metrics**: May emphasize total cost over per-execution efficiency in some contexts
- **Fenced-JSON Complexity**: Requires preprocessing to strip markers before JSON parsing
- **Regression Sensitivity**: May flag insignificant pass rate changes as regressions (e.g., 1.000 → 0.999)

## Alternatives Considered

- **Assertion Model**:
  - Procedural/imperative assertion chains
  - Why rejected: Would require significant refactoring to add nesting support (per curveball requirement)
  
- **Flaky Policy**:
  - Threshold-based (e.g., pass if ≥80% runs pass)
  - Majority-based or last-run-wins
  - Why rejected: Specification requires unanimity to prevent silent degradation; aligns with "7/10 passes is not passing" requirement
  
- **JSON Handling**:
  - Require strict JSON (no fencing)
  - Attempt parse-as-is, fall back to stripping on failure
  - Make fenced-JSON support configurable
  - Why rejected: Must ensure consistency between json_valid and json_field_equals per specification
  
- **Regression Definition**:
  - Only consider changes crossing pass/fail thresholds
  - Require minimum delta threshold or statistical significance
  - Why rejected: Would allow silent accuracy erosion; specification requires detection of any decrease
  
- **Cost Accounting**:
  - Report averages instead of sums
  - Report both sums and averages
  - Why rejected: Sums make cost-regressions visible; averages could hide regressions in successful cases
  
- **Assertion Types**:
  - Fewer, more primitive assertion types
  - Why rejected: Would require users to compose common patterns manually; specification requires specific types
  
- **Composition Approach**:
  - Configuration-driven assertions
  - Object-oriented assertion hierarchy
  - Why rejected: Pure function registry approach is simpler and more extensible for this use case
  
- **Reporting**:
  - Minimal JSON report with only totals
  - Different human-readable formats
  - Why rejected: Specification requires exact JSON schema and human-readable format for utility and compatibility

## References

- Feature Spec: specs/main/spec.md
- Implementation Plan: specs/main/plan.md
- Related ADRs: 1-Model-Interaction-Architecture
- Evaluator Evidence: