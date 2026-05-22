from rest_framework import serializers
from .models import Property, Room, RoomImage, Amenity


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ["id", "name", "icon_slug"]


class RoomImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomImage
        fields = ["id", "image"]


class RoomSerializer(serializers.ModelSerializer):
    # Mostriamo le immagini e le amenities direttamente nella stanza
    # invece di mostrare solo gli id
    images = RoomImageSerializer(many=True, read_only=True)
    amenities = AmenitySerializer(many=True, read_only=True)

    class Meta:
        model = Room
        fields = [
            "id", "name", "description", "price_per_night",
            "max_guests", "num_beds", "num_bathrooms",
            "room_type", "amenities", "images", "is_available",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RoomCreateSerializer(serializers.ModelSerializer):
    # Serializer separato per la creazione — accetta amenities come lista di id
    amenities = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Amenity.objects.all(),
        required=False
    )

    class Meta:
        model = Room
        fields = [
            "id", "name", "description", "price_per_night",
            "max_guests", "num_beds", "num_bathrooms",
            "room_type", "amenities", "is_available"
        ]


class PropertySerializer(serializers.ModelSerializer):
    # Mostriamo le stanze direttamente dentro la property
    rooms = RoomSerializer(many=True, read_only=True)
    # Mostriamo il nome dell'host invece del solo id
    host_username = serializers.CharField(source="host.username", read_only=True)

    class Meta:
        model = Property
        fields = [
            "id", "host_username", "name", "description",
            "address", "city", "country",
            "latitude", "longitude", "rooms",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "host_username", "created_at", "updated_at"]


class PropertyCreateSerializer(serializers.ModelSerializer):
    # Serializer per la creazione — non include rooms (si aggiungono dopo)
    class Meta:
        model = Property
        fields = [
            "id", "name", "description",
            "address", "city", "country",
            "latitude", "longitude"
        ]