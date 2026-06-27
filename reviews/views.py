from rest_framework import viewsets, mixins, permissions as drf_permissions
from rest_framework.exceptions import ValidationError
from http import HTTPStatus
from rest_framework.response import Response

from core.permissions import IsHost
from .models import Review, HostReview
from .serializers import (
    ReviewSerializer,
    ReviewCreateSerializer,
    ReviewUpdateSerializer,
    HostReviewSerializer,
    HostReviewCreateSerializer
)


class ReviewViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    def get_serializer_class(self):
        if self.action == 'create':
            return ReviewCreateSerializer
        # PATCH usa il serializer di aggiornamento — solo rating e commento
        if self.action in ['update', 'partial_update']:
            return ReviewUpdateSerializer
        return ReviewSerializer

    def get_permissions(self):
        # Chiunque può leggere le recensioni
        if self.action in ['list', 'retrieve']:
            return [drf_permissions.AllowAny()]
        # Solo utenti autenticati possono creare o modificare recensioni
        return [drf_permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = Review.objects.all()

        # Filtro opzionale per stanza — GET /reviews/guest-reviews/?room=uuid
        room_id = self.request.query_params.get('room')
        if room_id:
            queryset = queryset.filter(room_id=room_id)

        # Filtro opzionale per property — GET /reviews/guest-reviews/?property=uuid
        property_id = self.request.query_params.get('property')
        if property_id:
            queryset = queryset.filter(room__property_id=property_id)

        # Filtro opzionale per autore — GET /reviews/guest-reviews/?author=uuid
        author_id = self.request.query_params.get('author')
        if author_id:
            queryset = queryset.filter(author_id=author_id)

        return queryset

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        # Verifichiamo che solo l'autore possa modificare la sua recensione
        review = self.get_object()
        if review.author != self.request.user:
            raise ValidationError({"error": "Non puoi modificare la recensione di un altro utente"})
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
        if self.action in ['list', 'retrieve']:
            return [drf_permissions.AllowAny()]
        return [drf_permissions.IsAuthenticated(), IsHost()]

    def get_queryset(self):
        queryset = HostReview.objects.all()
        target_id = self.request.query_params.get('target')
        if target_id:
            queryset = queryset.filter(target_user_id=target_id)
        author_id = self.request.query_params.get('author')
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save()