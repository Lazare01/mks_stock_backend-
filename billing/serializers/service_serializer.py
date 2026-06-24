# finance/serializers/service.py

from rest_framework import serializers
from billing.models import Service


class ServiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Service
        fields = "__all__"