# Agent Execution Guide (`USAGE.md`)

This document is written specifically for autonomous AI agents executing or integrating with `promptlab`. It provides non-ambiguous CLI specifications, command choices, expected stdout/stderr output structures, and explicit exit-code remediation protocols.

---

## 1. Quick Capabilities Matrix

| Command | Purpose | When to Use | Primary Output |
| :--- | :--- | :--- | :--- |
| `python -m promptlab doctor` | Environment validation | Run first before any execution suite to verify tools. | Diagnostic report to stdout. |
| `python -m promptlab run` | Execute test suite | Execute baseline or candidate prompts against test cases. | Detailed JSON report (`--out`) & summary (`--report`). |
| `python -m promptlab compare` | Delta evaluation | Compare baseline vs candidate JSON reports to measure regressions. | Differential JSON output (`--out`) & comparison summary. |

---

## 2. Command Specifications & Protocols

### A. Environment Check (`doctor`)
Use this command prior to invoking any test runner to verify that Python, the model binary, and required modules are fully functional.

```bash
python -m promptlab doctor