from dataclasses import dataclass
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from ..serializers.code_with_files_task import CodeWithFilesTaskSerializer
import uuid
from ...services.paths_service import save_task_files_in_storage
from ...tasks import run_code_with_files
from ...services.lang_service import process_source_code

MAX_INPUT = 5
MAX_OUTPUT = 5


class CodeWithFilesViewSet(viewsets.ViewSet):
    parser_classes = [MultiPartParser, FormParser]

    @action(detail=False, methods=['POST'], url_path='create')
    def create_file_task(self, request: Request) -> Response:
        # Data Validations
        serializer = CodeWithFilesTaskSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        input_files = data['input_files'] or []
        print(input_files)
        output_files = data['output_files'] or []
        files = data['files'] or []

        """
        Files consistencies validations:

        - The input files declared in the 'input_files' array must be equals to the
        uploaded files

        - the output files and input files must not exceed the maximum amount allowed
        """
        if len(files) > MAX_INPUT or len(input_files) > MAX_INPUT:
            return Response(
                {"error": f"Invalid Request: inputs exceed maximum ({MAX_INPUT})."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(output_files) > MAX_OUTPUT:
            return Response(
                {"error": f"Invalid Request: outputs exceed maximum ({MAX_OUTPUT})."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if input_files and files and len(input_files) != len(files):
            print(len(input_files), len(files))
            return Response(
                {"error": "Invalid Request: inconsistent uploaded vs declared files."},
                status=status.HTTP_400_BAD_REQUEST
            )

        """
        Worker task where the task files are going to be stored inside the storage/in folder
        # NOTE: This is different from the celery task generated latter on
        """
        task_id = uuid.uuid4()
        target_dir = f"{task_id}/"

        # Uploading files to the storage/in directory
        save_task_files_in_storage(files=files, target_dir=target_dir)
        payload = {
            "programming_language": data["programming_language"],
            "source_code": data["source_code"],
            "input_files_array": data["input_files"] or [],
            "output_files_array": data["output_files"] or [],
        }

        source_code = process_source_code(payload['source_code'],
                                          payload['input_files_array'], task_id)
        print(source_code)
        # run_code_with_files.delay(payload=payload, task_id=task_id)

        return Response(status=status.HTTP_201_CREATED)
