"""Unit tests for suite parser."""
import unittest
import sys
import os
import tempfile
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from promptlab.suite_parser import load_suite

class TestSuiteParser(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.suite_dir = self.temp_dir.name

    def _write_suite(self, data, filename="suite.json"):
        path = os.path.join(self.suite_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return path

    def test_valid_suite(self):
        suite_data = {
            "name": "test-suite",
            "prompt_file": "prompt.txt",
            "model": {
                "temperature": 0.0,
                "max_tokens": 256
            },
            "runs": 1,
            "cases": [
                {
                    "id": "case1",
                    "input": "hello",
                    "assert": [
                        {"type": "contains", "value": "hello"}
                    ]
                }
            ]
        }
        prompt_path = os.path.join(self.suite_dir, "prompt.txt")
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write("prompt content")
        suite_path = self._write_suite(suite_data)
        # Should not raise
        suite = load_suite(suite_path)
        self.assertEqual(suite["name"], "test-suite")
        self.assertEqual(suite["prompt_file"], prompt_path)
        self.assertEqual(len(suite["cases"]), 1)

    def test_missing_prompt_file(self):
        suite_data = {
            "name": "test",
            "prompt_file": "missing.txt",
            "model": {"temperature": 0.0, "max_tokens": 256},
            "runs": 1,
            "cases": []
        }
        suite_path = self._write_suite(suite_data)
        with self.assertRaises(SystemExit) as cm:
            load_suite(suite_path)
        self.assertEqual(cm.exception.code, 4)  # unreadable file

    def test_invalid_runs(self):
        suite_data = {
            "name": "test",
            "prompt_file": "prompt.txt",
            "model": {"temperature": 0.0, "max_tokens": 256},
            "runs": 0,  # invalid
            "cases": []
        }
        prompt_path = os.path.join(self.suite_dir, "prompt.txt")
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write("prompt")
        suite_path = self._write_suite(suite_data)
        with self.assertRaises(SystemExit) as cm:
            load_suite(suite_path)
        self.assertEqual(cm.exception.code, 1)  # bad usage

    def test_duplicate_case_ids(self):
        suite_data = {
            "name": "test",
            "prompt_file": "prompt.txt",
            "model": {"temperature": 0.0, "max_tokens": 256},
            "runs": 1,
            "cases": [
                {"id": "dup", "input": "x", "assert": []},
                {"id": "dup", "input": "y", "assert": []}
            ]
        }
        prompt_path = os.path.join(self.suite_dir, "prompt.txt")
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write("prompt")
        suite_path = self._write_suite(suite_data)
        with self.assertRaises(SystemExit) as cm:
            load_suite(suite_path)
        self.assertEqual(cm.exception.code, 1)

    def test_unknown_assertion_type(self):
        suite_data = {
            "name": "test",
            "prompt_file": "prompt.txt",
            "model": {"temperature": 0.0, "max_tokens": 256},
            "runs": 1,
            "cases": [
                {"id": "c1", "input": "x", "assert": [{"type": "unknown", "value": "x"}]}
            ]
        }
        prompt_path = os.path.join(self.suite_dir, "prompt.txt")
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write("prompt")
        suite_path = self._write_suite(suite_data)
        with self.assertRaises(SystemExit) as cm:
            load_suite(suite_path)
        self.assertEqual(cm.exception.code, 1)

if __name__ == "__main__":
    unittest.main()