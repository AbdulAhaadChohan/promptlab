"""Subprocess model invoker with exact argument structure."""
import subprocess
import sys
from typing import Tuple, Optional

def invoke_model(
    binary: str,
    prompt_file: str,
    input_file: str,
    temperature: float,
    max_tokens: int,
    timeout: int = 30,
) -> Tuple[int, str, str]:
    """
    Invoke model binary with exact argument structure:
    python <model_binary> --prompt <prompt_file> --input <resolved_input> --temperature <temp> --max-tokens <max_tokens>

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    # Build command
    cmd = [
        sys.executable,  # use same python interpreter
        binary,
        "--prompt",
        prompt_file,
        "--input",
        input_file,
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