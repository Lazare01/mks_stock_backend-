from rest_framework import serializers

from billing.models import Payment, PaymentMethod


class PaymentMethodSerializer(serializers.ModelSerializer):

    class Meta:
        model = PaymentMethod
        fields = [
            "id",
            "name",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class PaymentSerializer(serializers.ModelSerializer):

    invoice_reference = serializers.CharField(
        source="invoice.reference",
        read_only=True,
    )

    customer_name = serializers.CharField(
        source="invoice.customer.name",
        read_only=True,
    )

    warehouse_name = serializers.CharField(
        source="invoice.warehouse.name",
        read_only=True,
    )

    payment_method_name = serializers.CharField(
        source="payment_method.name",
        read_only=True,
    )

    received_by_name = serializers.CharField(
        source="received_by.username",
        read_only=True,
    )

    cancelled_by_name = serializers.CharField(
        source="cancelled_by.username",
        read_only=True,
    )

    class Meta:
        model = Payment

        fields = [
            "id",
            "reference",

            "invoice",
            "invoice_reference",
            "customer_name",
            "warehouse_name",

            "payment_method",
            "payment_method_name",

            "amount",
            "payment_date",
            "notes",

            "received_by",
            "received_by_name",

            "is_cancelled",

            "cancelled_at",
            "cancelled_by",
            "cancelled_by_name",
            "cancellation_reason",

            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "reference",

            "received_by",

            "is_cancelled",

            "cancelled_at",
            "cancelled_by",
            "cancellation_reason",

            "created_at",
            "updated_at",
        ]

    def validate_amount(self, value):

        if value <= 0:
            raise serializers.ValidationError(
                "Le montant doit être supérieur à zéro."
            )

        return value

    def validate_payment_method(self, value):

        if not value.is_active:
            raise serializers.ValidationError(
                "Cette méthode de paiement est désactivée."
            )

        return value