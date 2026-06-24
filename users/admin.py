from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, OTP


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Colonne visibili nella lista utenti
    list_display = ['username', 'email', 'is_host', 'is_active', 'created_at']
    # Filtri nella sidebar destra
    list_filter = ['is_active']
    # Campi ricercabili
    search_fields = ['username', 'email']
    # Aggiungiamo i nostri campi custom ai fieldsets di UserAdmin
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('email' , 'is_host', 'profile_picture')}),
    )


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['user', 'code', 'expired_date']