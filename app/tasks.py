import os
import subprocess

from celery import shared_task
from .services.docker_service import get_docker_run_command, run_docker_command
from codeBox import settings
from .services.code_runner_service import extract_extension
import uuid

SOURCE_DIR_PATH = os.path.join(settings.BASE_DIR, '..', 'exec')


@shared_task()
def run_code(programming_language: str, source_code: str) -> dict[str, str]:
    unique_id = str(uuid.uuid4())
    code_extension = extract_extension(programming_language)
    temp_filename = os.path.join(SOURCE_DIR_PATH,
                                 f'{programming_language}/code_to_run_{unique_id}.{code_extension}')

    container_file_path = f'/app/resources/{programming_language}/code_to_run_{unique_id}.{code_extension}'

    os.makedirs(os.path.dirname(temp_filename), exist_ok=True)
    with open(temp_filename, 'w') as f:
        f.write(source_code)

    cmd = get_docker_run_command(programming_language, container_file_path, unique_id,
                                 SOURCE_DIR_PATH)
    if cmd is None:
        return {'error': 'Unsupported programming language'}

    result = run_docker_command(cmd)

    if os.path.exists(temp_filename):
        os.remove(temp_filename)

    return {"stdout": result.stdout, "sterr": result.stderr,
            "result": result.returncode} if isinstance(result,
                                                       subprocess.CompletedProcess) else result
