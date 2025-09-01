from rest_framework import serializers

LANG_CHOICES = ("python", "javascript", "c", "php")


class CodeWithFilesTaskSerializer(serializers.Serializer):
    programming_language = serializers.ChoiceField(choices=LANG_CHOICES)
    source_code = serializers.CharField()
    input_files = serializers.ListField(
        child=serializers.CharField(),
        allow_null=True,
        allow_empty=True,
        required=False
    )

    files = serializers.ListField(
        child=serializers.FileField(), allow_empty=True, allow_null=True, required=False
    )
