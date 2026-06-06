from rest_framework import serializers
from .models import Supplier
# =========================================================
# SUPPLIERS
# =========================================================

class SupplierSerializer(serializers.ModelSerializer):

    class Meta:
        model = Supplier

        fields = [
            "id",
            "name",
            "contact_person",
            "phone_number",
            "email",
            "address",
            "notes",
            "is_active",
            "created_at",
        ]