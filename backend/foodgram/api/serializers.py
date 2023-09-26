import base64
from django.core.validators import EmailValidator
from django.core.files.base import ContentFile
from rest_framework import serializers
from djoser.serializers import UserCreateSerializer
from rest_framework.generics import get_object_or_404

from .validators import UnicodeUsernameValidator

from users.models import Subscription
from recipes.models import Tag, Ingredient, Recipe, RecipeIngredient, FavoriteRecipe, ShoppingCart


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
            'password',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')

        if request and request.method == 'GET':
            if request.user.is_authenticated:
                user = request.user
                data['is_subscribed'] = Subscription.objects.filter(user=user, author=instance).exists()
            else:
                data.pop('is_subscribed', None)

        return data


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
        read_only_fields = ('ingredient',)


class RecipeCreateSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    ingredients = RecipeIngredientSerializer(many=True, source='recipe_m2m')
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'name', 'image', 'text', 'cooking_time')

    def create(self, validated_data):
        ingredients = validated_data.pop('recipe_m2m')
        recipe = Recipe.objects.create(**validated_data)

        for ingredient in ingredients:
            current_ingredient = ingredient.get('ingredient')
            amount = ingredient.get('amount')
            recipe.ingredients.add(
                current_ingredient,
                through_defaults={
                    'amount': amount
                }
             )

        return recipe

    def to_representation(self, instance):
        request = self.context.get('request')
        user = request.user if request else None
        tags_info = TagSerializer(instance.tags.all(), many=True).data
        author_info = UsersSerializer(instance.author).data

        data = super().to_representation(instance)
        data['tags'] = tags_info
        data['author'] = author_info

        if user and user.is_authenticated:
            data['author']['is_subscribed'] = Subscription.objects.filter(user=user, author=instance.author).exists()

        return data


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UsersSerializer()
    ingredients = IngredientSerializer(many=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'name', 'image', 'text', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ('author', 'recipes', 'recipes_count', 'is_subscribed')

    def to_representation(self, instance):
        author = instance.author
        user = self.context['request'].user
        is_subscribed = Subscription.objects.filter(user=user, author=author).exists()

        data = {
            'email': author.email,
            'id': author.id,
            'username': author.username,
            'first_name': author.first_name,
            'last_name': author.last_name,
            'is_subscribed': is_subscribed,
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


class BaseRecipeSerializer(serializers.ModelSerializer):
    recipe = serializers.SerializerMethodField()

    class Meta:
        abstract = True

    def to_representation(self, instance):
        recipe = instance.recipe
        data = {
            'id': recipe.id,
            'name': recipe.name,
            'image': recipe.image.url,
            'cooking_time': recipe.cooking_time,
        }
        return data


class FavoriteRecipeSerializer(BaseRecipeSerializer):
    class Meta:
        model = FavoriteRecipe
        fields = ('recipe',)


class ShoppingCartSerializer(BaseRecipeSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('recipe',)
