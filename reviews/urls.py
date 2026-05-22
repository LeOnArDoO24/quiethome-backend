from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReviewViewSet, HostReviewViewSet


# Router separati per evitare conflitti
router = DefaultRouter()
router.register(r'guest-reviews', ReviewViewSet, basename='reviews')
router.register(r'host-reviews', HostReviewViewSet, basename='host-reviews')

urlpatterns = [
    path('', include(router.urls)),
]