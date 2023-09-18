from rest_framework import viewsets, status
from rest_framework.response import Response

from users.models import User
from recipes.models import Tag, Ingredient, Recipe

from .serializers import UsersSerializer, TagSerializer, IngredientSerializer, RecipeCreateSerializer, RecipeReadSerializer
from .pagination import UsersPagination


class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UsersSerializer
    pagination_class = UsersPagination

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class TagViewSet(viewsets.ModelViewSet):  #ReadOnlyModelViewSet
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ModelViewSet):  #ReadOnlyModelViewSet
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return RecipeCreateSerializer
        else:
            return RecipeReadSerializer
