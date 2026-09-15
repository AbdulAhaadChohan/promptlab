#!/usr/bin/env python3
"""
Stub model for testing promptlab.
Accepts the same command line interface as the real model:
    python stubmodel.py --prompt <prompt_file> --input <input_file> --temperature <temp> --max-tokens <max_tokens>
Outputs a JSON object with:
    {
        "output": "Stub model response",
        "tokens_in": 10,
        "tokens_out": 5,
        "finish": "stop",
        "latency_ms": 10
    }
"""
import argparse
import json
import sys
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True, help="Path to prompt file")
    parser.add_argument("--input", required=True, help="Path to input file")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=256)
    args = parser.parse_args()

    # Read prompt and input files (though we ignore content)
    try:
        with open(args.prompt, 'r', encoding='utf-8') as f:
            prompt_content = f.read()
    except OSError:
        prompt_content = ""
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            input_content = f.read()
    except OSError:
        input_content = ""

    # Produce deterministic output that contains "hello" to satisfy the example suite
    output_text = "hello"
    output = {
        "output": output_text,
        "tokens_in": len(prompt_content) // 4 + 1,  # rough estimate
        "tokens_out": len(output_text) // 4 + 1,
        "finish": "stop",
        "latency_ms": 10,
    }
    # Ensure tokens_out does not exceed max-tokens
    if output["tokens_out"] > args.max_tokens:
        output["tokens_out"] = args.max_tokens
        output["finish"] = "length"
    # Output JSON
    json.dump(output, sys.stdout)
    sys.stdout.write('\n')

if __name__ == "__main__":
    main()