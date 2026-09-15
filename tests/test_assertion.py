"""Unit tests for assertion engine."""
import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from promptlab.assertion_engine import (
    assert_contains, assert_not_contains, assert_equals, assert_matches,
    assert_json_valid, assert_json_field_equals, assert_max_tokens,
    assert_finish_is, assert_all_of, assert_any_of, assert_json_subset,
    _dispatch_assertion
)

class TestAssertionEngine(unittest.TestCase):
    def setUp(self):
        self.base_output = {
            "output": "Hello world",
            "tokens_in": 10,
            "tokens_out": 5,
            "finish": "stop",
            "latency_ms": 100
        }

    def test_contains(self):
        passed, msg, val = assert_contains(self.base_output, {"value": "Hello", "ignore_case": False})
        self.assertTrue(passed)
        self.assertEqual(msg, "")
        self.assertIsNone(val)

        passed, msg, val = assert_contains(self.base_output, {"value": "hello", "ignore_case": True})
        self.assertTrue(passed)

        passed, msg, val = assert_contains(self.base_output, {"value": "xyz"})
        self.assertFalse(passed)
        self.assertIn("Expected substring", msg)

    def test_not_contains(self):
        passed, msg, val = assert_not_contains(self.base_output, {"value": "xyz"})
        self.assertTrue(passed)
        passed, msg, val = assert_not_contains(self.base_output, {"value": "Hello"})
        self.assertFalse(passed)

    def test_equals(self):
        passed, msg, val = assert_equals(self.base_output, {"value": "Hello world"})
        self.assertTrue(passed)
        # normalize only strips and collapses whitespace, does not change case
        passed, msg, val = assert_equals(self.base_output, {"value": "hello world", "normalize": True})
        self.assertFalse(passed)  # case-sensitive
        # Test whitespace normalization
        passed, msg, val = assert_equals(self.base_output, {"value": "Hello   world  ", "normalize": True})
        self.assertTrue(passed)
        passed, msg, val = assert_equals(self.base_output, {"value": "  Hello   world  ", "normalize": True})
        self.assertTrue(passed)
        # Test newline becomes space
        passed, msg, val = assert_equals(self.base_output, {"value": "Hello\nworld", "normalize": True})
        self.assertTrue(passed)
        passed, msg, val = assert_equals(self.base_output, {"value": "different"})
        self.assertFalse(passed)

    def test_matches(self):
        passed, msg, val = assert_matches(self.base_output, {"pattern": r"Hello.*"})
        self.assertTrue(passed)
        passed, msg, val = assert_matches(self.base_output, {"pattern": r"^Start"})
        self.assertFalse(passed)
        # invalid regex
        passed, msg, val = assert_matches(self.base_output, {"pattern": "*invalid"})
        self.assertFalse(passed)
        self.assertIn("Invalid regular expression", msg)

    def test_json_valid(self):
        out = {"output": '{"key": "value"}', "tokens_in": 0, "tokens_out": 0, "finish": "stop", "latency_ms": 0}
        passed, msg, val = assert_json_valid(out, {})
        print(f"plain JSON: passed={passed}, msg={msg}")
        self.assertTrue(passed)
        out2 = {"output": "not json", "tokens_in": 0, "tokens_out": 0, "finish": "stop", "latency_ms": 0}
        passed, msg, val = assert_json_valid(out2, {})
        print(f"not json: passed={passed}, msg={msg}")
        self.assertFalse(passed)
        self.assertIn("Output is not valid JSON", msg)

        # fenced JSON
        out3 = {'output': '```json\n{\"key\": \"value\"}\n```', 'tokens_in': 0, 'tokens_out': 0, 'finish': 'stop', 'latency_ms': 0}
        passed, msg, val = assert_json_valid(out3, {})
        print(f"fenced JSON: passed={passed}, msg={msg}")
        self.assertTrue(passed)

    def test_json_field_equals(self):
        out = {"output": '{"user": {"name": "Alice"}}', "tokens_in": 0, "tokens_out": 0, "finish": "stop", "latency_ms": 0}
        passed, msg, val = assert_json_field_equals(out, {"field": "user.name", "value": "Alice"})
        self.assertTrue(passed)
        passed, msg, val = assert_json_field_equals(out, {"field": "user.name", "value": "Bob"})
        self.assertFalse(passed)
        # missing field
        out2 = {"output": '{"age": 30}', "tokens_in": 0, "tokens_out": 0, "finish": "stop", "latency_ms": 0}
        passed, msg, val = assert_json_field_equals(out2, {"field": "user.name", "value": "Alice"})
        self.assertFalse(passed)
        self.assertIn("Field 'user.name' not found", msg)

    def test_max_tokens(self):
        out = {"output": "short", "tokens_in": 5, "tokens_out": 3, "finish": "stop", "latency_ms": 0}
        passed, msg, val = assert_max_tokens(out, {"value": 5})
        self.assertTrue(passed)
        passed, msg, val = assert_max_tokens(out, {"value": 2})
        self.assertFalse(passed)
        self.assertIn("tokens_out 3 exceeds maximum 2", msg)

    def test_finish_is(self):
        out = {"output": "done", "tokens_in": 5, "tokens_out": 3, "finish": "stop", "latency_ms": 0}
        passed, msg, val = assert_finish_is(out, {"value": "stop"})
        self.assertTrue(passed)
        passed, msg, val = assert_finish_is(out, {"value": "length"})
        self.assertFalse(passed)

    def test_all_of(self):
        out = {"output": "Hello world", "tokens_in": 10, "tokens_out": 5, "finish": "stop", "latency_ms": 0}
        passed, msg, val = assert_all_of(out, {
            "assertions": [
                {"type": "contains", "value": "Hello"},
                {"type": "equals", "value": "Hello world"}
            ]
        })
        self.assertTrue(passed)
        # one fails
        passed, msg, val = assert_all_of(out, {
            "assertions": [
                {"type": "contains", "value": "Hello"},
                {"type": "equals", "value": "Goodbye"}
            ]
        })
        self.assertFalse(passed)
        # The failure should be from the equals assertion
        self.assertIn("does not equal expected", msg)

    def test_any_of(self):
        out = {"output": "Hello", "tokens_in": 5, "tokens_out": 3, "finish": "stop", "latency_ms": 0}
        passed, msg, val = assert_any_of(out, {
            "assertions": [
                {"type": "equals", "value": "Hi"},
                {"type": "contains", "value": "Hell"}
            ]
        })
        self.assertTrue(passed)
        # none pass
        passed, msg, val = assert_any_of(out, {
            "assertions": [
                {"type": "equals", "value": "Hi"},
                {"type": "equals", "value": "Hey"}
            ]
        })
        self.assertFalse(passed)
        self.assertIn("None of the assertions", msg)

    def test_json_subset(self):
        out = {"output": '{"user": {"id": 1, "name": "Alice"}, "active": true}', "tokens_in": 0, "tokens_out": 0, "finish": "stop", "latency_ms": 0}
        subset = {"user": {"id": 1}, "active": True}
        passed, msg, val = assert_json_subset(out, {"subset": subset})
        self.assertTrue(passed)
        # wrong value
        subset2 = {"user": {"id": 2}}
        passed, msg, val = assert_json_subset(out, {"subset": subset2})
        self.assertFalse(passed)
        self.assertIn("Value mismatch", msg)

    def test_dispatch(self):
        # test that dispatch works for known types
        passed, msg, val = _dispatch_assertion(self.base_output, {"type": "contains", "value": "Hello"})
        self.assertTrue(passed)
        passed, msg, val = _dispatch_assertion(self.base_output, {"type": "unknown", "value": "x"})
        self.assertFalse(passed)
        self.assertIn("Unknown assertion type", msg)

if __name__ == "__main__":
    unittest.main()