from rest_framework import serializers
from dataclasses import dataclass
import uuid

LANG_CHOICES = ("python", "javascript", "c", "php")


class CodeWithFilesTaskSerializer(serializers.Serializer):
    # Raw Data
    programming_language = serializers.ChoiceField(choices=LANG_CHOICES)
    source_code = serializers.CharField()
    input_files = serializers.ListField(child=serializers.CharField(), allow_null=True)
    output_files = serializers.ListField(child=serializers.CharField(), allow_null=True)

    # Uploaded Files
    files = serializers.ListField(
        child=serializers.FileField(), allow_empty=True
    )
