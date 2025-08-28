from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from ..serializers.code_with_files_task import CodeWithFilesTaskSerializer

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
            return Response(
                {"error": "Invalid Request: inconsistent uploaded vs declared files."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Uploading files to the storage/in directory


        return Response(status=status.HTTP_201_CREATED)
