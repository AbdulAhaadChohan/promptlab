# promptlab Implementation Plan

## Architecture Overview

Based on the constitution and specification, promptlab will be implemented as a command-line tool with the following core components:

### 1. Core Components
- **CLI Parser**: Handles command-line arguments for `run`, `compare`, and `doctor` commands
- **Test Runner**: Executes test suites against model invocations
- **Assertion Engine**: Implements and evaluates all assertion types (core, resource, composite)
- **Flaky Detector**: Distinguishes pass/fail/flaky outcomes across multiple runs
- **Comparator**: Analyzes two reports to detect regressions, improvements, and changes
- **Doctor**: Validates environment and installation integrity
- **Reporter**: Generates machine-readable JSON reports and human-readable summaries

### 2. Data Flow
```
Suite File → [CLI Parser] → [Test Runner] 
                                → [Model Invoker (subprocess)] 
                                → [Assertion Engine] 
                                → [Flaky Detector] 
                                → [Reporter (JSON & Human-readable)]
                               ↑
                   [Comparator] ← [Reporter] (for compare command)
                               ↑
                   [Doctor] ← [Environment Validation]
```

## Implementation Approach

### Phase 1: Foundation (Weeks 1-2)
1. **CLI Infrastructure**
   - Implement argument parsing for all three commands
   - Establish exit code contract and precedence rules
   - Create basic project structure and entry point

2. **Subprocess Model Invoker**
   - Implement exact argument structure execution
   - Add 30-second timeout safeguard
   - Handle exit codes, exceptions, and timeouts
   - Route stderr/stdout appropriately

3. **Basic Suite Parser**
   - Parse and validate suite JSON structure
   - Handle edge cases (empty suites, empty assertions)
   - Validate input file paths relative to suite location

### Phase 2: Core Functionality (Weeks 3-4)
1. **Assertion Engine**
   - Implement pure function model for all assertion types
   - Create assertion registry for extensibility
   - Build core assertions: contains, not_contains, equals, matches, json_valid, json_field_equals
   - Implement resource assertions: max_tokens, finish_is
   - Develop composite assertions: all_of, any_of, json_subset

2. **Test Runner & Flaky Detector**
   - Execute cases N times (from --runs or suite runs)
   - Apply flaky policy (unanimity required)
   - Calculate pass rates and status determinations
   - Aggregate token and timing metrics

### Phase 3: Reporting & Comparison (Weeks 5-6)
1. **JSON Reporter**
   - Generate exact report schema as specified
   - Compute prompt_hash (first 12 chars of SHA-256)
   - Aggregate totals across cases and runs
   - Build per-case and per-assertion statistics

2. **Human-Readable Output**
   - Implement concise summary format
   - Route output according to stream routing rules
   - Format worst cases display

3. **Comparator**
   - Implement comparison JSON schema
   - Calculate pass_rate_change and percentage deltas
   - Classify cases as regressions, improvements, unchanged
   - Validate comparison prerequisites (same suite, settings, runs)

### Phase 4: Polish & Verification (Weeks 7-8)
1. **Doctor Command**
   - Environment validation (Python version, model binary)
   - Suite discoverability check
   - Assertion type registry verification
   - Exit with code 0 if all checks pass

2. **Error Handling & Edge Cases**
   - Invalid runs value (<1) validation
   - Duplicate case ID detection
   - Unknown assertion type rejection
   - Invalid regex preprocessing (for matches assertion)
   - Missing/unreadable file handling (Exit Code 4)

3. **Verification Suite**
   - Comprehensive unit test coverage
   - Fresh clone validation script
   - Spec compliance verification

## Technical Details

### Language & Dependencies
- **Language**: Python 3.10+ (standard library only)
- **No Third-Party Packages**: Pure stdlib implementation
- **Subprocess Usage**: `subprocess.run()` with timeout, not `Popen` or `call`

### Key Implementation Decisions
1. **Assertion Evaluation**
   - Pure functions returning `(bool, str, Any)`
   - Registry pattern for assertion type lookup
   - Recursive evaluation for composite assertions
   - No short-circuiting; all assertions evaluated per case

2. **Flaky Handling**
   - Pass/fail/flaky determined by run pass rate
   - Per-assertion pass/fail counts tracked
   - First failure captured for reporting (with run index)

