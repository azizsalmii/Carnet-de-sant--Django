from rest_framework import serializers

class ChestXRayInputSerializer(serializers.Serializer):
    image = serializers.CharField(help_text="Base64 string or absolute path to image")

class ChestXRayOutputSerializer(serializers.Serializer):
    predicted_class = serializers.CharField()
    probabilities = serializers.DictField(child=serializers.FloatField())
    latency_ms = serializers.FloatField()
