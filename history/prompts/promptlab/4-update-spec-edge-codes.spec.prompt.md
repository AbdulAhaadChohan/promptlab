---
id: 4
title: Update SPEC.md for missing edge cases and exit code fix
stage: spec
date: 2026-09-16
surface: agent
model: nvidia_nim/nvidia/nemotron-3-super-120b-a12b
feature: promptlab
branch: main
user: mashhodagentic-lab
command: Updated SPEC.md with missing edge cases and exit code fix
labels: [specification, promptlab, edge-codes, exit-codes]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - SPEC.md
tests: 
- 

## Prompt

Please update my existing `SPEC.md` file to address missing edge cases and discrepancies. 

CRITICAL INSTRUCTIONS:
1. DO NOT break, overwrite, or simplify any of the existing behavior, schemas, CLI contracts, or architecture.
2. Add the missing edge-case specifications and fix the existing exit code discrepancy seamlessly into the document structure.

Here are the step-by-step additions and modifications required:

---

### Step 1: Fix Exit Code Discrepancy in Section 3.3 (Input Handling)
* Change the exit code for missing input/prompt files from Exit Code 3 to Exit Code 4 to match Section 2.4 and the Student Brief.
* Update Section 3.3 text to:
  "Missing input files or unreadable prompt files produce Exit Code 4 (Suite or report file unreadable) with a descriptive one-line message on stderr."

---

### Step 2: Add Parameter Validation & "runs: 0" Handling in Section 3.4 (Edge Cases in Suite Parsing)
Add the following points under Section 3.4:
* **Invalid Runs Value (`runs: 0` or negative)**: 
  "If `runs` in the suite file or passed via `--runs` is less than 1 (e.g., `runs: 0`), `promptlab` must reject the configuration immediately during validation, emit a single-line error to `stderr`, and exit with **Exit Code 1** (Bad usage / malformed input)."
* **Duplicate Case IDs**: 
  "If two or more cases in a suite share the same `id` string, suite validation must fail immediately, outputting a clear one-line error to `stderr`, and exit with **Exit Code 1**."
* **Unknown Assertion Types**: 
  "If a case contains an assertion with an unrecognized `type` string (e.g., not matching standard core, resource, or composite types), validation must fail immediately, emit a single-line error to `stderr`, and exit with **Exit Code 1**."

---

### Step 3: Add Exit Code Precedence Matrix to Section 2.4 (Exit Codes)
Add a clear priority hierarchy at the end of Section 2.4:
"**Exit Code Priority / Precedence Rule:**
When multiple execution errors or conditions occur simultaneously during a run, `promptlab` evaluates and exits using the highest-priority code in the following hierarchy:
1. **Exit Code 1**: Usage / CLI argument errors, malformed suite files, invalid regex, or unknown assertion types (Checked before execution).
2. **Exit Code 4**: Unreadable suite file, missing prompt file, missing input file, or unreadable report file (Checked during file resolution).
3. **Exit Code 3**: Model invocation failures (Model timeout >30s, non-zero subprocess exit, or executable missing).
4. **Exit Code 2**: One or more test cases failed or were marked flaky (Evaluation result).
5. **Exit Code 0**: All test cases passed successfully."

---

### Step 4: Expand Failure Schema for Composite Assertions in Section 7.2 & 5.4
Update Section 7.2 (`failures` array schema) and Section 5.4 to clarify nested assertion failure reporting:
* Specify that when a composite assertion (`all_of`, `any_of`) fails:
  - The top-level assertion object in `assertions` counts as 1 entry.
  - The `failures` array entry MUST detail the specific child assertion that caused the failure, including:
    - `assertion`: The specific child assertion object that failed.
    - `parent_type`: (Optional/Contextual) The type of composite wrapper (`all_of` / `any_of`).
    - `expected`: Expected value/rule of the failing child assertion.
    - `actual`: Truncated model output.
    - `measured_value`: Associated value if applicable.
    - `run_index`: The 0-based run index where the failure occurred.

## Response snapshot

Updated SPEC.md with the requested edge case specifications and exit code fixes:
1. Fixed Section 3.3: Changed exit code for missing input/prompt files from 3 to 4, updated description accordingly
2. Enhanced Section 3.4: Added validation for invalid runs value (<1), duplicate case IDs, and unknown assertion types - all resulting in exit code 1
3. Added Section 2.4: Exit code precedence matrix defining priority order for simultaneous errors
4. Updated Sections 5.4 and 7.2: Clarified failure reporting for composite assertions (all_of, any_of) to include child assertion details and parent type context

All changes were made without breaking existing behavior, schemas, CLI contracts, or architecture decisions. The updates address specific gaps while maintaining full backward compatibility with previously specified requirements.

## Outcome

- ✅ Impact: SPEC.md now includes comprehensive edge case handling and correct exit code behavior
- 🧪 Tests: No tests run (specification update work only)
- 📁 Files: Updated SPEC.md (approximately 19KB)
- 🔁 Next prompts: Begin implementation of promptlab CLI tool based on this fully compliant specification
- 🧠 Reflection: Successfully incorporated detailed technical requirements for edge cases and exit codes while preserving all existing specification integrity. The updates ensure robust error handling and clear failure reporting as required by the hackathon rules.

## Evaluation notes (flywheel)

- Failure modes observed: None - specification updates proceeded smoothly
- Grader results: Not applicable yet
- Prompt variant ID: Not applicable
- Next experiment: Implement the specification starting with CLI argument parsing and doctor command, then test suite parsing and model invocation with edge case validation