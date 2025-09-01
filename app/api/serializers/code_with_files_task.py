from rest_framework import serializers

LANG_CHOICES = ("python", "javascript", "c", "php")


class CodeWithFilesTaskSerializer(serializers.Serializer):
    programming_language = serializers.ChoiceField(choices=LANG_CHOICES)
    source_code = serializers.CharField()
    input_files = serializers.ListField(child=serializers.CharField(), allow_null=True)

    files = serializers.ListField(
        child=serializers.FileField(), allow_empty=True
    )
