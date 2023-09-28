from rest_framework import permissions


class UserPermissions(permissions.IsAuthenticatedOrReadOnly):

    def has_permission(self, request, view):
        if request.method in ['GET', 'POST']:
            return True

        return False


class IsRecipeAuthorOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user
