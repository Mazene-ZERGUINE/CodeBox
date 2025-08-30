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
    parser_classes = [MultiPartParser, FormParser]

    @action(detail=False, methods=['POST'], url_path='create')
    def create_file_task(self, request: Request) -> Response:
        serializer = CodeWithFilesTaskSerializer(data=request.data)

        # Data validations
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




