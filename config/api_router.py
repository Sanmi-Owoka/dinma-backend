from rest_framework.routers import DefaultRouter, SimpleRouter
from django.conf import settings
from authentication.views.patient_authentication_views import (
    PatientAuthenticationViewSet,
)

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register(
    "authentication",
    PatientAuthenticationViewSet,
    basename="patient authentication viewsets",
)

app_name = "api"
urlpatterns = router.urls
