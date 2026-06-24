# finance/views/customer.py

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from billing.models import Customer
from billing.serializers import CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):

    queryset = Customer.objects.all()

    serializer_class = CustomerSerializer

    permission_classes = [
        IsAuthenticated
    ]