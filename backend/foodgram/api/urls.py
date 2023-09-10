from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UsersViewSet, TagViewSet

router = DefaultRouter()
router.register('users', UsersViewSet, basename='user')
router.register('tags', TagViewSet, basename='tag')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
