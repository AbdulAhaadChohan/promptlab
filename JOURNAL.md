# Engineering Journal (`JOURNAL.md`)

## Q1: Three Design Decisions Made and Rejected

1. **Made:** Renamed the root module from `src/` to `promptlab/`.
   * **Rejected Alternative:** Keeping code under a generic `src/` folder.
   * **Rationale:** Direct CLI execution (`python -m promptlab run...` and `python -m promptlab doctor`) failed when using `src/` due to package resolution issues. Standardizing on `promptlab/` with proper `__main__.py` entry points allowed seamless execution without requiring extra environment variables.

2. **Made:** Enforced strict JSON output parsing without markdown fences in prompt v2.
   * **Rejected Alternative:** Allowing raw output with arbitrary prose wrappers.
   * **Rationale:** Accepting unstructured prose led to frequent `json_valid` assertion failures across runs.

3. **Made:** Standardized execution logs and report artifact cleanup workflows.
   * **Rejected Alternative:** Accumulating multiple report output files dynamically without clear tracking.
   * **Rationale:** Stale files caused prompt hash mismatches during `promptlab compare` execution.

---

## Q2: Hardest Bug Hit and Root Cause

* **The Bug:** Trailing `Input:` markers at the end of prompt v2 templates caused the stub model to generate invalid markdown code blocks (` ```json `), failing `json_valid` and `json_field_equals` assertions on every run.
* **Root Cause & Resolution:** The model concatenated the trailing input text with raw response generation, breaking expected string formats. Resolving this required strict prompt-ending directives and refining prompt template boundaries.
* **Secondary File Management Issues:** Claude Code repeatedly generated files in incorrect directory structures and occasionally removed essential files during agentic tasks. This was resolved by implementing strict explicit path checks and restoring missing suite paths manually.

---

## Q3: Something Claude Code Got Confidently Wrong

* **Wrong Path Assumptions:** Claude Code consistently generated files in wrong target paths (e.g., placing test scripts outside `tests/` or misplacing runner modules).
* **Ignored Non-Determinism:** Claude Code treated non-deterministic execution outputs as simple binary Pass/Fail results. It completely ignored multi-run variance and temperature-driven flaky behavior (`0.0 < pass_rate < 1.0`), which had to be manually caught, constrained, and validated in the test runner harness.

---

## Q4: What You Would Do Differently With 4 Extra Hours

* **Terminal UI (TUI):** Build a rich, interactive terminal-based UI (using libraries like `rich` or `textual`) to display real-time test progress, side-by-side prompt comparisons, and colored metrics directly in the console for better user experience.

---

## Q5: Team Member Responsibilities

* **Whole Team Collaboration:** The entire team worked closely and collaboratively across all phases of the project — including designing the core CLI harness, implementing test assertions, writing unit test cases, tuning baseline vs candidate prompts, and verifying submission requirements.