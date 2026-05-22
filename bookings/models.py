from django.db import models
from core.models import BaseModel
from users.models import User
from properties.models import Room
from django.core.exceptions import ValidationError


class Booking(BaseModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    # Stanza prenotata
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="bookings")
    # Utente che ha effettuato la prenotazione
    guest = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
    check_in = models.DateField()
    check_out = models.DateField()
    num_guests = models.PositiveIntegerField()
    # Prezzo totale calcolato al momento della prenotazione
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    # Messaggio opzionale del guest all'host
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.guest.username} - {self.room.name} ({self.status})"

    def clean(self):
        # Validazione date — check_out deve essere dopo check_in
        if self.check_in and self.check_out:
            if self.check_out <= self.check_in:
                raise ValidationError("La data di check-out deve essere successiva al check-in")

        # Validazione num_guests — non può superare il massimo della stanza
        if self.num_guests and self.room:
            if self.num_guests > self.room.max_guests:
                raise ValidationError(
                    f"Il numero di ospiti non può superare {self.room.max_guests}"
                )

    def save(self, *args, **kwargs):
        # Eseguiamo le validazioni prima di salvare
        self.clean()
        super().save(*args, **kwargs)

    @property
    def num_nights(self):
        # Calcola automaticamente il numero di notti
        return (self.check_out - self.check_in).days

    class Meta:
        # Ordina le prenotazioni dalla più recente
        ordering = ['-created_at']