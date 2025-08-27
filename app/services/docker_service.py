import subprocess

from codeBox.apps import logger
from .lang_service import Language, normalize_language

VENV_PATH = '/app/.venv/bin/python'


def get_docker_run_command(language, container_path, unique_id, resources_path):
    lang = normalize_language(language)

    common_args = [
        'docker', 'run', '--rm', '--cpus', '1.0', '--memory', '512m', '--memory-swap',
        '512m',
        '--pids-limit', '100', '--cap-drop', 'ALL', '--security-opt',
        'no-new-privileges',
        '-v', f'{resources_path}:/app/resources',
        '-v', f'/tmp/docker_temp_{unique_id}:/tmp'
    ]

    if lang is Language.python:
        return common_args + ['code_runner:latest', VENV_PATH, container_path]
    elif lang is Language.javascript:
        return common_args + ['code_runner:latest', 'node', container_path]
    elif lang is Language.php:
        return common_args + ['code_runner:latest', 'php', container_path]
    elif lang is Language.c:
        compiled_path = f'/app/resources/{language}/compiled_{unique_id}'
        compile_cmd = common_args + ['code_runner:latest', 'g++', container_path, '-o',
                                     compiled_path]
        compile_result = run_docker_command(compile_cmd)
        if compile_result.returncode != 0:
            logger.error(f'Error compiling C++ code: {compile_result.stderr}')
            return {"stdout": compile_result.stdout, "stderr": compile_result.stderr,
                    "returncode": compile_result.returncode}

        return common_args + ['code_runner:latest', compiled_path]
    else:
        logger.error(f'Unsupported programming language: {language}')
        return None


def run_docker_command(cmd: list[str]):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        logger.info(f'Command executed successfully: {cmd}')
        logger.info(f'stdout: {result.stdout}')
        logger.info(f'stderr: {result.stderr}')
        return result
    except subprocess.TimeoutExpired as e:
        logger.error(f'Execution time exceeded: {str(e)}, Command: {cmd}')
        return {'error': 'Execution time exceeded'}
    except subprocess.CalledProcessError as e:
        logger.error(
            f'Subprocess error: {str(e)}, stdout: {e.stdout}, stderr: {e.stderr}')
        return {'error': str(e)}
    except Exception as e:
        logger.error(f'Unexpected error: {str(e)}, Command: {cmd}')
        return {'error': 'Unexpected error occurred'}
