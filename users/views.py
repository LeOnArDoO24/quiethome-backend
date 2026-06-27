from .serializers import UserSerializer, UserViewSerializer
from .models import User, OTP
from rest_framework import ( viewsets, permissions as drf_permissions, mixins )
from rest_framework.decorators import action
from rest_framework.response import Response
from http import HTTPStatus
from core.permissions import IsOwner
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from django.core.mail import send_mail
from rest_framework.authtoken.models import Token
from rest_framework.authtoken import views as auth_views


class UserModelView(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    queryset = User.objects.all()
    permission_classes = [drf_permissions.IsAuthenticated]

    def get_serializer_class(self):
        # In base all'azione usiamo serializer diversi
        if self.action in ["retrieve", "me", "update", "partial_update"]:
            return UserViewSerializer
        return UserSerializer

    def get_permissions(self):
        # Azioni pubbliche — chiunque può registrarsi e verificare l'OTP
        if self.action in ['create', 'verify_otp', 'resend_otp', 'forgot_password', 'reset_password']:
            return [drf_permissions.AllowAny()]

        # Solo il proprietario dell'account può vedere o modificare i propri dati
        if self.action in ['retrieve', 'update', 'partial_update']:
            return [drf_permissions.IsAuthenticated(), IsOwner()]

        # Default — qualsiasi altra azione richiede solo autenticazione
        return [drf_permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        # Salviamo l'utente e poi hasciamo la password
        # set_password() trasforma la password in chiaro in un hash sicuro
        instance = serializer.save()
        instance.set_password(instance.password)
        instance.save()

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        """
        GET /users/me/
        Ritorna i dati dell'utente autenticato
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=HTTPStatus.OK)

    @action(detail=False, methods=['post'], url_path='verify-otp')
    def verify_otp(self, request):
        """
        POST /users/verify-otp/
        Body: { "code": "123456" }
        Verifica il codice OTP e attiva l'account
        """
        code = request.data.get("code")

        if not code:
            raise ValidationError({"error": "Il codice OTP è obbligatorio"})

        # Cerchiamo l'OTP nel database
        otp_code = OTP.objects.filter(code=code).first()

        if not otp_code:
            raise ValidationError({"error": "Codice OTP non valido"})

        if otp_code.is_expired:
            raise ValidationError({"error": "Il codice OTP è scaduto"})

        # Troviamo l'utente collegato all'OTP
        user = otp_code.user

        # Attiviamo l'account e cancelliamo l'OTP usato
        user.is_active = True
        user.save(update_fields=['is_active'])
        otp_code.delete()

        # Recuperiamo il token creato dal signal alla registrazione
        token = Token.objects.filter(user=user).first()

        return Response({
            "token": token.key,
            "user": UserViewSerializer(user).data,
            "message": "Account verificato con successo"
        }, status=HTTPStatus.OK)

    @action(detail=False, methods=['post'], url_path='resend-otp')
    def resend_otp(self, request):
        """
        POST /users/resend-otp/
        Body: { "user": "uuid-utente" }
        Cancella il vecchio OTP e ne genera uno nuovo
        """
        user_id = request.data.get("user")

        if not user_id:
            raise ValidationError({"error": "L'id utente è obbligatorio"})

        # Gestiamo il caso in cui l'id non sia un UUID valido
        try:
            user = User.objects.filter(id=user_id).first()
        except (DjangoValidationError, ValueError):
            raise ValidationError({"error": "Utente non trovato"})

        if not user:
            raise ValidationError({"error": "Utente non trovato"})

        if user.is_active:
            raise ValidationError({"error": "L'utente è già attivo"})

        # Cancelliamo il vecchio OTP se esiste
        OTP.objects.filter(user=user).delete()

        # Creiamo un nuovo OTP — triggera OTP.save()
        otp = OTP.objects.create(user=user)

        send_mail(
            "Nuovo OTP Code",
            f"Ciao {user.username}, ecco il tuo nuovo OTP: {otp.code}. "
            f"Scadrà il {otp.expired_date.strftime('%d/%m/%y alle %H:%M:%S')}",
            "noreply@vacanze.com",
            [user.email],
            fail_silently=False,
        )

        return Response({"message": "Nuovo OTP inviato"}, status=HTTPStatus.OK)

    @action(detail=False, methods=['post'], url_path='become-host')
    def become_host(self, request):
        """
        POST /users/become-host/
        Cambia is_host dell'utente autenticato a True
        """
        user = request.user

        if user.is_host:
            raise ValidationError({"error": "Sei già un host"})

        user.is_host = True
        user.save(update_fields=['is_host'])

        return Response({
            "message": "Sei diventato host con successo",
            "user": UserViewSerializer(user).data
        }, status=HTTPStatus.OK)

    @action(detail=False, methods=['post'], url_path='forgot-password')
    def forgot_password(self, request):
        """
        POST /users/forgot-password/
        Body: { "email": "utente@email.com" }
        Genera un OTP e lo manda via email per il recupero password
        """
        email = request.data.get("email")

        if not email:
            raise ValidationError({"error": "L'email è obbligatoria"})

        # Cerchiamo l'utente con quell'email
        user = User.objects.filter(email=email).first()

        # Per sicurezza non rivelare se l'email esiste o meno
        if not user:
            return Response({"message": "Se l'email esiste riceverai un codice"}, status=HTTPStatus.OK)

        # Cancelliamo eventuale OTP precedente e ne generiamo uno nuovo
        OTP.objects.filter(user=user).delete()
        otp = OTP.objects.create(user=user)

        # Mandiamo l'email con il codice di recupero
        send_mail(
            "Recupero password QuietHome",
            f"Ciao {user.username}, hai richiesto il recupero della password.\n\n"
            f"Il tuo codice è: {otp.code}\n\n"
            f"Scadrà tra 15 minuti. Se non hai richiesto il recupero, ignora questa email.",
            "noreply@quiethome.com",
            [user.email],
            fail_silently=True,
        )

        return Response({
            "message": "Se l'email esiste riceverai un codice",
            "user_id": str(user.id)
        }, status=HTTPStatus.OK)

    @action(detail=False, methods=['post'], url_path='reset-password')
    def reset_password(self, request):
        """
        POST /users/reset-password/
        Body: { "code": "123456", "new_password": "nuovapassword" }
        Verifica l'OTP e aggiorna la password dell'utente
        """
        code = request.data.get("code")
        new_password = request.data.get("new_password")

        if not code or not new_password:
            raise ValidationError({"error": "Codice OTP e nuova password sono obbligatori"})

        if len(new_password) < 8:
            raise ValidationError({"error": "La password deve essere di almeno 8 caratteri"})

        # Cerchiamo l'OTP nel database
        otp_code = OTP.objects.filter(code=code).first()

        if not otp_code:
            raise ValidationError({"error": "Codice OTP non valido"})

        if otp_code.is_expired:
            raise ValidationError({"error": "Il codice OTP è scaduto"})

        # Aggiorniamo la password e attiviamo l'account (nel caso fosse inattivo)
        user = otp_code.user
        user.set_password(new_password)
        user.is_active = True
        user.save(update_fields=['password', 'is_active'])

        # Cancelliamo l'OTP usato
        otp_code.delete()

        return Response({
            "message": "Password aggiornata con successo"
        }, status=HTTPStatus.OK)


class LoginView(auth_views.ObtainAuthToken):
    """
    POST /users/login/
    Body: { "username": "...", "password": "..." }
    Ritorna il token di autenticazione
    """
    permission_classes = [drf_permissions.AllowAny]