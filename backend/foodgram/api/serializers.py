from django.core.validators import EmailValidator
from rest_framework import serializers
from djoser.serializers import UserCreateSerializer

from .validators import UnicodeUsernameValidator


class SignUpSerializer(UserCreateSerializer):
    """Сериализация для регистрации пользователя"""
    id = serializers.ReadOnlyField()
    email = serializers.CharField(
        validators=[
            EmailValidator(),
        ],
        max_length=254,
        required=True
    )
    username = serializers.CharField(
        validators=[
            UnicodeUsernameValidator(),
        ],
        max_length=150,
        required=True
    )
    first_name = serializers.CharField(
        max_length=150,
        required=True
    )
    last_name = serializers.CharField(
        max_length=150,
        required=True
    )
    password = serializers.CharField(
        max_length=150,
        required=True,
        write_only=True
    )

    class Meta(UserCreateSerializer.Meta):
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password'
        )
