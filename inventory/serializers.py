# serializers.py

from rest_framework import serializers

from .models import Warehouse


class WarehouseSerializer(serializers.ModelSerializer):

    available_stock = serializers.ReadOnlyField()
    current_manager = serializers.SerializerMethodField()
    city_name = serializers.SerializerMethodField()

    class Meta:
        model = Warehouse
        fields = [
            "id",
            "name",
            "warehouse_type",
            "city",
            "city_name",
            "address",
            "status",
            "available_stock",
            "current_manager",
            "created_at",
            "updated_at",
        ]

    def get_city_name(self, instance):
        if instance.city:
            return instance.city.name

    def get_current_manager(self, obj):

        manager = obj.current_manager

        if not manager:
            return None

        return {
            "id": manager.id,
            "username": manager.username,
            "email": manager.email,
            "full_name": manager.get_full_name(),
        }
