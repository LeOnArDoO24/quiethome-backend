from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # Esponiamo solo i campi necessari alla registrazione
        fields = ["username", "email", "password", "profile_picture", "is_host", "id"]
        extra_kwargs = {
            # La password non deve mai essere ritornata nelle response
            "password": {"write_only": True}
        }


class UserViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # Campi che vogliamo mostrare quando visualizziamo un utente
        fields = ["id", "username", "email", "profile_picture", "is_host", "created_at", "updated_at"]
        # Questi campi non possono essere modificati tramite API
        read_only_fields = ["id", "created_at", "updated_at"]