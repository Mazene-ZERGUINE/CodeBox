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
from typing import Union, Iterable

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import logging
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import UploadedFile
from django.utils.text import get_valid_filename

logger = logging.getLogger(__name__)

fs_inbox = FileSystemStorage(location=str(settings.STORAGE_IN))


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

    def write(self, rel: Union[str, os.PathLike], content: str,
              mode: int = 0o644) -> str:
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


def ensure_storage_dir(path: Path, label: str) -> None:
    """
        Ensure `path` exists as a directory, is readable & writable.
        Logs whether it existed or was created.
        Raises ImproperlyConfigured on any failure (stops app startup).
        """
    path = Path(path)
    try:
        if path.exists():
            if not path.is_dir():
                raise ImproperlyConfigured(
                    f"{label} '{path}' exists but is not a directory.")

            logger.info("%s: directory exists at %s", label, path)
        else:
            path.mkdir(parents=True, exist_ok=False)

            logger.info("%s: directory created at %s", label, path)
        try:
            _ = list(path.iterdir())
        except Exception as e:
            raise ImproperlyConfigured(f"{label} '{path}' is not readable: {e}")

        try:
            with tempfile.NamedTemporaryFile(dir=path, prefix=".permcheck_",
                                             delete=True) as tmp:

                tmp.write(b"ok")
                tmp.flush()

            logger.info("%s: directory is writable.", label)
        except Exception as e:
            raise ImproperlyConfigured(f"{label} '{path}' is not writable: {e}")

    except Exception as exc:
        logger.exception("Failed to prepare %s at %s: %s", label, path, exc)
        raise


def save_task_files_in_storage(
    files: Iterable[UploadedFile],
    target_dir: str | Path
) -> None:
    for file in files:
        base_name = os.path.basename(file.name)
        safe_name = get_valid_filename(base_name)

        related_path = fs_inbox.get_available_name(os.path.join(target_dir, safe_name))
        fs_inbox.save(related_path, file)
