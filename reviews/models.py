from django.db import models
from core.models import BaseModel
from users.models import User
from properties.models import Room
from bookings.models import Booking
from django.core.validators import MinValueValidator, MaxValueValidator


class Review(BaseModel):
    # Colleghiamo la recensione alla prenotazione
    # Garantisce che solo chi ha soggiornato può recensire
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="review")
    # Chi scrive la recensione
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    # La stanza recensita
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="reviews")
    # Rating da 1 a 5
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()

    def __str__(self):
        return f"{self.author.username} - {self.room.name} ({self.rating}/5)"

    class Meta:
        ordering = ['-created_at']


class HostReview(BaseModel):
    # Recensione dell'host verso il guest dopo il soggiorno
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="host_review")
    # L'host che scrive la recensione
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="host_reviews")
    # Il guest recensito
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_reviews")
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()

    def __str__(self):
        return f"{self.author.username} → {self.target_user.username} ({self.rating}/5)"

    class Meta:
        ordering = ['-created_at']