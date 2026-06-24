from rest_framework import viewsets, mixins, permissions as drf_permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from http import HTTPStatus
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from bookings.models import Booking
import googlemaps

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
        # Recuperiamo indirizzo, città e paese per costruire la stringa da geocodificare
        address = serializer.validated_data.get('address', '')
        city = serializer.validated_data.get('city', '')
        country = serializer.validated_data.get('country', '')

        # Costruiamo l'indirizzo completo da mandare a Google Maps
        full_address = f"{address}, {city}, {country}"

        latitude = None
        longitude = None

        try:
            # Inizializziamo il client Google Maps con la chiave definita in settings.py
            gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)

            # Chiamiamo la Geocoding API con l'indirizzo completo
            result = gmaps.geocode(full_address)

            if result:
                # Estraiamo lat/long dal primo risultato restituito da Google
                location = result[0]['geometry']['location']
                latitude = location['lat']
                longitude = location['lng']
                print(f"Geocoding riuscito: {full_address} → {latitude}, {longitude}")
            else:
                # Nessun risultato trovato — salviamo senza coordinate
                print(f"Geocoding: nessun risultato per {full_address}")
        except Exception as e:
            # Se il geocoding fallisce per qualsiasi motivo (es. chiave non valida,
            # rete assente) salviamo comunque la property senza coordinate
            print(f"Geocoding error: {e}")

        # Associamo automaticamente l'host alla property e salviamo le coordinate
        serializer.save(
            host=self.request.user,
            latitude=latitude,
            longitude=longitude
        )

    def get_queryset(self):
        queryset = Property.objects.prefetch_related(
            'rooms',
            'rooms__images',
            'rooms__amenities'
        ).select_related('host')

        # Filtro per città — GET /properties/?city=Roma
        city = self.request.query_params.get('city')
        if city:
            queryset = queryset.filter(city__icontains=city)

        # Filtro per paese — GET /properties/?country=Italia
        country = self.request.query_params.get('country')
        if country:
            queryset = queryset.filter(country__icontains=country)

        # Filtro per nome property — GET /properties/?name=Villa
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)

        # Filtro per numero ospiti — GET /properties/?guests=2
        # Mostra solo properties che hanno almeno una stanza con max_guests >= guests
        guests = self.request.query_params.get('guests')
        if guests:
            try:
                guests = int(guests)
                queryset = queryset.filter(rooms__max_guests__gte=guests).distinct()
            except ValueError:
                pass

        # Filtro per date disponibili — GET /properties/?check_in=2026-07-01&check_out=2026-07-10
        # Mostra solo properties che hanno almeno una stanza libera in quel periodo
        check_in = self.request.query_params.get('check_in')
        check_out = self.request.query_params.get('check_out')
        if check_in and check_out:
            # Troviamo le stanze già prenotate in quel periodo
            booked_rooms = Booking.objects.filter(
                status__in=['pending', 'confirmed'],
                check_in__lt=check_out,
                check_out__gt=check_in
            ).values_list('room_id', flat=True)

            # Escludiamo le properties che non hanno stanze libere
            queryset = queryset.filter(
                rooms__is_available=True
            ).exclude(
                rooms__id__in=booked_rooms
            ).distinct()

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
        Ritorna le date divise per stato:
        - occupied_dates: prenotazioni di altri (pending o confirmed) → rosso
        - pending_dates: mie prenotazioni in attesa → giallo
        - my_dates: mie prenotazioni confermate → verde
        Parametri opzionali:
        - month: mese (1-12)
        - year: anno (es. 2026)
        """
        room = self.get_object()

        # SCADENZA AUTOMATICA PENDING — approccio lazy
        # Cancella automaticamente i pending più vecchi di 3 giorni
        # senza bisogno di task schedulati esterni (es. Celery)
        expiry_threshold = timezone.now() - timedelta(days=3)
        expired = Booking.objects.filter(
            room=room,
            status='pending',
            created_at__lt=expiry_threshold
        )
        if expired.exists():
            print(f"Scadenza automatica: {expired.count()} prenotazioni pending cancellate per {room.name}")
            expired.update(status='cancelled')

        # Leggiamo i parametri opzionali dall'URL
        # Es. /availability/?month=6&year=2026
        month = request.query_params.get('month')
        year = request.query_params.get('year')

        # Identifichiamo l'utente loggato (può essere anonimo)
        current_user = request.user if request.user.is_authenticated else None

        # Prendiamo tutte le prenotazioni attive della stanza
        all_bookings = Booking.objects.filter(
            room=room,
            status__in=['pending', 'confirmed']
        )

        # Se specificati filtriamo per mese e anno
        if month and year:
            all_bookings = all_bookings.filter(
                check_in__year=year,
                check_in__month=month
            ) | all_bookings.filter(
                check_out__year=year,
                check_out__month=month
            )

        # Funzione helper per generare lista di date da una prenotazione
        def get_dates(booking):
            dates = []
            current_date = booking.check_in
            while current_date < booking.check_out:
                dates.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)
            return dates

        occupied_dates = set()  # prenotazioni di altri (pending o confirmed) → rosso
        pending_dates = set()   # mie prenotazioni in attesa → giallo
        my_dates = set()        # mie prenotazioni confermate → verde

        for booking in all_bookings:
            dates = get_dates(booking)
            is_mine = current_user and booking.guest == current_user

            if is_mine and booking.status == 'confirmed':
                # Mie prenotazioni confermate — verde
                my_dates.update(dates)
            elif is_mine and booking.status == 'pending':
                # Mie prenotazioni in attesa di conferma — giallo
                pending_dates.update(dates)
            else:
                # Prenotazioni di altri (pending o confirmed) — rosso
                # Bloccano comunque la stanza indipendentemente dallo stato
                occupied_dates.update(dates)

        return Response({
            "room_id": str(room.id),
            "room_name": room.name,
            "is_available": room.is_available,
            # Prenotazioni di altri → rosso
            "occupied_dates": sorted(list(occupied_dates)),
            # Mie prenotazioni in attesa → giallo
            "pending_dates": sorted(list(pending_dates)),
            # Mie prenotazioni confermate → verde
            "my_dates": sorted(list(my_dates)),
            "total_occupied_days": len(occupied_dates) + len(pending_dates)
        }, status=HTTPStatus.OK)