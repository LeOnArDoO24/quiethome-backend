from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, OTP
from rest_framework.authtoken.models import Token
from django.core.mail import send_mail


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    # Eseguiamo la logica solo alla creazione, non agli aggiornamenti
    if created:
        # Creiamo il token di autenticazione per il nuovo utente
        Token.objects.create(user=instance)
        
        # Creiamo l'OTP — triggera il metodo save() di OTP
        # che genera il codice e imposta la scadenza
        otp = OTP.objects.create(user=instance)
        
        # Inviamo l'email con il codice OTP
        send_mail(
            "OTP Code",
            f"Ciao {instance.username}, ecco il tuo OTP: {otp.code}. "
            f"Scadrà il {otp.expired_date.strftime('%d/%m/%y alle %H:%M:%S')}",
            "noreply@vacanze.com",
            [instance.email],  # mandiamo all'email reale dell'utente
            fail_silently=False,
        )