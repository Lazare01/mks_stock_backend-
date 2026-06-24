# finance/views/service.py

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from billing.serializers import ServiceSerializer
from billing.models import Service


class ServiceViewSet(viewsets.ModelViewSet):

    queryset = Service.objects.all()

    serializer_class = ServiceSerializer

    permission_classes = [
        IsAuthenticated
    ]