from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from .views import PropertyViewSet, RoomViewSet, AmenityViewSet


# Router principale per le properties
router = DefaultRouter()
router.register(r'', PropertyViewSet, basename='properties')
router.register(r'amenities', AmenityViewSet, basename='amenities')

# Router nested per le rooms dentro le properties
# Genera URL tipo /properties/{property_pk}/rooms/
properties_router = routers.NestedDefaultRouter(router, r'', lookup='property')
properties_router.register(r'rooms', RoomViewSet, basename='property-rooms')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(properties_router.urls)),
]