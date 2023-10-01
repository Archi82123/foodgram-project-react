from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView, DestroyAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend

from api.serializers import (UsersSerializer, TagSerializer,
                             IngredientSerializer, RecipeSerializer,
                             SubscriptionSerializer, FavoriteRecipeSerializer,
                             ShoppingCartSerializer, ChangePasswordSerializer)
from api.permissions import UserPermissions, IsRecipeAuthorOrReadOnly
from api.pagination import PageLimitPagination
from api.filters import RecipeFilter, IngredientFilter
from users.models import User, Subscription
from recipes.models import (Tag, Ingredient,
                            Recipe, FavoriteRecipe,
                            RecipeIngredient, ShoppingCart)

SHOPPING_LIST_FILE_TYPE = 'text/plain'


class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UsersSerializer
    pagination_class = PageLimitPagination

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def get_permissions(self):
        if self.action in ('create', 'list'):
            return (AllowAny(),)
        return (UserPermissions(),)

    @action(
        detail=False,
        methods=('GET',),
        url_path='me',
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=('GET',),
        url_path='subscriptions',
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        user = self.request.user
        subscriptions = user.follower.all()

        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = SubscriptionSerializer(
                page,
                many=True,
                context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(
            subscriptions,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=('POST',),
        url_path='set_password',
        permission_classes=(IsAuthenticated,)
    )
    def set_password(self, request):
        user = request.user
        serializer = ChangePasswordSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        current_password = (serializer
                            .validated_data.get('current_password'))
        new_password = serializer.validated_data.get('new_password')

        if not user.check_password(current_password):
            return Response(
                {'current_password': 'Введён неверный пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        return Response(
            {'detail': 'Пароль успешно изменен.'},
            status=status.HTTP_200_OK
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('-id')
    serializer_class = RecipeSerializer
    permission_classes = (IsRecipeAuthorOrReadOnly,)
    pagination_class = PageLimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True,
            methods=('POST', 'DELETE'),
            url_path='favorite',
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        favorite_recipe = (FavoriteRecipe.objects
                           .filter(user=user, recipe=recipe).first())

        if request.method == 'POST':
            if not favorite_recipe:
                favorite_recipe = (FavoriteRecipe.objects
                                   .create(user=user, recipe=recipe))
                serializer = FavoriteRecipeSerializer(favorite_recipe)
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {'detail': 'Рецепт уже в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.method == 'DELETE':
            if favorite_recipe:
                favorite_recipe.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'detail': 'Этого рецепта нет в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        url_path='shopping_cart',
        permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        cart_recipe = (ShoppingCart.objects
                       .filter(user=user, recipe=recipe).first())

        if request.method == 'POST':
            if not cart_recipe:
                cart_recipe = (ShoppingCart.objects
                               .create(user=user, recipe=recipe))
                serializer = ShoppingCartSerializer(cart_recipe)
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {'detail': 'Рецепт уже в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.method == 'DELETE':
            if cart_recipe:
                cart_recipe.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'detail': 'Этого рецепта нет в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=False,
        methods=('GET',),
        url_path='download_shopping_cart',
        permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, *args, **kwargs):
        user = self.request.user
        ingredients_total = (RecipeIngredient.objects
                             .filter(recipe__users_cart__user=user)
                             .values('ingredient__name',
                                     'ingredient__measurement_unit')
                             .annotate(total_amount=Sum('amount')))

        shopping_list = []
        for ingredient in ingredients_total:
            ingredient_name = ingredient['ingredient__name']
            ingredient_amount = ingredient['total_amount']
            ingredient_unit = ingredient['ingredient__measurement_unit']
            shopping_list.append(
                f'{ingredient_name} - {ingredient_amount} {ingredient_unit}'
            )

        shopping_list_text = 'Список покупок:\n\n' + '\n'.join(shopping_list)

        response = HttpResponse(shopping_list_text,
                                content_type=SHOPPING_LIST_FILE_TYPE)
        response['Content-Disposition'] = \
            f'attachment; 'f'filename="{settings.SHOPPING_LIST_FILENAME}"'

        return response


class SubscribeUserView(CreateAPIView, DestroyAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        author = get_object_or_404(User, id=kwargs.get('id'))

        if author == request.user:
            return Response(
                {'detail': 'Вы не можете подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if Subscription.objects.filter(
                user=request.user, author=author
        ).exists():
            return Response(
                {'detail': 'Вы уже подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription = Subscription.objects.create(
            user=request.user,
            author=author
        )
        serializer = self.get_serializer(
            subscription,
            context={'request': request}
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        author = get_object_or_404(User, id=kwargs.get('id'))
        subscription = Subscription.objects.filter(
            user=request.user, author=author
        ).first()

        if subscription:
            subscription.delete()
            return Response(
                {'detail': 'Вы успешно отписались от пользователя.'},
                status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                {'detail': 'Вы не подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
