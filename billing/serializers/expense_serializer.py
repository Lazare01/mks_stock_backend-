from rest_framework import serializers

from billing.models.expense import Expense
from billing.models.expense_category import ExpenseCategory


class ExpenseSerializer(serializers.ModelSerializer):

    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
    )

    warehouse_name = serializers.CharField(
        source="warehouse.name",
        read_only=True,
    )

    created_by_name = serializers.CharField(
        source="created_by.username",
        read_only=True,
    )

    approved_by_name = serializers.CharField(
        source="approved_by.username",
        read_only=True,
    )

    class Meta:
        model = Expense
        fields = [
            "id",
            "reference",
            "warehouse",
            "warehouse_name",
            "category",
            "category_name",
            "amount",
            "expense_date",
            "description",
            "status",
            "created_by",
            "created_by_name",
            "approved_by",
            "approved_by_name",
            "approved_at",
            "cancelled_by",
            "cancelled_at",
            "cancellation_reason",
            "notes",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "reference",
            "status",
            "created_by",
            "approved_by",
            "approved_at",
            "cancelled_by",
            "cancelled_at",
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

    def validate_category(self, value):
        if not value.is_active:
            raise serializers.ValidationError(
                "Cette catégorie est désactivée."
            )

        return value

    def validate(self, attrs):
        description = attrs.get("description")

        if not description or not description.strip():
            raise serializers.ValidationError({
                "description": "La description est obligatoire."
            })

        return attrs