3. **Reporting**
   - Totals use sums across runs (not averages)
   - Timing fields isolated: `wall_ms` (totals) and `tokens_out_avg` (cases)
   - Deterministic at temperature 0.0 (except timing fields)

4. **Comparison**
   - Baseline vs candidate pass rate deltas
   - Percentage changes for tokens_in, tokens_out, wall_ms
   - Clear classification of case outcomes
   - Warnings for mismatched prompt_hash or model settings

## Acceptance Criteria

### Definition of Done
- [ ] SPEC.md present in first commit with zero implementation code
- [ ] All EXIT CODE contracts honored with precedence rules
- [ ] Deterministic output at temperature 0.0 (byte-identical except timing)
- [ ] Flaky handling implements strict unanimity policy
- [ ] All eight base assertions + three composite assertions implemented
- [ ] Stream routing prevents stdout corruption
- [ ] Subprocess invocation uses exact argument structure
- [ ] 30-second timeout on model invocations
- [ ] Human-readable and JSON reports match exact schemas
- [ ] Comparator implements specified JSON output and rules
- [ ] Doctor command validates environment and installation
- [ ] Unit test suite covers all core functionality
- [ ] Fresh clone verification passes in under 5 minutes
- [ ] Required context artifacts present (CLAUDE.md, PROMPTS.md, etc.)

### Starter Verification (Must Pass in <5 Minutes)
1. `promptlab doctor` executes successfully (exit code 0)
2. `promptlab run --suite suites/smoke.json` completes without error
3. `python -m unittest` passes from fresh clone
- [ ] All tests must avoid direct dependencies on stubmodel.py

## Risk Mitigation

### Technical Risks
1. **Determinism Breach**
   - Mitigation: Isolate timing-sensitive code; audit all code paths for non-determinism
   - Validation: Run same suite twice at temp 0.0; diff output (should differ only in timing fields)

2. **Subprocess Hangs**
   - Mitigation: Strict 30-second timeout; proper exception handling
   - Validation: Test with hanging model binary; verify exit code 3

3. **Stream Routing Errors**
   - Mitigation: Comprehensive flag combination testing
   - Validation: All permutations of --out and --report flags

4. **Assertion Composition Complexity**
   - Mitigation: Pure function base; extensive unit tests for nesting
   - Validation: Deeply nested all_of/any_of/json_subset combinations

### Schedule Risks
1. **Scope Creep**
   - Mitigation: Strict adherence to SPEC.md; treat as immutable during implementation
   - Validation: Regular spec compliance checks

2. **Underestimating Edge Cases**
   - Mitigation: Exhaustive validation testing; property-based approaches where applicable
   - Validation: Fuzzing for malformed inputs; boundary value testing

## Dependencies & Interfaces

### Internal Interfaces
- CLI Parser ↔ Test Runner (configuration)
- Test Runner ↔ Model Invoker (execution requests)
- Test Runner ↔ Assertion Engine (evaluation requests)
- Assertion Engine ↔ Flaky Detector (run results)
- Test Runner ↔ Reporter (final results)
- Reporter ↔ Comparator (for compare command)

### External Interfaces
- Model Binary: Subprocess execution with defined CLI contract
- File System: Suite files, prompt files, input files (read-only)
- Standard Output/Error: JSON reports, human-readable summaries, error messages
- User Input: Command-line arguments and flags

## Success Metrics

### Functional Correctness
- 100% compliance with SPEC.md behaviors and contracts
- All exit codes used correctly with proper precedence
- Deterministic output verified at temperature 0.0
- Flaky classification matches unanimity policy
- All assertion types behave as specified
- Composite assertions evaluate correctly with nesting
- Reports match exact JSON schemas
- Human-readable output matches specified format
- Comparator output follows defined rules and classifications

### Quality Attributes
- No tracebacks reach user under any error condition
- Error messages are descriptive and actionable
- Performance acceptable for expected use cases
- Memory usage remains bounded
- Implementation follows constitution principles
- Code is maintainable and extensible

### Process Compliance
- Spec-first development maintained throughout
- Architecture decisions documented in ADRs
- Context artifacts created and maintained
- Unit test coverage meets or exceeds 80%
- All deliverables present in final submission