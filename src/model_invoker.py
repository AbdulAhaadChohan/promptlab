"""Subprocess model invoker with exact argument structure."""
import subprocess
import sys
import tempfile
import os
from typing import Tuple, Optional

def invoke_model(
    binary: str,
    prompt_file: str,
    input_content: str,
    temperature: float,
    max_tokens: int,
    timeout: int = 30,
) -> Tuple[int, str, str]:
    """
    Invoke model binary with exact argument structure:
    python <model_binary> --prompt <prompt_file> --input <input_file> --temperature <temp> --max-tokens <max_tokens>

    The input_content is written to a temporary file and its path is passed as --input.

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    # Write input_content to a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(input_content)
        input_file_path = f.name

    try:
        # Build command
        cmd = [
            sys.executable,  # use same python interpreter
            binary,
            "--prompt",
            prompt_file,
            "--input",
            input_file_path,
            "--temperature",
            str(temperature),
            "--max-tokens",
            str(max_tokens),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            # result.returncode is int
            return result.returncode, result.stdout, result.stderr
        except FileNotFoundError:
            # binary not found
            return 3, "", f"Model binary not found: {binary}"
        except subprocess.TimeoutExpired:
            return 3, "", f"Model invocation timeout after {timeout}s"
        except Exception as e:  # catch-all for other errors
            return 3, "", f"Model invocation failed: {e}"
    finally:
        # Clean up temp file
        try:
            os.unlink(input_file_path)
        except OSError:
            pass