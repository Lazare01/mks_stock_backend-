from rest_framework import serializers


class PaymentCancelSerializer(serializers.Serializer):

    reason = serializers.CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=True,
    )

    def validate_reason(self, value):

        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "La raison d'annulation est obligatoire."
            )

        return value