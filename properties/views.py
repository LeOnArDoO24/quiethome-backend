from rest_framework import viewsets, mixins, permissions as drf_permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination #paginazione degli appartamenti
from http import HTTPStatus
from django.shortcuts import get_object_or_404
from bookings.models import Booking

from core.permissions import IsHost, IsOwner
from .models import Property, Room, RoomImage, Amenity
from .serializers import ( PropertySerializer, PropertyCreateSerializer, RoomSerializer, RoomCreateSerializer, AmenitySerializer, RoomImageSerializer )


class PropertyPagination(PageNumberPagination):
    page_size = 10

class AmenityViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    # Le amenities sono visibili a tutti ma solo gli admin le creano
    queryset = Amenity.objects.all()
    serializer_class = AmenitySerializer

    def get_permissions(self):
        if self.action == 'list':
            # Chiunque può vedere la lista delle amenities
            return [drf_permissions.AllowAny()]
        # Solo utenti autenticati possono creare amenities
        return [drf_permissions.IsAuthenticated()]


class PropertyViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    pagination_class = PropertyPagination
    queryset = Property.objects.all()

    def get_serializer_class(self):
        # In lettura mostriamo tutto, in scrittura solo i campi necessari
        if self.action in ['list', 'retrieve']:
            return PropertySerializer
        return PropertyCreateSerializer

    def get_permissions(self):
        # Chiunque può vedere le properties
        if self.action in ['list', 'retrieve']:
            return [drf_permissions.AllowAny()]
        # Solo gli host possono creare properties
        if self.action == 'create':
            return [drf_permissions.IsAuthenticated(), IsHost()]
        # Solo l'host proprietario può modificare o cancellare
        if self.action in ['update', 'partial_update', 'destroy']:
            return [drf_permissions.IsAuthenticated(), IsHost()]
        return [drf_permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        # Associamo automaticamente l'host alla property
        # L'utente autenticato diventa il proprietario
        serializer.save(host=self.request.user)

    def get_queryset(self):
        queryset = Property.objects.prefetch_related(
            'rooms',
            'rooms__images',
            'rooms__amenities'
        ).select_related('host') 
        #CAMBIATO QUI AL POSTO DI Property.all...
        city = self.request.query_params.get('city')
        if city:
            queryset = queryset.filter(city__icontains=city)
        # Filtro opzionale per country — GET /properties/?country=Italia
        country = self.request.query_params.get('country')
        if country:
            queryset = queryset.filter(country__icontains=country)
        return queryset

class RoomViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = RoomSerializer

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RoomCreateSerializer
        return RoomSerializer

    def get_permissions(self):
        # Chiunque può vedere le stanze e la disponibilità
        if self.action in ['list', 'retrieve', 'availability']:
            return [drf_permissions.AllowAny()]
        # Solo gli host possono gestire le stanze
        return [drf_permissions.IsAuthenticated(), IsHost()]

    def get_queryset(self):
        # Ritorniamo solo le stanze della property specificata nell'URL
        # /properties/{property_id}/rooms/
        property_id = self.kwargs.get('property_pk')
        return Room.objects.filter(property_id=property_id)

    def perform_create(self, serializer):
        # Recuperiamo la property dall'URL e la associamo alla stanza
        property_id = self.kwargs.get('property_pk')
        property = get_object_or_404(Property, id=property_id)

        # Verifichiamo che l'host sia il proprietario della property
        if property.host != self.request.user:
            raise ValidationError({"error": "Non sei il proprietario di questa property"})

        serializer.save(property=property)


    @action(detail=True, methods=['post'], url_path='images')
    def add_image(self, request, property_pk=None, pk=None):
        """
        POST /properties/{property_id}/rooms/{room_id}/images/
        Aggiunge un'immagine alla stanza
        """
        room = self.get_object()

        # Verifichiamo che l'host sia il proprietario
        if room.property.host != request.user:
            raise ValidationError({"error": "Non sei il proprietario di questa stanza"})

        # L'immagine arriva come file nel request
        image = request.FILES.get('image')
        if not image:
            raise ValidationError({"error": "Nessuna immagine fornita"})

        room_image = RoomImage.objects.create(room=room, image=image)
        return Response(
            RoomImageSerializer(room_image).data,
            status=HTTPStatus.CREATED
        )
    
    @action(detail=True, methods=['get'], url_path='availability')
    def availability(self, request, property_pk=None, pk=None):
        """
        GET /properties/{property_id}/rooms/{room_id}/availability/
        Ritorna le date occupate della stanza
        Parametri opzionali:
        - month: mese (1-12)
        - year: anno (es. 2026)
        """
        room = self.get_object()

        # Leggiamo i parametri opzionali dall'URL
        # Es. /availability/?month=6&year=2026
        month = request.query_params.get('month')
        year = request.query_params.get('year')

        # Prendiamo tutte le prenotazioni attive della stanza
        bookings = Booking.objects.filter(
            room=room,
            status__in=['pending', 'confirmed']
        )

        # Se specificati filtriamo per mese e anno
        if month and year:
            bookings = bookings.filter(
                check_in__year=year,
                check_in__month=month
            ) | bookings.filter(
                check_out__year=year,
                check_out__month=month
            )

        # Generiamo la lista di tutte le date occupate
        occupied_dates = []
        for booking in bookings:
            current_date = booking.check_in
            # Iteriamo ogni giorno tra check_in e check_out
            while current_date < booking.check_out:
                occupied_dates.append(current_date.strftime('%Y-%m-%d'))
                from datetime import timedelta
                current_date += timedelta(days=1)

        # Rimuoviamo duplicati e ordiniamo
        occupied_dates = sorted(list(set(occupied_dates)))

        return Response({
            "room_id": str(room.id),
            "room_name": room.name,
            "is_available": room.is_available,
            "occupied_dates": occupied_dates,
            "total_occupied_days": len(occupied_dates)
        }, status=HTTPStatus.OK)