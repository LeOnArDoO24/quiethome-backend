from rest_framework import serializers
from .models import Review, HostReview
from users.serializers import UserViewSerializer
from properties.serializers import RoomSerializer


class ReviewSerializer(serializers.ModelSerializer):
    # Mostriamo i dettagli completi in lettura
    author_details = UserViewSerializer(source='author', read_only=True)
    room_details = RoomSerializer(source='room', read_only=True)

    class Meta:
        model = Review
        fields = [
            "id", "booking", "author_details", "room_details",
            "rating", "comment", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["id", "booking", "rating", "comment"]

    def validate(self, data):
        booking = data.get('booking')
        request = self.context.get('request')

        if booking.status != 'confirmed':
            raise serializers.ValidationError({
                "booking": "Puoi recensire solo prenotazioni confermate"
            })

        if booking.guest != request.user:
            raise serializers.ValidationError({
                "booking": "Non sei il guest di questa prenotazione"
            })

        if Review.objects.filter(booking=booking).exists():
            raise serializers.ValidationError({
                "booking": "Hai già recensito questa prenotazione"
            })

        return data

    def create(self, validated_data):
        booking = validated_data['booking']
        return Review.objects.create(
            **validated_data,
            room=booking.room,
            author=self.context['request'].user
        )


class ReviewUpdateSerializer(serializers.ModelSerializer):
    # Serializer per la modifica — solo rating e commento modificabili
    # Non si può cambiare la prenotazione o la stanza
    class Meta:
        model = Review
        fields = ["rating", "comment"]

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Il rating deve essere tra 1 e 5")
        return value


class HostReviewSerializer(serializers.ModelSerializer):
    author_details = UserViewSerializer(source='author', read_only=True)
    target_user_details = UserViewSerializer(source='target_user', read_only=True)

    class Meta:
        model = HostReview
        fields = [
            "id", "booking", "author_details", "target_user_details",
            "rating", "comment", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class HostReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HostReview
        fields = ["id", "booking", "rating", "comment"]

    def validate(self, data):
        booking = data.get('booking')
        request = self.context.get('request')

        if booking.status != 'confirmed':
            raise serializers.ValidationError({
                "booking": "Puoi recensire solo prenotazioni confermate"
            })

        if booking.room.property.host != request.user:
            raise serializers.ValidationError({
                "booking": "Non sei l'host di questa prenotazione"
            })

        if HostReview.objects.filter(booking=booking).exists():
            raise serializers.ValidationError({
                "booking": "Hai già recensito questo guest"
            })

        return data

    def create(self, validated_data):
        booking = validated_data['booking']
        return HostReview.objects.create(
            **validated_data,
            author=self.context['request'].user,
            target_user=booking.guest
        )