from django.contrib import admin
from .models import Property, PropertyImage, Room, RoomImage, Amenity


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    # Colonne visibili nella lista amenities
    list_display = ['name', 'icon_slug']
    # Campi ricercabili
    search_fields = ['name']


class PropertyImageInline(admin.TabularInline):
    # Mostra le immagini direttamente nella pagina della property
    # extra=1 significa che mostra 1 riga vuota per aggiungere nuove immagini
    model = PropertyImage
    extra = 1


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    # Colonne visibili nella lista properties
    list_display = ['name', 'city', 'country', 'host']
    # Filtri nella sidebar destra
    list_filter = ['city', 'country']
    # Campi ricercabili
    search_fields = ['name', 'city', 'host__username']
    # Includiamo le immagini inline nella pagina della property
    inlines = [PropertyImageInline]


class RoomImageInline(admin.TabularInline):
    # Mostra le immagini direttamente nella pagina della stanza
    # extra=1 significa che mostra 1 riga vuota per aggiungere nuove immagini
    model = RoomImage
    extra = 1


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    # Colonne visibili nella lista stanze
    list_display = ['name', 'property', 'room_type', 'price_per_night', 'is_available']
    # Filtri nella sidebar destra
    list_filter = ['room_type', 'is_available']
    # Campi ricercabili
    search_fields = ['name', 'property__name']
    # Includiamo le immagini inline nella pagina della stanza
    inlines = [RoomImageInline]