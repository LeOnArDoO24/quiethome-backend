from rest_framework import viewsets, mixins, permissions as drf_permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from http import HTTPStatus
from django.core.mail import send_mail

from core.permissions import IsHost, IsGuest
from .models import Booking
from .serializers import BookingSerializer, BookingCreateSerializer
from users.serializers import UserViewSerializer


class BookingViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [drf_permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return BookingCreateSerializer
        return BookingSerializer

    def get_queryset(self):
        user = self.request.user
        # Parametro opzionale — se as_host=true mostra prenotazioni ricevute
        # Default false — mostra sempre le prenotazioni fatte come guest
        as_host = self.request.query_params.get('as_host', 'false')

        # Swift non passa il parametro → vede prenotazioni fatte
        # React passa as_host=true → vede prenotazioni ricevute come host
        if as_host == 'true' and user.is_host:
            return Booking.objects.filter(room__property__host=user)

        # Default — prenotazioni fatte dall'utente come guest
        return Booking.objects.filter(guest=user)

    def create(self, request, *args, **kwargs):
        print("BODY RICEVUTO:", request.data)
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("ERRORI:", serializer.errors)
            return Response(serializer.errors, status=400)
        self.perform_create(serializer)
        # Usa BookingSerializer per la risposta completa
        return Response(BookingSerializer(serializer.instance).data, status=201)

    def perform_create(self, serializer):
        print("DATA RICEVUTA:", self.request.data)
        print("ERRORI SERIALIZER:", serializer.errors if not serializer.is_valid() else "nessuno")
        # Verifichiamo che l'utente non prenoti una propria stanza
        room = serializer.validated_data.get('room')
        if room.property.host == self.request.user:
            raise ValidationError({"error": "Non puoi prenotare una tua stanza"})

        # Salviamo la prenotazione associando il guest all'utente autenticato
        booking = serializer.save(guest=self.request.user)

        # Notifichiamo l'host via email
        host = room.property.host
        send_mail(
            "Nuova prenotazione",
            f"Ciao {host.username}, hai ricevuto una nuova prenotazione da "
            f"{self.request.user.username} per la stanza {room.name} "
            f"dal {booking.check_in} al {booking.check_out}.",
            "noreply@vacanze.com",
            [host.email],
            fail_silently=False,
        )

    @action(detail=True, methods=['patch'], url_path='confirm')
    def confirm(self, request, pk=None):
        """
        PATCH /bookings/{id}/confirm/
        Solo l'host può confermare una prenotazione
        """
        booking = self.get_object()

        # Verifichiamo che l'utente sia l'host della stanza
        if booking.room.property.host != request.user:
            raise ValidationError({"error": "Non sei l'host di questa prenotazione"})

        # Verifichiamo che la prenotazione sia in stato pending
        if booking.status != 'pending':
            raise ValidationError({"error": f"Non puoi confermare una prenotazione in stato {booking.status}"})

        booking.status = 'confirmed'
        booking.save(update_fields=['status'])

        # Notifichiamo il guest via email
        send_mail(
            "Prenotazione confermata",
            f"Ciao {booking.guest.username}, la tua prenotazione per la stanza "
            f"{booking.room.name} dal {booking.check_in} al {booking.check_out} "
            f"è stata confermata!",
            "noreply@vacanze.com",
            [booking.guest.email],
            fail_silently=False,
        )

        return Response(BookingSerializer(booking).data, status=HTTPStatus.OK)

    @action(detail=True, methods=['patch'], url_path='cancel')
    def cancel(self, request, pk=None):
        """
        PATCH /bookings/{id}/cancel/
        Sia l'host che il guest possono cancellare
        """
        booking = self.get_object()

        # Verifichiamo che l'utente sia l'host o il guest della prenotazione
        is_host = booking.room.property.host == request.user
        is_guest = booking.guest == request.user

        if not is_host and not is_guest:
            raise ValidationError({"error": "Non sei autorizzato a cancellare questa prenotazione"})

        # Non si può cancellare una prenotazione già cancellata
        if booking.status == 'cancelled':
            raise ValidationError({"error": "La prenotazione è già cancellata"})

        booking.status = 'cancelled'
        booking.save(update_fields=['status'])

        return Response(BookingSerializer(booking).data, status=HTTPStatus.OK)

    @action(detail=False, methods=['get'], url_path='my-bookings')
    def my_bookings(self, request):
        """
        GET /bookings/my-bookings/              → prenotazioni fatte come guest
        GET /bookings/my-bookings/?as_host=true → prenotazioni ricevute come host
        """
        bookings = self.get_queryset()
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data, status=HTTPStatus.OK)