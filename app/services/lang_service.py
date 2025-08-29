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
import re
from enum import Enum
from pathlib import Path
from typing import List
from django.conf import settings
import uuid

from django.utils.text import get_valid_filename

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


def process_source_code(
    source_code: str,
    input_files: list[str],
    task_id: uuid.UUID
) -> str:
    """
    Replaces:
      - IN_{i}  (i starts at 1)     -> <STORAGE_IN>/<task_id>/<input_files[i-1]>
      - OUT_{NAME}.EXT              -> <STORAGE_OUT>/<task_id>/<NAME.EXT>
    """
    input_files_dir = Path(settings.STORAGE_IN) / str(task_id)
    output_files_dir = Path(settings.STORAGE_OUT) / str(task_id)

    in_pat = re.compile(r"\bIN_(\d+)\b")

    def _replace_in(match: re.Match[str]) -> str:
        one_based = int(match.group(1))
        if one_based < 1:
            raise ValueError(
                f"Invalid placeholder {match.group(0)}: indices start at 1 (use IN_1, "
                f"IN_2, ...)."
            )
        idx = one_based - 1  # convert to 0-based
        if idx >= len(input_files):
            raise ValueError(
                f"Placeholder {match.group(0)} refers to index {one_based}, "
                f"but only {len(input_files)} input file(s) were provided. "
                f"Highest allowed is IN_{len(input_files)}."
            )
        file_name = Path(input_files[idx]).name  # sanitize
        in_path = str(input_files_dir / file_name)
        return _to_string(in_path)

    processed_source_code = in_pat.sub(_replace_in, source_code)

    out_pat = re.compile(r"OUT_(?:\{)?([A-Za-z0-9_\-]+)(?:\})?\.([A-Za-z0-9]+)")

    def _replace_out(m: re.Match[str]) -> str:
        name = get_valid_filename(m.group(1))
        ext = m.group(2)

        out_path = str(output_files_dir / f"{name.lower()}.{ext.lower()}")
        return _to_string(out_path)

    processed_source_code = out_pat.sub(_replace_out, processed_source_code)

    return processed_source_code


def _to_string(s: str) -> str:
    return f'"{s}"'
