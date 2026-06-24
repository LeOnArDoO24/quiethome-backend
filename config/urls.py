from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Tutte le url che iniziano con /users/ vengono gestite da users/urls.py
    path('users/', include('users.urls')),
    path('properties/', include('properties.urls')),
    path('bookings/', include('bookings.urls')),
    path('reviews/', include('reviews.urls'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)