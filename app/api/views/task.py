from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from ..serializers.task import CreateTaskSerializer, \
    TaskCreatedResponseSerializer
from ...tasks import run_code


class SimpleTaskViewSet(viewsets.ViewSet):
    """
    POST /tasks/create
    """

    @action(detail=False, methods=["POST"], url_path="create")
    def create_new_task(self, request: Request) -> Response:
        serializer = CreateTaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        task = run_code.delay(data['programming_language'], data['source_code'])

        response = TaskCreatedResponseSerializer(
            {"task_id": task.id, "status": "accepted"})
        return Response(response.data, status=status.HTTP_202_ACCEPTED)
