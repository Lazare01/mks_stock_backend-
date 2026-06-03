# urls.py

from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .views import WarehouseViewSet

router = DefaultRouter()

router.register(r"warehouses", WarehouseViewSet, basename="warehouse")

urlpatterns = [
    path("", include(router.urls)),
]
