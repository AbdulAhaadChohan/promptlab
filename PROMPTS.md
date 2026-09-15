---

### **2. `PROMPTS.md` (Root directory me save karein)**

```markdown
# Top 5 Agent Interactions Log (`PROMPTS.md`)

This document records the top 5 key prompts issued during the development of `promptlab`, detailing the interaction, LLM response, adjustments made, and technical justification.

---

### Interaction 1: Core Harness Architecture Setup

* **Prompt Issued:**
  > "Create a Python CLI module structure named promptlab that supports doctor, run, and compare commands. Use standard library modules where possible."
* **Model Output:** Suggested creating a `src/` directory with a setup script.
* **Adjustment Made:** Rejected `src/` folder. Standardized structure directly under `promptlab/` with `__main__.py` entry points.
* **Rationale:** Direct execution via `python -m promptlab` was failing with module import errors when using `src/`.

---

### Interaction 2: Assertion Engine Logic

* **Prompt Issued:**
  > "Write assertion evaluators for json_valid and json_field_equals that handle LLM outputs containing markdown code fences."
* **Model Output:** Provided simple `json.loads()` validation logic.
* **Adjustment Made:** Implemented pre-parsing regex logic to strip leading/trailing code fences (` ```json ` and ` ``` `) before calling `json.loads()`.
* **Rationale:** Standard LLM completions often wrap output in markdown blocks, causing false negative assertion failures on `json_valid`.

---

### Interaction 3: Candidate Prompt Optimization (v2)

* **Prompt Issued:**
  > "Improve prompts/classify_v1.txt so that customer tickets are accurately classified into billing, technical, account, or unclear, returning strictly JSON."
* **Model Output:** Generated a long prompt template ending with `Input: {ticket_text}`.
* **Adjustment Made:** Removed trailing `Input:` markers from the base prompt text and explicitly added "No markdown formatting, no code blocks" directives.
* **Rationale:** Trailing `Input:` text caused stub model string concatenation bugs that injected raw code block fences, breaking assertion rules.

---

### Interaction 4: Handling Flaky & Non-Deterministic Tests

* **Prompt Issued:**
  > "How should the test runner handle test cases where pass_rate is between 0.0 and 1.0?"
* **Model Output:** Recommended marking any test case with at least 1 failure as a simple binary "FAILED".
* **Adjustment Made:** Created a dedicated `flaky` classification when `0.0 < pass_rate < 1.0` and set CLI Exit Code to `2`.
* **Rationale:** Non-deterministic prompt runs require clear differentiation between complete failure (0% pass rate) and temperature-driven variance (flaky pass rate).

---

### Interaction 5: Delta Comparison & Hash Mismatch Troubleshooting

* **Prompt Issued:**
  > "Write compare command logic to check pass rate delta between baseline.json and candidate.json."
* **Model Output:** Implemented basic JSON numerical subtraction without validating source prompt hashes.
* **Adjustment Made:** Added prompt hash verification step. If hashes match, print warning `Reports have different prompt hashes` or report zero delta change without crashing.
* **Rationale:** Ensured engine robustness against accidental self-comparisons or stale cached baseline files.