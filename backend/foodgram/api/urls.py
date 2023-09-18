from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UsersViewSet, TagViewSet, IngredientViewSet, RecipeViewSet

router = DefaultRouter()
router.register('users', UsersViewSet, basename='user')
router.register('tags', TagViewSet, basename='tag')
router.register('ingredients', IngredientViewSet, basename='ingredient')
router.register('recipes', RecipeViewSet, basename='recipe')


urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
