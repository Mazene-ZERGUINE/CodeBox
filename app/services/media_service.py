# services/media_service.py
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
                    # writestr reads fully; acceptable for typical sizes. For huge files, switch to zf.open() + chunked writes.
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
