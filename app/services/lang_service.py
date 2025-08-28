"""
Language utilities for the sandboxed code runner.

This module provides:
- A normalized `Language` enum and alias resolution.
- Helpers to derive the correct source-file extension for each language.
- A factory that builds the in-container command to compile/run the user code.

notes
------------
- For interpreted languages (Python/JS/PHP), we directly invoke the interpreter.
- For compiled languages (C/C++), we compile to `/tmp` (tmpfs) and then execute
  the resulting binary in a single container invocation.
"""

from enum import Enum
from typing import List

# Path to the Python interpreter inside the runner image
# keeps the container base clean and avoids system Python errors
VENV_PATH = "/app/.venv/bin/python"


class Language(str, Enum):
    python = "python"
    javascript = "javascript"
    php = "php"
    c = "c"
    cpp = "cpp"

# This allows flexible inputs (e.g., "py", "python3", "node", "c++", etc.).
_ALIASES = {
    "py": "python",
    "python3": "python",

    "js": "javascript",
    "node": "javascript",
    "nodejs": "javascript",

    "c++": "cpp",
    "g++": "cpp",
    "cpp": "cpp",

    "gcc": "c",
}


def normalize_language(s: str) -> Language:
    """
    Convert a user provided language label into a  `Language` enum.
    """
    key = (s or "").strip().lower()
    key = _ALIASES.get(key, key)
    try:
        return Language(key)
    except ValueError:
        raise ValueError(f"Unsupported language: {s}")


def extract_extension(lang: Language) -> str:
    """
    Return the expected source file extension for the given language.

    Args:
        lang: Canonical language enum.

    Returns:
        The file extension without a leading dot (e.g., "py", "cpp").
    """

    return {
        Language.python: "py",
        Language.javascript: "js",
        Language.php: "php",
        Language.c: "c",
        Language.cpp: "cpp",
    }[lang]


def build_lang_command(lang: Language, source_path: str) -> List[str]:
    """
    Build the in-container argv to compile/run the user code.

    - `source_path` is the absolute path inside the container (e.g., "/sandbox/main.cpp").
    - For interpreted languages (Python/JS/PHP), we directly exec the interpreter.
    - For compiled languages (C/C++), we compile to `/tmp/main` and then execute it.
      `/tmp` is a tmpfs in the container (RAM-backed), so no artifacts touch the host.

    """
    if lang is Language.python:
        return [VENV_PATH, source_path]

    if lang is Language.javascript:
        return ["node", source_path]

    if lang is Language.php:
        return ["php", source_path]

    if lang is Language.c:
        # Compile in /tmp and run; single 'sh -lc' keeps it in one container
        return [
            "sh",
            "-lc",
            f"gcc {source_path} -O2 -std=c11 -o /tmp/main && /tmp/main",
        ]

    if lang is Language.cpp:
        return [
            "sh",
            "-lc",
            f"g++ {source_path} -O2 -std=c++17 -o /tmp/main && /tmp/main",
        ]

    # Should never happen due to normalization
    raise ValueError(f"Unsupported language: {lang}")
