from rest_framework import serializers
from .models import Booking
from properties.serializers import RoomSerializer
from users.serializers import UserViewSerializer
from django.utils import timezone


class BookingSerializer(serializers.ModelSerializer):
    # Mostriamo i dettagli completi della stanza e del guest in lettura
    room_details = RoomSerializer(source='room', read_only=True)
    guest_details = UserViewSerializer(source='guest', read_only=True)
    # Campo calcolato — True se esiste già una recensione per questa prenotazione
    # Permette all'app Swift di mostrare o nascondere il bottone "Lascia recensione"
    has_review = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "id", "room_details", "guest_details",
            "check_in", "check_out", "num_guests",
            "total_price", "status", "notes",
            "num_nights", "created_at", "updated_at",
            "has_review"
        ]
        read_only_fields = ["id", "total_price", "status", "created_at", "updated_at"]

    def get_has_review(self, obj):
        # Sfruttiamo la relazione OneToOne definita in Review.booking
        # hasattr restituisce True se esiste già una recensione collegata
        return hasattr(obj, 'review')


class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            "id", "room", "check_in", "check_out",
            "num_guests", "notes"
        ]

    def validate(self, data):
        room = data.get('room')
        check_in = data.get('check_in')
        check_out = data.get('check_out')
        num_guests = data.get('num_guests')

        # Verifichiamo che check_in non sia nel passato
        if check_in and check_in < timezone.now().date():
            raise serializers.ValidationError({"check_in": "La data di check-in non può essere nel passato"})

        # Verifichiamo che check_out sia dopo check_in
        if check_in and check_out and check_out <= check_in:
            raise serializers.ValidationError({"check_out": "La data di check-out deve essere successiva al check-in"})

        # Verifichiamo che la stanza sia disponibile
        if room and not room.is_available:
            raise serializers.ValidationError({"room": "La stanza non è disponibile"})

        # Verifichiamo che il numero di ospiti non superi il massimo
        if room and num_guests and num_guests > room.max_guests:
            raise serializers.ValidationError({
                "num_guests": f"Il numero massimo di ospiti per questa stanza è {room.max_guests}"
            })

        # Verifichiamo che non ci siano prenotazioni sovrapposte
        if room and check_in and check_out:
            overlapping = Booking.objects.filter(
                room=room,
                status__in=['pending', 'confirmed'],
                check_in__lt=check_out,
                check_out__gt=check_in
            ).exists()
            if overlapping:
                raise serializers.ValidationError({
                    "room": "La stanza è già prenotata per queste date"
                })

        return data

    def create(self, validated_data):
        room = validated_data['room']
        check_in = validated_data['check_in']
        check_out = validated_data['check_out']

        # Calcoliamo il prezzo totale al momento della creazione
        num_nights = (check_out - check_in).days
        total_price = room.price_per_night * num_nights

        return Booking.objects.create(
            **validated_data,
            total_price=total_price
        )