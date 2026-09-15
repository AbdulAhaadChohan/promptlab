# Claude Code Project Guidelines (`CLAUDE.md`)

This file provides architectural context, commands, and operational rules for Claude Code and AI agents working on `promptlab`.

---

## 1. Project Overview & Architecture

`promptlab` is a Python-based CLI evaluation harness for benchmarking LLM prompt changes across deterministic and non-deterministic test suites.

* **Root Module:** `promptlab/` (Executed via `python -m promptlab <command>`)
* **Test Suites:** `suites/` (JSON formats defining test cases and assertions)
* **Prompts:** `prompts/` (Raw text templates, e.g., `classify_v1.txt`, `classify_v2.txt`)
* **Reports:** `reports/` (Generated baseline, candidate, and delta JSON outputs)
* **Unit Tests:** `tests/` (Python `unittest` test suite)

---

## 2. Essential Commands

### Environment & Diagnostics
```bash
python -m promptlab doctor