from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from ..serializers.task import CreateTaskSerializer, \
    TaskCreatedResponseSerializer
from ...tasks import run_code


class CodeExecutionViewSet(viewsets.ViewSet):
    """
    Code Execution Tasks API

    This ViewSet exposes  endpoints to handel and manage code execution tasks.
    The execution is performed asynchronously via Celery.

    Endpoints
    ----------
        POST /tasks/create:
            Enqueue a new code-execution task. Returns a task id you can use to query
            status/results later


    """

    @action(detail=False, methods=["POST"], url_path="create")
    def create_new_task(self, request: Request) -> Response:
        """
        Enqueue a new code-execution task

        Request Body
        ------------
            programming_language (str) -> One of supported languages (python, javascript, php, c)
            source_code (str): The full source code to run/compile.

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
        - The actual execution result (stdout/stderr/return code) is not returned here.
        - After receiving the task_id fetch the results via /task_results/<task_id>. endpoint
        """
        serializer = CreateTaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        task = run_code.delay(data['programming_language'], data['source_code'])

        response = TaskCreatedResponseSerializer(
            {"task_id": task.id, "status": "accepted"})

        return Response(response.data, status=status.HTTP_202_ACCEPTED)
