import base64
from django.core.validators import EmailValidator
from django.core.files.base import ContentFile
from rest_framework import serializers
from djoser.serializers import UserCreateSerializer

from .validators import UnicodeUsernameValidator

from recipes.models import Tag, Ingredient, Recipe, RecipeIngredient


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class UsersSerializer(UserCreateSerializer):
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


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    ingredient = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = ('ingredient', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    # ingredients = RecipeIngredientSerializer(many=True, source='ingredients_used')
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'name', 'image', 'text', 'cooking_time')

    def to_representation(self, instance):
        tags_info = TagSerializer(instance.tags.all(), many=True).data
        data = super().to_representation(instance)
        data['tags'] = tags_info
        return data

    # def create(self, validated_data):
    #     ingredients = validated_data.pop('ingredients_used')
    #     recipes = Recipe.objects.create(**validated_data)
    #
    #     for ingredient in ingredients:
    #         current_ingredient = ingredient.get('ingredient')
    #         amount = ingredient.get('amount')
    #         recipes.ingredients.add(current_ingredient, through_defaults={'amount': amount})
    #
    #     return recipes


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)

    class Meta:
        model = Recipe
        fields = '__all__'
