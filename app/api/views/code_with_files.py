# app/api/views/code_with_files.py
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from ..serializers.code_with_files_task import CodeWithFilesTaskSerializer
from ...services.file_task_service import create_file_task
import logging

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
