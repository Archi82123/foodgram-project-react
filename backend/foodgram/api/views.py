from rest_framework import viewsets, status
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView, DestroyAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from users.models import User, Subscription
from recipes.models import Tag, Ingredient, Recipe, FavoriteRecipe

from .serializers import UsersSerializer, TagSerializer, IngredientSerializer, RecipeCreateSerializer, RecipeReadSerializer, SubscriptionSerializer, FavoriteRecipeSerializer
from .pagination import UsersPagination, RecipesPagination


class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UsersSerializer
    pagination_class = UsersPagination
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def get_permissions(self):
        if self.action in ['create', 'list']:
            return [AllowAny()]
        return super().get_permissions()

    @action(detail=False, methods=['GET'], url_path='me', permission_classes=[IsAuthenticated])
    def me(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'], url_path='subscriptions')
    def subscriptions(self, request):
        user = self.request.user
        subscriptions = Subscription.objects.filter(user=user)
        page = self.paginate_queryset(subscriptions)
        serializer = SubscriptionSerializer(subscriptions, many=True,
                                            context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['POST'], url_path='set_password', permission_classes=[IsAuthenticated])
    def set_password(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not user.check_password(current_password):
            return Response({'detail': 'Текущий пароль неверен.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({'detail': 'Пароль успешно изменен.'}, status=status.HTTP_200_OK)


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
        tags = self.request.query_params.getlist('tags')

        if author_id:
            author = get_object_or_404(User, id=author_id)
            queryset = queryset.filter(author=author)

        if tags:
            queryset = queryset.filter(tags__slug__in=tags)

        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return RecipeCreateSerializer
        else:
            return RecipeReadSerializer

    @action(detail=True, methods=['POST', 'DELETE'], url_path='favorite', permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        favorite_recipe = FavoriteRecipe.objects.filter(user=user, recipe=recipe).first()

        if request.method == 'POST':
            if not favorite_recipe:
                favorite_recipe = FavoriteRecipe.objects.create(user=user, recipe=recipe)
                serializer = FavoriteRecipeSerializer(favorite_recipe)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response({'detail': 'Рецепт уже в избранном'}, status=status.HTTP_400_BAD_REQUEST)
        if request.method == 'DELETE':
            if favorite_recipe:
                favorite_recipe.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'detail': 'Этого рецепта нет в избранном'}, status=status.HTTP_400_BAD_REQUEST)

class SubscribeUserView(CreateAPIView, DestroyAPIView):
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
        serializer = self.get_serializer(subscription, context={'request': request})

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        author = get_object_or_404(User, id=kwargs.get('id'))
        subscription = Subscription.objects.filter(user=request.user, author=author).first()

        if subscription:
            subscription.delete()
            return Response({'detail': 'Вы успешно отписались от пользователя.'}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'detail': 'Вы не подписаны на этого пользователя.'},
                            status=status.HTTP_400_BAD_REQUEST)
