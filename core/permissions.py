from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """
    Permette l'accesso solo se l'oggetto stesso è l'utente autenticato.
    Usata su viewset di User (es. UserModelView) dove obj È lo User,
    non ha un campo "user" al suo interno.
    """
    def has_object_permission(self, request, view, obj):
        return obj == request.user


class IsPropertyOwner(BasePermission):
    """
    Permette l'accesso solo all'host proprietario dell'oggetto.
    Funziona sia su Property (campo diretto `host`) sia su Room
    (proprietario raggiungibile tramite `room.property.host`).
    """
    def has_object_permission(self, request, view, obj):
        host = obj.host if hasattr(obj, 'host') else obj.property.host
        return host == request.user


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