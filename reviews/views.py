from rest_framework import viewsets, mixins, permissions as drf_permissions
from rest_framework.exceptions import ValidationError
from http import HTTPStatus
from rest_framework.response import Response

from core.permissions import IsHost
from .models import Review, HostReview
from .serializers import (
    ReviewSerializer,
    ReviewCreateSerializer,
    HostReviewSerializer,
    HostReviewCreateSerializer
)


class ReviewViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    def get_serializer_class(self):
        if self.action == 'create':
            return ReviewCreateSerializer
        return ReviewSerializer

    def get_permissions(self):
        # Chiunque può leggere le recensioni
        if self.action in ['list', 'retrieve']:
            return [drf_permissions.AllowAny()]
        # Solo utenti autenticati possono creare recensioni
        return [drf_permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = Review.objects.all()
        # Filtro opzionale per stanza — GET /reviews/?room=uuid
        room_id = self.request.query_params.get('room')
        if room_id:
            queryset = queryset.filter(room_id=room_id)
        # Filtro opzionale per autore — GET /reviews/?author=uuid
        author_id = self.request.query_params.get('author')
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save()


class HostReviewViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    def get_serializer_class(self):
        if self.action == 'create':
            return HostReviewCreateSerializer
        return HostReviewSerializer

    def get_permissions(self):
        # Chiunque può leggere le recensioni degli host
        if self.action in ['list', 'retrieve']:
            return [drf_permissions.AllowAny()]
        # Solo gli host possono creare recensioni sui guest
        return [drf_permissions.IsAuthenticated(), IsHost()]

    def get_queryset(self):
        queryset = HostReview.objects.all()
        # Filtro per guest recensito — GET /host-reviews/?target=uuid
        target_id = self.request.query_params.get('target')
        if target_id:
            queryset = queryset.filter(target_user_id=target_id)
        # Filtro per autore — GET /host-reviews/?author=uuid
        author_id = self.request.query_params.get('author')
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save()