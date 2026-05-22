from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """
    Permette l'accesso solo se request.user == obj.user
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsHost(BasePermission):
    """
    Permette l'accesso solo agli utenti con role == host
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "host"


class IsGuest(BasePermission):
    """
    Permette l'accesso solo agli utenti con role == guest
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "guest"