from rest_framework import serializers
from billing.models import InvoiceLine


class InvoiceLineSerializer(serializers.ModelSerializer):

    class Meta:
        model = InvoiceLine
        fields = "__all__"

    def validate(self, attrs):

        line_type = attrs.get("line_type")

        product = attrs.get("product")

        service = attrs.get("service")

        if line_type == "PRODUCT" and not product:
            raise serializers.ValidationError(
                "Produit obligatoire."
            )

        if line_type == "SERVICE" and not service:
            raise serializers.ValidationError(
                "Service obligatoire."
            )

        return attrs