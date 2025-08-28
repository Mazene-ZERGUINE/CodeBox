"""
Per-job filesystem utilities for the sandboxed code executor.

This module provides `JobDir`, a tiny helper that:
- Creates a *unique* temporary directory for each execution under a single allowed base
- Writes user source files safely within that directory (guards against path traversal).
- Cleans up the directory automatically.

"""

import os
import tempfile
from pathlib import Path
from typing import Union

from django.conf import settings


class JobDir:
    """
    Per-execution temporary directory under a single allowed base.
    Mounted read-only inside the container.
    Auto-cleaned on context exit or .cleanup().
    """
    def __init__(self) -> None:
        base = Path(settings.BASE_DIR).joinpath("..", "exec").resolve()
        base.mkdir(parents=True, exist_ok=True)

        # Create per-job temp dir inside allowed base
        self._td = tempfile.TemporaryDirectory(dir=str(base))
        self.path: Path = Path(self._td.name).resolve()

    def write(self, rel: Union[str, os.PathLike], content: str, mode: int = 0o644) -> str:
        p = (self.path / Path(rel)).resolve()
        if not str(p).startswith(str(self.path)):
            # Prevent path traversal outside the job dir
            raise ValueError("Attempted to write outside of the job directory.")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        os.chmod(p, mode)
        return str(p)

    def cleanup(self) -> None:
        self._td.cleanup()

    def __enter__(self) -> "JobDir":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.cleanup()
