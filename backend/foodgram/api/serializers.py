import base64
from django.core.validators import EmailValidator
from django.core.files.base import ContentFile
from rest_framework import serializers
from djoser.serializers import UserCreateSerializer

from .validators import UnicodeUsernameValidator

from users.models import User, Subscription
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

    def validate(self, data):
        email = data.get('email')
        username = data.get('username')

        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError({'email': 'Пользователь с такой почтой уже существует.'})

        if username and User.objects.filter(username=username).exists():
            raise serializers.ValidationError({'username': 'Пользователь с таким именем уже существует.'})

        return data

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


class RecipeCreateSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    ingredients = RecipeIngredientSerializer(many=True, source='recipes_ingredient')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited', 'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time')
        read_only_fields = ('author',)

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

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time', instance.cooking_time)

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
        user = request.user if request and request.user.is_authenticated else None
        return FavoriteRecipe.objects.filter(user=user, recipe=instance).exists()

    def get_is_in_shopping_cart(self, instance):
        request = self.context.get('request')
        user = request.user if request and request.user.is_authenticated else None
        return ShoppingCart.objects.filter(user=user, recipe=instance).exists()

    def to_representation(self, instance):
        request = self.context.get('request')
        user = request.user if request and request.user.is_authenticated else None
        tags_info = TagSerializer(instance.tags.all(), many=True).data
        author_info = UsersSerializer(instance.author).data

        ingredients_info = []
        for ingredient in instance.ingredients.all():
            ingredient_data = {
                'id': ingredient.id,
                'name': ingredient.name,
                'measurement_unit': ingredient.measurement_unit,
                'amount': instance.recipes_ingredient.get(ingredient=ingredient).amount
            }
            ingredients_info.append(ingredient_data)

        data = super().to_representation(instance)
        data['tags'] = tags_info
        data['author'] = author_info
        data['ingredients'] = ingredients_info

        if user:
            data['author']['is_subscribed'] = Subscription.objects.filter(user=user, author=instance.author).exists()

        return data


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

        recipes_limit = int(self.context['request'].query_params.get('recipes_limit', 5))

        data = {
            'email': author.email,
            'id': author.id,
            'username': author.username,
            'first_name': author.first_name,
            'last_name': author.last_name,
            'is_subscribed': is_subscribed,
            'recipes': self.get_recipes(author)[:recipes_limit],
            'recipes_count': Recipe.objects.filter(author=author).count()
        }

        return data

    def get_recipes(self, author):
        recipes = Recipe.objects.filter(author=author).order_by('-id')
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
