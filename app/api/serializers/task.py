from rest_framework import serializers

LANG_CHOICES = ("python", "javascript", "c", "php")


class CreateTaskSerializer(serializers.Serializer):
    programming_language = serializers.ChoiceField(choices=LANG_CHOICES)
    source_code = serializers.CharField()


class TaskCreatedResponseSerializer(serializers.Serializer):
    task_id = serializers.CharField()
    status = serializers.CharField(default="accepted")
