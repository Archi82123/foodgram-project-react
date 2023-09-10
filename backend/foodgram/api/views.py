from rest_framework import generics, viewsets

from users.models import User
from recipes.models import Tag
from .serializers import UsersSerializer, TagSerializer
from .pagination import UsersPagination


class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UsersSerializer
    pagination_class = UsersPagination

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
