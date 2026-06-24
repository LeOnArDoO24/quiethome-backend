from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    # Colonne visibili nella lista prenotazioni
    list_display = ['guest', 'room', 'check_in', 'check_out', 'status', 'created_at']
    # Filtri nella sidebar destra
    list_filter = ['status']
    # Campi ricercabili
    search_fields = ['guest__username', 'room__name']
    # Permette di cambiare lo status direttamente dalla lista
    list_editable = ['status']