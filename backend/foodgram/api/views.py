from rest_framework import viewsets, status
from django.shortcuts import get_object_or_404
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models import User, Subscription
from recipes.models import Tag, Ingredient, Recipe

from .serializers import UsersSerializer, TagSerializer, IngredientSerializer, RecipeCreateSerializer, RecipeReadSerializer, SubscriptionSerializer, SubSerializer
from .pagination import UsersPagination, RecipesPagination


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
    pagination_class = RecipesPagination

    def get_queryset(self):
        queryset = Recipe.objects.all()

        author_id = self.request.query_params.get('author')
        if author_id:
            author = get_object_or_404(User, id=author_id)
            queryset = queryset.filter(author=author)

        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__slug__in=tags)

        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return RecipeCreateSerializer
        else:
            return RecipeReadSerializer


class SubscribeUserView(CreateAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        author = get_object_or_404(User, id=kwargs.get('id'))

        if author == request.user:
            return Response({'detail': 'Вы не можете подписаться на самого себя.'}, status=status.HTTP_400_BAD_REQUEST)

        if Subscription.objects.filter(user=request.user, author=author).exists():
            return Response({'detail': 'Вы уже подписаны на этого пользователя.'}, status=status.HTTP_400_BAD_REQUEST)

        subscription = Subscription.objects.create(user=request.user, author=author)
        serializer = SubscriptionSerializer(subscription)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubSerializer
