import base64

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.validators import EmailValidator
from django.db import transaction
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers

from api.validators import UnicodeUsernameValidator
from recipes.models import (Tag, Ingredient, Recipe,
                            RecipeIngredient, FavoriteRecipe, ShoppingCart)
from users.models import User, Subscription

EMAIL_ERROR = {'email': 'Пользователь с такой почтой уже существует.'}
USERNAME_ERROR = {'username': 'Пользователь с таким именем уже существует.'}

DUPLICATE_INGREDIENT_ERROR = {'ingredients':
                              'Ингредиенты не могут повторяться.'}
AMOUNT_ERROR = {'amount': f'Количество ингредиента должно быть не более '
                          f'{settings.MAX_AMOUNT}.'}
COOKING_TIME_ERROR = 'Время приготовления дожно быть не более 24 часов'


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class UsersSerializer(UserCreateSerializer):
    id = serializers.ReadOnlyField()
    email = serializers.CharField(
        validators=(
            EmailValidator(),
        ),
        max_length=254,
        required=True
    )
    username = serializers.CharField(
        validators=(
            UnicodeUsernameValidator(),
        ),
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

    def validate(self, data):
        email = data.get('email')
        username = data.get('username')

        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError(EMAIL_ERROR)

        if username and User.objects.filter(username=username).exists():
            raise serializers.ValidationError(USERNAME_ERROR)

        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')

        if request and request.method != 'GET':
            return data
        if request.user.is_authenticated:
            user = request.user
            data['is_subscribed'] = Subscription.objects.filter(
                user=user, author=instance
            ).exists()
        else:
            data.pop('is_subscribed', None)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


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
        read_only_fields = ('id',)


class RecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = RecipeIngredientSerializer(
        many=True, source='recipes_ingredient'
    )
    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited'
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_cart'
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )
        read_only_fields = ('author',)

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('recipes_ingredient')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        for ingredient in ingredients:
            recipe.ingredients.add(
                ingredient.get('id'),
                through_defaults={
                    'amount': ingredient.get('amount')
                }
            )

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )

        tags = validated_data.get('tags')
        if tags:
            instance.tags.set(tags)

        ingredients = validated_data.get('recipes_ingredient')
        if ingredients:
            instance.recipes_ingredient.all().delete()
            for ingredient in ingredients:
                instance.ingredients.add(
                    ingredient.get('id'),
                    through_defaults={
                        'amount': ingredient.get('amount')
                    }
                )

        instance.save()
        return instance

    def get_is_favorited(self, instance):
        request = self.context.get('request')
        return FavoriteRecipe.objects.filter(
            user=request.user, recipe=instance
        ).exists()

    def get_is_in_shopping_cart(self, instance):
        request = self.context.get('request')
        return ShoppingCart.objects.filter(
            user=request.user, recipe=instance
        ).exists()

    def to_representation(self, instance):
        request = self.context.get('request')
        tags_info = TagSerializer(instance.tags.all(), many=True).data
        author_info = UsersSerializer(instance.author).data

        ingredients_info = []
        for ingredient in instance.ingredients.all():
            ingredient_data = {
                'id': ingredient.id,
                'name': ingredient.name,
                'measurement_unit': ingredient.measurement_unit,
                'amount': instance.recipes_ingredient.get(
                    ingredient=ingredient
                ).amount
            }
            ingredients_info.append(ingredient_data)

        data = super().to_representation(instance)
        data['tags'] = tags_info
        data['author'] = author_info
        data['ingredients'] = ingredients_info

        if request.user:
            data['author']['is_subscribed'] = Subscription.objects.filter(
                user=request.user, author=instance.author
            ).exists()

        return data

    def validate_cooking_time(self, value):
        if (value < settings.MIN_COOKING_TIME
                or value > settings.MAX_COOKING_TIME):
            raise serializers.ValidationError(COOKING_TIME_ERROR)
        return value

    def validate(self, data):
        ingredients = data.get('recipes_ingredient')
        ingredient_ids = set()

        for ingredient in ingredients:
            ingredient_id = ingredient.get('id')
            amount = ingredient.get('amount')
            if amount < settings.MIN_AMOUNT or amount > settings.MAX_AMOUNT:
                raise serializers.ValidationError(AMOUNT_ERROR)
            if ingredient_id in ingredient_ids:
                raise serializers.ValidationError(DUPLICATE_INGREDIENT_ERROR)
            ingredient_ids.add(ingredient_id)

        return data


class SubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = ('author', 'recipes', 'recipes_count', 'is_subscribed')

    def to_representation(self, instance):
        author = instance.author
        user = self.context['request'].user
        is_subscribed = (Subscription.objects
                         .filter(user=user, author=author).exists())

        recipes_limit = int(
            self.context['request'].query_params.get('recipes_limit', 5)
        )

        data = {
            'email': author.email,
            'id': author.id,
            'username': author.username,
            'first_name': author.first_name,
            'last_name': author.last_name,
            'is_subscribed': is_subscribed,
            'recipes': self.get_recipes(author, recipes_limit),
            'recipes_count': Recipe.objects.filter(author=author).count()
        }

        return data

    def get_recipes(self, author, recipes_limit):
        recipes = author.recipes.all()[:recipes_limit]
        return (
            {
                'id': recipe.id,
                'name': recipe.name,
                'image': recipe.image.url,
                'cooking_time': recipe.cooking_time,
            }
            for recipe in recipes
        )


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
