# finance/serializers/customer.py

from rest_framework import serializers
from billing.models import Customer


class CustomerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Customer
        fields = "__all__"