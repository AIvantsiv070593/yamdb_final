from rest_framework import permissions


class IsAdminPermission(permissions.BasePermission):
    """Set permission for users with role = admin.
    """
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return request.user.is_admin()


class ReadOnly(permissions.BasePermission):
    """ReadOnly classes was added to make sure that users without token
    can get genres/categories/titles data.
    """
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class IsOwner(permissions.BasePermission):
    """Set permission for users with role = admin, moderator
    or user = author.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated:
            return (
                obj.author == request.user
                or request.user.is_admin()
                or request.user.is_moderator()
            )
