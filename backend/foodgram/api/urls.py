from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import (UsersViewSet, TagViewSet,
                       IngredientViewSet, RecipeViewSet,
                       SubscribeUserView)

router = DefaultRouter()
router.register('users', UsersViewSet, basename='user')
router.register('tags', TagViewSet, basename='tag')
router.register('ingredients', IngredientViewSet, basename='ingredient')
router.register('recipes', RecipeViewSet, basename='recipe')


urlpatterns = (
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
    path(
        'users/<int:id>/subscribe/',
        SubscribeUserView.as_view(), name='subscribe-user'
    ),
)
