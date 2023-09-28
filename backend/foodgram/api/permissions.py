from rest_framework.permissions import IsAuthenticatedOrReadOnly


class UserPermissions(IsAuthenticatedOrReadOnly):

    def has_permission(self, request, view):
        if request.method in ['GET', 'POST']:
            return True

        return False