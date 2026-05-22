from django.contrib import admin
from .models import Property, Room, RoomImage, Amenity


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon_slug']
    search_fields = ['name']


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'country', 'host']
    list_filter = ['city', 'country']
    search_fields = ['name', 'city', 'host__username']


class RoomImageInline(admin.TabularInline):
    # Mostra le immagini direttamente nella pagina della stanza
    model = RoomImage
    extra = 1


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'property', 'room_type', 'price_per_night', 'is_available']
    list_filter = ['room_type', 'is_available']
    search_fields = ['name', 'property__name']
    # Includiamo le immagini inline nella pagina della stanza
    inlines = [RoomImageInline]