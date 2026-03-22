from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=50)
    password = serializers.CharField(max_length=128)


class PasswordChangeSerializer(serializers.Serializer):
    currentPassword = serializers.CharField(max_length=128)
    newPassword = serializers.CharField(max_length=128)


class SessionSerializer(serializers.Serializer):
    sessionId = serializers.CharField()
    username = serializers.CharField()
    role = serializers.CharField()
    issuedAt = serializers.IntegerField()
    isCurrent = serializers.BooleanField(default=False)
