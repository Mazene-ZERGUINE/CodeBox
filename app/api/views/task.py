from celery.result import AsyncResult
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from ..serializers.create_task import CreateTaskSerializer, \
    TaskCreatedResponseSerializer


class SimpleTaskViewSet(viewsets.ViewSet):
    """
    POST /tasks/create
    """

    @action(detail=False, methods=["POST"], url_path="create")
    def create_new_task(self, request: Request) -> Response:
        serializer = CreateTaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        print(serializer.validated_data)

        data = serializer.validated_data
        # task = run_code.delay(serializer.source_code, serializer.programming_language)

        response = TaskCreatedResponseSerializer(
            {"task_id": "task_id", "status": "accepted"})
        return Response(response.data, status=status.HTTP_202_ACCEPTED)
