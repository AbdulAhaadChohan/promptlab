# ADR-4: Measurement Quality

> **Scope**: Document decision clusters, not individual technology choices. Group related decisions that work together (e.g., "Frontend Stack" not separate ADRs for framework, styling, deployment).

- **Status:** Proposed
- **Date:** 2026-09-16
- **Feature:** main
- **Context:** Need to ensure that prompt engineering measurements are valid, reliable, and comparable across experiments to support honest assessment of improvement efforts and prevent self-deception through flawed metrics.

## Decision

- **Measurement Source**: All measurements must come exclusively from promptlab reports; no external measurements or estimations permitted for assessment
- **Comparison Controls**: Comparisons must use identical suite, model settings (temperature, max_tokens), and run counts to ensure validity
- **Accuracy Gain Metric**: Measured as the delta (difference) in pass_rate averaged across all cases between baseline and candidate
- **Cost Measurement**: Measured as percentage change in total tokens_in and total tokens_out between reports
- **Failed Experiment Requirement**: Documentation of at least one change that did not help is required as a graded component, ensuring honest assessment
- **Experimental Integrity**: Prohibits "cherry picking" favorable comparisons or changing experimental conditions mid-iteration

## Consequences

### Positive
- **Measurement Validity**: Ensures that reported improvements reflect actual changes in prompt effectiveness, not measurement artifacts
- **Experimental Consistency**: Controls for variables that could otherwise confound results (different suites, models, or run counts)
- **Clear Improvement Metric**: Pass_rate delta provides intuitive, interpretable measure of accuracy improvement
- **Cost Visibility**: Percentage-based cost changes enable understanding of tradeoffs between accuracy and resource usage
- **Honest Assessment**: Required failed experiment documentation prevents confirmation bias and promotes learning from failures
- **Reproducibility**: Strict controls enable others to replicate experiments and verify results
- **Anti-Gaming Measures**: Prevents manipulation of metrics through experimental design changes rather than actual prompt improvements

### Negative
- **Experimental Overhead**: Requires strict discipline to maintain identical conditions across experiments
- **Limited Flexibility**: Makes it difficult to explore certain variations (e.g., different temperatures) without invalidating comparisons
- **Metric Selection Constraints**: May not capture all dimensions of prompt quality that stakeholders care about
- **Percentage Cost Complexity**: Percentage changes can be misleading when baseline values are very small or zero
- **Averaging Limitations**: Case-averaged pass_rate delta may hide important variations in specific case types
- **Failed Experiment Barrier**: Psychological difficulty of documenting failures may lead to superficial compliance rather than genuine learning
- **Measurement Latency**: Waiting for full experimental compliance may slow down rapid iteration cycles

## Alternatives Considered

- **Measurement Sources**:
  - Allow external measurements or estimations alongside promptlab reports
  - Why rejected: Would introduce uncontrolled variables and potential for self-deception or measurement bias
  
- **Comparison Controls**:
  - Allow varying some parameters (e.g., run counts) with statistical adjustments
  - Why rejected: Increases complexity and reduces certainty; specification requires strict controls for validity
  
- **Accuracy Metrics**:
  - Use different aggregation methods (median, weighted average)
  - Measure improvements per-case rather than averaged
  - Use alternative metrics like F1-score or AUC for specific case types
  - Why rejected: Pass_rate delta averaged across cases is simple, interpretable, and aligns with specification
  
- **Cost Measurement**:
  - Use absolute changes rather than percentages
  - Measure cost per-case or per-run instead of totals
  - Include additional cost factors (memory, storage, etc.)
  - Why rejected: Percentage change in totals is simple and specification-compliant; absolute changes less meaningful across different scales
  
- **Failed Experiment Handling**:
  - Make failed experiment documentation optional
  - Allow multiple failed experiments or none if all changes helped
  - Why rejected: Specification requires honest assessment; expecting all changes to help is unrealistic and prevents learning
  
- **Experimental Flexibility**:
  - More lenient controls on what must stay constant between experiments
  - Why rejected: Would threaten validity of comparisons and enable measurement manipulation

## References

- Feature Spec: specs/main/spec.md
- Implementation Plan: specs/main/plan.md
- Related ADRs: 1-Model-Interaction-Architecture, 2-Assertion-and-Evaluation-Architecture, 3-Determinism-and-Reliability
- Evaluator Evidence: