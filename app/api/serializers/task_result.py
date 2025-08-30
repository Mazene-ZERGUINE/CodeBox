from rest_framework import serializers
from celery import states


class OutputFileSerializer(serializers.Serializer):
    name = serializers.CharField()
    path = serializers.CharField()


class TaskResultPayloadSerializer(serializers.Serializer):
    stdout = serializers.CharField(allow_blank=True, default="")
    stderr = serializers.CharField(allow_blank=True, default="")
    returncode = serializers.IntegerField(required=False, allow_null=True)
    error = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    output_files = OutputFileSerializer(many=True, required=False)


class TaskResultSerializer(serializers.Serializer):
    task_id = serializers.CharField()
    status = serializers.ChoiceField(choices=list(states.ALL_STATES))
    result = TaskResultPayloadSerializer(required=True, allow_null=False)
