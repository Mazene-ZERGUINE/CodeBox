import re
import uuid
from pathlib import Path
from typing import Any, Dict, List
from django.conf import settings
from celery import shared_task
from codeBox.apps import logger

from .services.paths_service import JobDir
from .services.lang_service import (
    Language,
    normalize_language,
    extract_extension,
    build_lang_command,
)
from .services.docker_service import (
    get_docker_run_command_ro,
    run_docker_command,
)

_OUT_PLACEHOLDER = re.compile(
    r"^OUT_(?:\{)?([A-Za-z0-9_-]+)(?:\})?\.([A-Za-z0-9.]+)$", re.IGNORECASE
)


@shared_task()
def run_code(programming_language: str, source_code: str) -> Dict[str, Any]:
    """
    Celery task: execute user-provided source code inside an isolated controlled and secure Docker container.

    - A fresh, per-job temporary directory is created on the host and mounted read-only
        at /sandbox inside the container.

    - All compilation artifacts and runtime temp files are written to /tmp inside the
        container, which is a tmpfs (RAM-backed) mount.


    The container is launched with strict limits (CPU, memory, pids) and no network.
    """
    unique_id = str(uuid.uuid4())

    try:
        lang: Language = normalize_language(programming_language)
    except ValueError as e:
        logger.error(f"Unsupported language: {programming_language}. {e}")
        return _normalize_result(
            {"error": "Unsupported programming language", "returncode": 2})

    # Prepare a per-job temp dir and write the source file
    job = JobDir()
    try:
        filename = f"main.{extract_extension(lang)}"
        job.write(filename, source_code)

        # Build the in-container command for this language
        lang_cmd = build_lang_command(lang, f"/sandbox/{filename}")

        # Build docker run command with a read-only bind mount for this job dir
        cmd = get_docker_run_command_ro(job_dir=str(job.path), lang_cmd=lang_cmd)

        # Execute with a strict timeout (seconds)
        result = run_docker_command(cmd, timeout=30)

        return _normalize_result(result)
    finally:
        #  cleanup after the execution
        try:
            job.cleanup()
        except Exception as e:
            logger.warning(f"JobDir cleanup failed for {unique_id}: {e}")


@shared_task()
def run_code_with_files(
    payload: Dict[str, Any],
    task_id: str | uuid.UUID
) -> Dict[str, Any]:
    """
    Execute user code that references files.

    payload:
      - `payload["source_code"]` has already had IN_/OUT_ placeholders replaced with
        *absolute host paths* under STORAGE_IN/STORAGE_OUT (your process_source_code did this).
      - We bind mount STORAGE_IN (RO) and STORAGE_OUT/<task_id> (RW) into the container **at the
        same absolute paths** so those paths resolve properly inside the container.

    Returns:
      {stdout, stderr, returncode, error, output_files}
    """
    try:
        lang: Language = normalize_language(payload["programming_language"])
    except Exception as e:
        logger.error(
            f"Unsupported programming language: {payload.get('programming_language')}. {e}")
        return _normalize_result(
            {"error": "Unsupported programming language", "returncode": 2})

    task_id_str = str(task_id)
    source_code: str = payload["source_code"]

    out_dir = Path(settings.STORAGE_OUT) / task_id_str
    out_dir.mkdir(parents=True, exist_ok=True)

    job = JobDir()
    try:
        filename = f"main.{extract_extension(lang)}"
        job.write(filename, source_code)

        lang_cmd = build_lang_command(lang, f"/sandbox/{filename}")

        cmd = get_docker_run_command_ro(job_dir=str(job.path), lang_cmd=lang_cmd)

        extra_mounts = [
            "--mount", (
                f"type=bind,"
                f"src={str(Path(settings.STORAGE_IN))},"
                f"dst={str(Path(settings.STORAGE_IN))},"
                f"ro,bind-propagation=rprivate"
            ),
            "--mount", (
                f"type=bind,"
                f"src={str(out_dir)},"
                f"dst={str(out_dir)},"
                f"bind-propagation=rprivate"
            ),
        ]

        insert_at = len(cmd) - (len(lang_cmd) + 1)
        cmd = cmd[:insert_at] + extra_mounts + cmd[insert_at:]

        result = run_docker_command(cmd, timeout=30)
        norm = _normalize_result(result)

        # just list all files under the job's out dir
        output_files = _collect_outputs(out_dir)

        norm["output_files"] = output_files
        return norm

    finally:
        try:
            job.cleanup()
        except Exception as e:
            logger.warning(f"JobDir cleanup failed for {task_id_str}: {e}")


def _collect_outputs(out_dir: Path) -> List[Dict[str, Any]]:
    """
    Return metadata for all files directly under `out_dir`.
    If you expect subfolders, switch to `rglob('*')` instead of `iterdir()`.
    """
    if not out_dir.exists():
        return []

    items: List[Dict[str, Any]] = []
    for p in sorted(out_dir.iterdir()):
        if not p.is_file():
            continue
        try:
            st = p.stat()
            items.append({"name": p.name, "path": str(p), "size": st.st_size})
        except Exception:
            items.append({"name": p.name, "path": str(p), "size": None})
    return items


def _normalize_result(res: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize any result dict coming from the Docker runner into the correct format and type.
    """
    return {
        "stdout": res.get("stdout", ""),
        "stderr": res.get("stderr", ""),
        "returncode": res.get("returncode", None),
        "error": res.get("error", None),
    }
