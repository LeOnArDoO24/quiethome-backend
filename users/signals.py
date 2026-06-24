from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, OTP
from rest_framework.authtoken.models import Token
from django.core.mail import send_mail
import zoneinfo

LOCAL_TZ = zoneinfo.ZoneInfo("Europe/Rome")


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    if created:
        Token.objects.create(user=instance)

        otp = OTP.objects.create(user=instance)

        # Convertiamo la scadenza in ora locale per l'email
        local_expiry = otp.expired_date.astimezone(LOCAL_TZ)

        send_mail(
            "OTP Code",
            f"Ciao {instance.username}, ecco il tuo OTP: {otp.code}. "
            f"Scadrà il {local_expiry.strftime('%d/%m/%y alle %H:%M:%S')}",
            "noreply@vacanze.com",
            [instance.email],
            fail_silently=True,
        )