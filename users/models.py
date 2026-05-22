from django.db import models
from django.contrib.auth.models import AbstractUser
from core.models import BaseModel
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from datetime import timedelta
from core.utils import validate_image_size
import random


class User(AbstractUser, BaseModel):
    # Sovrascriviamo username di AbstractUser con un limite di 15 caratteri
    username = models.CharField(max_length=15, unique=True)
    
    # Foto profilo opzionale, accetta solo jpg/png/jpeg con validazione peso
    profile_picture = models.FileField(
        upload_to="images/",
        validators=[
            FileExtensionValidator(['jpg', 'png', 'jpeg']),
            validate_image_size
        ],
        null=True,
        blank=True
    )
    
    # Email unica per ogni utente, la usiamo anche come login
    email = models.EmailField(unique=True)
    
    # Ruolo utente, default guest — chiunque parte come ospite
    ROLE_CHOICES = [
        ('guest', 'Guest'),
        ('host', 'Host'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='guest')
    
    # L'utente nasce inattivo finché non verifica l'OTP
    is_active = models.BooleanField(default=False)

    # Oltre a username, Django richiede anche email alla creazione tramite CLI
    REQUIRED_FIELDS = ["email"]



class OTP(BaseModel):
    # Codice a 6 cifre, unico e non modificabile dall'esterno
    code = models.CharField(max_length=6, unique=True, editable=False)
    
    # Data di scadenza, calcolata al momento del salvataggio
    expired_date = models.DateTimeField()
    
    # Relazione 1:1 con User — ogni utente ha al massimo un OTP attivo
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        # Generiamo un codice univoco prima di salvare
        while True:
            temp_otp = random.randrange(111111, 999999)
            # Controlliamo che il codice non esista già nel database
            if not OTP.objects.filter(code=temp_otp).exists():
                self.code = temp_otp
                break
        
        # Impostiamo la scadenza solo alla creazione, non agli aggiornamenti
        if not self.expired_date:
            self.expired_date = timezone.now() + timedelta(minutes=15)

        return super().save(*args, **kwargs)

    @property
    def is_expired(self):
        # Property — si usa come attributo (otp.is_expired) non come metodo
        # Ritorna True se la data attuale è oltre la scadenza
        return timezone.now() > self.expired_date