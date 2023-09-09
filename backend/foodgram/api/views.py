from rest_framework import generics

from users.models import User
from .serializers import SignUpSerializer
from .pagination import SignUpPagination


class SignUpView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignUpSerializer
    pagination_class = SignUpPagination
