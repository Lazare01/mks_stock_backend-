from rest_framework import serializers
from billing.models import Invoice
from billing.serializers import InvoiceLineSerializer



class InvoiceSerializer(serializers.ModelSerializer):

    lines = InvoiceLineSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Invoice
        fields = "__all__"