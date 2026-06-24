from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomerViewSet,ServiceViewSet

router = DefaultRouter()



router.register(
    "customers",
    CustomerViewSet,
    basename="customers"
)

router.register(
    "services",
    ServiceViewSet,
    basename="services"
)

urlpatterns = [path("", include(router.urls))]
