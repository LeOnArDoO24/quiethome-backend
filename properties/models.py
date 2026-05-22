from django.db import models
from core.models import BaseModel
from users.models import User
from core.utils import validate_image_size
from django.core.validators import FileExtensionValidator


class Amenity(BaseModel):
    # Servizio offerto dalla stanza (wifi, parcheggio, cucina, ecc.)
    name = models.CharField(max_length=50)
    # Slug per il frontend (es. "wifi", "parking") — utile per mostrare icone
    icon_slug = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Amenities"


class Property(BaseModel):
    # Host proprietario della casa
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name="properties")
    name = models.CharField(max_length=100)
    description = models.TextField()
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    # Coordinate geografiche opzionali per mappe future
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.city}"

    class Meta:
        verbose_name_plural = "Properties"


class Room(BaseModel):
    ROOM_TYPE_CHOICES = [
        ('entire_place', 'Entire Place'),
        ('private_room', 'Private Room'),
        ('shared_room', 'Shared Room'),
    ]

    # Appartamento/stanza dentro una Property
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="rooms")
    name = models.CharField(max_length=100)
    description = models.TextField()
    price_per_night = models.DecimalField(max_digits=8, decimal_places=2)
    max_guests = models.PositiveIntegerField()
    num_beds = models.PositiveIntegerField()
    num_bathrooms = models.PositiveIntegerField()
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES, default='entire_place')
    # Relazione M2M — una stanza può avere più amenities e una amenity può essere in più stanze
    amenities = models.ManyToManyField(Amenity, blank=True, related_name="rooms")
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.property.name}"


class RoomImage(BaseModel):
    # Immagini della stanza — separato da Room per permettere più immagini
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="images")
    image = models.FileField(
        upload_to="rooms/",
        validators=[
            FileExtensionValidator(['jpg', 'png', 'jpeg']),
            validate_image_size
        ]
    )

    def __str__(self):
        return f"Image for {self.room.name}"