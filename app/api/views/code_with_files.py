import json
from celery.result import AsyncResult, states
from django.http.response import Http404
from django_celery_results.models import TaskResult
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from ..serializers.code_with_files_task import CodeWithFilesTaskSerializer
from ...services.file_task_service import create_file_task
import logging
from ...services.paths_service import normalize_output_files, build_zip_filename
from ...services.media_service import stream_single_file, stream_zip

log = logging.getLogger(__name__)


class CodeWithFilesViewSet(viewsets.ViewSet):
    """
    File Tasks API ViewSet

    This ViewSet exposes  endpoints to handle files related code executions and output
    files downloads
    The execution is performed asynchronously via Celery
    Files are downloaded as single files and as zips

    Endpoints:
    ----------
        POST / /file_task/create
            - Generate a unique id for each task
            - Upload the used files in  /storage/in/<task_id> directory

            - Enqueue a new code-execution task. Returns a task id you can use to query
            status/results later

        GET /file_task/{task_id}/download
            Downloads the generated output files (if generated) of the passed task_id
            as a single file or as a zip if many files
    """
    parser_classes = [MultiPartParser, FormParser]

    @action(detail=False, methods=['POST'], url_path='create')
    def create_file_task(self, request: Request) -> Response:
        """
        Upload the resources files in /storage/in/<task_id> directory
        Enqueue a new code-execution task

        Request Body <formData>
        ------------
            programming_language (str) -> One of supported languages (python, javascript, php, c)
            source_code (str): The full source code to run/compile.
            input_files (list[str]): Array with the input file names
            files: list[File]: the uploaded files

        Returns
        -------
            202 Accepted:
                TaskCreatedResponseSerializer
                    - task_id (str): Celery task identifier.
                     - status (str): Always 'accepted' on success.

            400 Bad Request:
                If validation fails. (ex: Programming Language not supported)

        Notes
        ------
        - The files and the input_files array must be identical
        - the uploaded files must not exceed the MAX 5 files
        """
        serializer = CodeWithFilesTaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = create_file_task(serializer.validated_data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log.exception("create_file_task failed")

            return Response({"error": "Internal error"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(result, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["GET"], url_path="download")
    def download_file_task(self, request, pk=None):
        """
        Downloads the generated output files (if generated)

        Path Parameters
        ---------------
        task_id (str): Celery task identifier (provided here as `pk` by the router)

        Returns:
        --------
            200 OK:
                List of generated files {name: str, path: str}
        """
        if not pk:
            return Response({"error": "task_id is required"},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            task_result = TaskResult.objects.get(task_id=pk)

            results = task_result.result
            if isinstance(results, str):
                try:
                    results = json.loads(results)
                except json.JSONDecodeError:
                    results = {}

            files = results["output_files"] or []
            entries = normalize_output_files(files)

            if not entries:
                return Response({"error": "No output files"},
                                status=status.HTTP_404_NOT_FOUND)

            if len(entries) == 1:
                return stream_single_file(entries[0])

            zip_name = build_zip_filename(pk)
            return stream_zip(entries, zip_name)

        except TaskResult.DoesNotExist:
            res = AsyncResult(pk)
            if res.state in {states.PENDING, states.RECEIVED, states.STARTED,
                             states.RETRY}:
                return Response({"state": res.state}, status=status.HTTP_202_ACCEPTED)
            return Response({"error": "TaskResult does not exist"},
                            status=status.HTTP_404_NOT_FOUND)
        except Http404 as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
