"""
Service layer for the “code-with-files” workflow.

This module orchestrates the end-to-end flow for executing user-provided source
code that references uploaded input files and declares expected output files.

Flow
----
1) Validate request limits and the consistency between declared `input_files`
   and actually uploaded `files`.
2) Persist uploaded files under `storage/in/<uuid4>/`.
3) Rewrite placeholders in the source code:
   - `IN_{i}` (1-based)           -> <STORAGE_IN>/<task_uuid>/<input_files[i-1]>
   - `OUT_{NAME}.EXT` ({} optional)-> <STORAGE_OUT>/<task_uuid>/<NAME.EXT>
   Then ensure no placeholders remain.
4) Enqueue a Celery task (`run_code_with_files`) with a JSON-serializable payload.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4
from ..tasks import run_code_with_files
from .paths_service import save_task_files_in_storage
from .lang_service import process_source_code, validate_processed_source_code

MAX_INPUT = 5
MAX_OUTPUT = 5


def create_file_task(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate, store files, rewrite source placeholders, and enqueue the execution task

    Returns
    -------
    Dict[str, Any]
        A small envelope with Celery metadata:
        {
            "task_id": str,   # Celery task id (NOT the storage/job UUID)
            "status": str,    # e.g., "PENDING"
        }

    Raises
    ------
    ValueError
        If limits are exceeded, declared vs uploaded files are inconsistent,
        or placeholders remain after processing.
    Exception
        Propagated from file storage or Celery in case of unexpected failures.


    Side Effects
    ------------
    - Persists uploaded files under `storage/in/<uuid4>/`.
    - Schedules a Celery task (`run_code_with_files`) with a JSON-safe payload.
    """
    input_files = data.get("input_files") or []
    output_files = data.get("output_files") or []
    files = data.get("files") or []

    _validate_files_limits(input_files, output_files, files)
    _validate_declared_vs_uploaded(input_files, files)

    task_uuid = uuid4()
    target_dir = f"{task_uuid}/"
    save_task_files_in_storage(files=files, target_dir=target_dir)

    processed_source = process_source_code(
        data["source_code"], input_files, task_uuid
    )
    validate_processed_source_code(processed_source)

    payload = {
        "programming_language": data["programming_language"],
        "source_code": processed_source,
        "input_files_array": input_files,
        "output_files_array": output_files,
    }
    async_res = run_code_with_files.delay(payload, str(task_uuid))

    return {"task_id": async_res.id, "status": async_res.status}


def _validate_files_limits(input_files, output_files, files) -> None:
    """
    Enforce global limits on the number of input and output files.

    Raises
    ------
    ValueError
         If the number of inputs or outputs exceeds the configured maximums.
    """

    if len(files) > MAX_INPUT or len(input_files) > MAX_INPUT:
        raise ValueError(f"Invalid Request: inputs exceed maximum ({MAX_INPUT}).")
    if len(output_files) > MAX_OUTPUT:
        raise ValueError(f"Invalid Request: outputs exceed maximum ({MAX_OUTPUT}).")


def _validate_declared_vs_uploaded(input_files, files) -> None:
    """
    Ensure declared input filenames match the uploaded files (by basename and count).

    Compares only basenames to avoid path traversal issues. Both count and set
    equality must match; order is validated indirectly via your later
    placeholder replacement (IN_{i} is position-based).
    """
    if input_files and files:
        if len(input_files) != len(files):
            raise ValueError(
                "Invalid Request: inconsistent uploaded vs declared files.")
        declared = {Path(n).name for n in input_files}
        uploaded = {Path(f.name).name for f in files}
        if declared != uploaded:
            raise ValueError(
                "Invalid Request: uploaded filenames don't match input_files.")
