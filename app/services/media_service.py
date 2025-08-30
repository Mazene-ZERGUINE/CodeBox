"""
This service provides utilities for streaming file downloads directly from
Django's default storage backend. It supports two main use cases:

1. **Single file download**
   - Ensures the file exists in storage.
   - Returns a `FileResponse` that streams the file to the client as an attachment.

2. **Multiple files as ZIP download**
   - Collects multiple storage entries (`OutputEntry` objects).
   - Builds a temporary ZIP archive using a spooled temporary file
     (kept in memory until it reaches 64MB, then written to disk).
   - Automatically inserts a `MISSING_FILES.txt` entry in the ZIP if some
     files are not found at download time.
   - Streams the ZIP archive back to the client as a downloadable response.

The service ensures efficient memory usage and avoids loading all files into
memory at once. It is intended for cases where users may request multiple
files for bulk download, such as exporting reports, datasets, or user uploads.
"""

from __future__ import annotations
from typing import Iterable, Tuple, List
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404, HttpResponse
import tempfile
import zipfile

from .paths_service import OutputEntry


def ensure_exists_or_404(path: str) -> None:
    if not default_storage.exists(path):
        raise Http404("File not found")


def stream_single_file(entry: OutputEntry) -> FileResponse:
    """
    Open a single file from storage and return a streaming FileResponse.
    """
    ensure_exists_or_404(entry.path)
    f = default_storage.open(entry.path, "rb")
    return FileResponse(f, as_attachment=True, filename=entry.arcname)


def build_zip_spooled(entries: Iterable[OutputEntry]) -> Tuple[
    tempfile.SpooledTemporaryFile, List[str]]:
    """
    Create a ZIP in a SpooledTemporaryFile from storage entries.
    Returns the spooled file (seeked to 0) and a list of 'missing' arcnames.
    """
    missing: List[str] = []
    spooled = tempfile.SpooledTemporaryFile(
        max_size=64 * 1024 * 1024)  # 64MB memory threshold

    with zipfile.ZipFile(spooled, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for e in entries:
            if default_storage.exists(e.path):
                with default_storage.open(e.path, "rb") as src:
                    zf.writestr(e.arcname, src.read())
            else:
                missing.append(e.arcname)

        if missing:
            note = "The following files were not found at download time:\n" + "\n".join(
                f"- {m}" for m in missing)
            zf.writestr("MISSING_FILES.txt", note)

    spooled.seek(0)
    return spooled, missing


def stream_zip(entries: Iterable[OutputEntry], zip_name: str) -> FileResponse:
    """
    Build a ZIP (spooled) and return as FileResponse.
    """
    spooled, _missing = build_zip_spooled(entries)
    return FileResponse(spooled, as_attachment=True, filename=zip_name)
