from rest_framework import serializers
from .models import Property, PropertyImage, Room, RoomImage, Amenity


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ["id", "name", "icon_slug"]


class RoomImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomImage
        fields = ["id", "image"]


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ["id", "image"]


class RoomSerializer(serializers.ModelSerializer):
    # Mostriamo le immagini e le amenities direttamente nella stanza
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
    # Mostriamo le stanze e le immagini direttamente dentro la property
    rooms = RoomSerializer(many=True, read_only=True)
    images = PropertyImageSerializer(many=True, read_only=True)
    # Mostriamo il nome dell'host invece del solo id
    host_username = serializers.CharField(source="host.username", read_only=True)
    # Rating medio calcolato da tutte le recensioni delle stanze della property
    # Restituisce None se non ci sono ancora recensioni
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            "id", "host_username", "name", "description",
            "address", "city", "country",
            "latitude", "longitude", "images", "rooms",
            "average_rating",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "host_username", "created_at", "updated_at"]

    def get_average_rating(self, obj):
        # Recuperiamo tutte le recensioni delle stanze di questa property
        # tramite la relazione room → reviews definita in reviews/models.py
        from reviews.models import Review
        reviews = Review.objects.filter(room__property=obj)
        if not reviews.exists():
            # Nessuna recensione — restituiamo None invece di 0
            return None
        # Calcoliamo la media e arrotondiamo a 1 decimale
        total = sum(r.rating for r in reviews)
        return round(total / reviews.count(), 1)


class PropertyCreateSerializer(serializers.ModelSerializer):
    # Serializer per la creazione — non include rooms e images (si aggiungono dopo)
    class Meta:
        model = Property
        fields = [
            "id", "name", "description",
            "address", "city", "country",
            "latitude", "longitude"
        ]