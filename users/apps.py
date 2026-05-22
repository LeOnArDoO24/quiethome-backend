from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'users'
    
    def ready(self):
        # Importiamo i signals quando l'app è pronta
        # Senza questo Django non sa che i signals esistono
        from . import signals