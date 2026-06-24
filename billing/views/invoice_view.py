from rest_framework.viewsets import ModelViewSet
from billing.models import Invoice
from billing.serializers import InvoiceSerializer
from rest_framework.permissions import IsAuthenticated



class InvoiceViewSet(ModelViewSet):

    queryset = Invoice.objects.all()

    serializer_class = InvoiceSerializer

    permission_classes = [
        IsAuthenticated
    ]