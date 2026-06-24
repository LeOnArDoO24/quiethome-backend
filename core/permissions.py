from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """
    Permette l'accesso solo se request.user == obj.user
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsHost(BasePermission):
    """
    Permette l'accesso solo agli utenti con is_host == True
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_host


class IsGuest(BasePermission):
    """
    Permette l'accesso solo agli utenti con is_host == False
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and not request.user.is_host