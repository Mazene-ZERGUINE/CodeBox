import uuid
from typing import Any, Dict

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
