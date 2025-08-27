import os
import re
from pathlib import Path

SAFE_UNIQUE_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def sanitize_unique_id(unique_id: str) -> str:
    if not SAFE_UNIQUE_ID_RE.match(unique_id or ""):
        raise ValueError("unique_id contains forbidden characters.")
    return unique_id


def ensure_safe_mount(source_path: str, allowed_base: str) -> str:
    src = Path(source_path).expanduser().resolve()
    base = Path(allowed_base).expanduser().resolve()
    if not src.exists() or not src.is_dir():
        raise ValueError(f"source_path must exist and be a directory: {src}")
    try:
        src.relative_to(base)
    except ValueError:
        raise ValueError(f"source_path {src} must be inside {base}")
    return str(src)
