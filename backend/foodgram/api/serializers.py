import base64
from django.core.validators import EmailValidator
from django.core.files.base import ContentFile
from rest_framework import serializers
from djoser.serializers import UserCreateSerializer

from .validators import UnicodeUsernameValidator

from users.models import Subscription
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
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    ingredients = RecipeIngredientSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'name', 'image', 'text', 'cooking_time')

    def to_representation(self, instance):
        tags_info = TagSerializer(instance.tags.all(), many=True).data
        data = super().to_representation(instance)
        data['tags'] = tags_info
        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)

        for ingredient_data in ingredients_data:
            ingredient = ingredient_data['id']
            amount = ingredient_data['amount']

            print(f"Ingredient: {ingredient}, Amount: {amount}")

            RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredient, amount=amount)

        recipe.tags.set(tags_data)

        return recipe


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UsersSerializer()
    ingredients = IngredientSerializer(many=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'name', 'image', 'text', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    # is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ('author', 'recipes', 'recipes_count')

    def to_representation(self, instance):
        author = instance.author
        # user = self.context['request'].user

        data = {
            'email': author.email,
            'id': author.id,
            'username': author.username,
            'first_name': author.first_name,
            'last_name': author.last_name,
            # 'is_subscribed': user.is_authenticated and user.subscriptions.filter(author=author).exists(),
            'recipes': self.get_recipes(author),
            'recipes_count': Recipe.objects.filter(author=author).count()
        }
        return data

    def get_recipes(self, author):
        recipes = Recipe.objects.filter(author=author)
        return [
            {
                'id': recipe.id,
                'name': recipe.name,
                'image': recipe.image.url,
                'cooking_time': recipe.cooking_time,
            }
            for recipe in recipes
        ]


class SubSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('id', 'user', 'author')
