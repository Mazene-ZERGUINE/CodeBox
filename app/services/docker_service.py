"""
Docker runner utilities for the sandboxed code executor (Option B: read-only bind mount).

This module is responsible for:
- Constructing a *hardened* `docker run` command that:
  * Disables networking
  * Uses a read-only root filesystem
  * Mounts a per-job host directory read-only at /sandbox
  * Provides a tmpfs at /tmp for compilation/runtime artifacts
  * Runs as an unprivileged user
  * Applies CPU/memory/pid limits and drops capabilities
- Executing that command with a timeout and returning a uniform result shape.
"""

import shlex
import subprocess
from typing import List, Dict, Any, Optional

from codeBox.apps import logger

# Docker image Name
IMAGE_NAME = "code_runner:latest"


def get_docker_run_command_ro(*, job_dir: str, lang_cmd: List[str]) -> List[str]:
    """
    Build a hardened 'docker run' command that:
      - Mounts a per-job directory read-only to /sandbox
      - Uses a read-only root filesystem
      - Provides a tmpfs /tmp for compilation/runtime artifacts
      - Disables networking
      - Drops capabilities and limits pids
      - Runs as an unprivileged user in /sandbox
    """
    return [
        "docker", "run", "--rm",
        "--cpus", "1.0",
        "--memory", "512m",
        "--memory-swap", "512m",
        "--pids-limit", "100",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--network", "none",
        "--read-only",
        "--mount", f"type=bind,src={job_dir},dst=/sandbox,ro,bind-propagation=rprivate",
        "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=64m",
        "--workdir", "/sandbox",
        "--user", "1000:1000",
        IMAGE_NAME,
        *lang_cmd,
    ]


def run_docker_command(cmd: List[str], timeout: int = 30) -> Dict[str, Any]:
    """
    Execute the docker command with a timeout and return a uniform dict.
    """
    try:
        logger.info(f"Executing: {shlex.join(cmd)}")
        cp = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        stdout = _truncate(cp.stdout or "")
        stderr = _truncate(cp.stderr or "")
        logger.info(
            f"Exit {cp.returncode}; stdout_len={len(stdout)} stderr_len={len(stderr)}")
        return {"stdout": stdout, "stderr": stderr, "returncode": cp.returncode}
    except subprocess.TimeoutExpired as e:
        logger.error(f"Execution time exceeded: {e}")
        return {"error": "Execution time exceeded", "stdout": "", "stderr": "",
                "returncode": None}
    except subprocess.CalledProcessError as e:
        logger.error(
            f"Subprocess error: {e}, stdout={len(e.stdout or '')}, stderr={len(e.stderr or '')}")
        return {
            "error": "Subprocess error",
            "stdout": _truncate(e.stdout or ""),
            "stderr": _truncate(e.stderr or ""),
            "returncode": e.returncode if hasattr(e, "returncode") else None,
        }
    except Exception as e:
        logger.exception(f"Unexpected error running docker: {e}")
        return {"error": "Unexpected error occurred", "stdout": "", "stderr": "",
                "returncode": None}


def _truncate(s: str, limit: int = 64_000) -> str:
    if s is None:
        return ""
    if len(s) > limit:
        return s[:limit] + "\n...[truncated]..."
    return s
