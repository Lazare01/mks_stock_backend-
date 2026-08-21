from rest_framework import serializers

from billing.models.expense_category import ExpenseCategory


class ExpenseCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = ExpenseCategory
        fields = [
            "id",
            "name",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Le nom de la catégorie est obligatoire."
            )

        return value