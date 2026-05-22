from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserModelView, LoginView


# Creiamo un'istanza del router
router = DefaultRouter()

# Registriamo il ViewSet sul router
# Il prefisso '' significa che le url partiranno da /users/
router.register(r'', UserModelView, basename='users')

urlpatterns = [
    # Login prima del router altrimenti il ViewSet intercetta la richiesta
    path('login/', LoginView.as_view()),
    path('', include(router.urls)),
]