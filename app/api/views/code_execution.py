import json
from celery.result import AsyncResult
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from ..serializers.task import CreateTaskSerializer, \
    TaskCreatedResponseSerializer
from ...tasks import run_code
from django_celery_results.models import TaskResult
from celery import states
from ..serializers.task_result import TaskResultSerializer, TaskResultPayloadSerializer


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

        GET / task_result
            Fetch the result of a task returns the task result (stdout, stderr, returncode)
            when complete or the task status if pending, failed or rejected


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

    @action(detail=True, methods=["GET"], url_path="task_result")
    def task_result(self, request: Request, pk=None) -> Response:
        """
        Fetch the status/result of a code-execution task.

        Path Parameters
        ---------------
        task_id (str): Celery task identifier (provided here as `pk` by the router).

        Returns
        -------
        200 OK
            TaskResultSerializer
              - task_id (str)
              - status (str): e.g., SUCCESS, FAILURE, REVOKED...
              - result (TaskResultPayload)
                  - stdout (str)
                  - stderr (str)
                  - returncode (int | null)
                  - error (str | null)

        202 Accepted
            {"state": "PENDING" | "RECEIVED" | "STARTED" | "RETRY"}

        404 Not Found
            {"error": "TaskResult does not exist"}

        400 Bad Request
            {"error": "task_id is required"}
        """
        if not pk:
            return Response({"error": "task_id is required"},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            task_result = TaskResult.objects.get(task_id=pk)
        except TaskResult.DoesNotExist:
            res = AsyncResult(pk)
            if res.state in {states.PENDING, states.RECEIVED, states.STARTED,
                             states.RETRY}:
                return Response({"state": res.state}, status=status.HTTP_202_ACCEPTED)
            return Response({"error": "TaskResult does not exist"},
                            status=status.HTTP_404_NOT_FOUND)

        payload = task_result.result
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = {}

        if isinstance(payload, dict):
            if "stderr" not in payload and "sterr" in payload:
                payload["stderr"] = payload.pop("sterr")

        data = {
            "task_id": pk,
            "status": task_result.status,
            "result": payload or {},
        }

        return Response(TaskResultSerializer(instance=data).data,
                        status=status.HTTP_200_OK)
