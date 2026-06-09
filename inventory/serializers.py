# serializers.py

from rest_framework import serializers

from .models import Warehouse

from supplier.models import Supplier

from inventory.models import (
    Warehouse,
    Product,
    StockEntry,
    StockEntryItem,
    StockEntryStatus,
)
from supplier.serializers import SupplierSerializer


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


# =========================================================
# STOCK ENTRY ITEM Utilisé pour l'affichage.
# =========================================================


class StockEntrySerialSerializer(serializers.Serializer):

    serial_number = serializers.CharField(max_length=255)

    mac_address = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
    )


# =========================================================
# STOCK ENTRY ITEM Utilisé lors de la création.
# ======================================
class StockEntryItemSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(
        source="product.name",
        read_only=True,
    )

    class Meta:
        model = StockEntryItem

        fields = [
            "id",
            "product",
            "product_name",
            "received_quantity",
            "unit_cost",
        ]


class StockEntryItemCreateSerializer(serializers.Serializer):

    product_id = serializers.UUIDField()

    unit_cost = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0.01,
    )
    received_quantity = serializers.IntegerField(min_value=1)

    serials = StockEntrySerialSerializer(many=True)

    def validate_serials(self, value):

        if not value:
            raise serializers.ValidationError("Au moins un numéro de série est requis.")

        return value


class StockEntryCreateSerializer(serializers.Serializer):

    supplier_name = serializers.CharField(max_length=255)

    warehouse_id = serializers.UUIDField()

    invoice_number = serializers.CharField(max_length=150)

    expected_delivery_date = serializers.DateField(
        required=False,
        allow_null=True,
    )

    notes = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    items = StockEntryItemCreateSerializer(many=True)

    def validate_items(self, value):

        if not value:
            raise serializers.ValidationError("Au moins un produit est requis.")

        return value

    def validate_warehouse_id(self, value):

        warehouse = Warehouse.objects.filter(id=value).first()

        if not warehouse:
            raise serializers.ValidationError("Entrepôt introuvable.")

        return value


# =========================================================
# LIST STOCK ENTRY
# =========================================================


class StockEntryListSerializer(serializers.ModelSerializer):

    supplier_name = serializers.CharField(
        source="supplier.name",
        read_only=True,
    )

    warehouse_name = serializers.CharField(
        source="warehouse.name",
        read_only=True,
    )

    item_count = serializers.SerializerMethodField()

    class Meta:
        model = StockEntry

        fields = [
            "id",
            "reference",
            "supplier_name",
            "warehouse_name",
            "invoice_number",
            "status",
            "item_count",
            "expected_delivery_date",
            "received_date",
            "created_at",
        ]

    def get_item_count(self, obj):

        return obj.items.count()


# =========================================================
# DETAIL STOCK ENTRY
# =========================================================


class StockEntryDetailSerializer(serializers.ModelSerializer):

    supplier = SupplierSerializer(read_only=True)

    warehouse_name = serializers.CharField(
        source="warehouse.name",
        read_only=True,
    )

    items = StockEntryItemSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = StockEntry

        fields = [
            "id",
            "reference",
            "supplier",
            "warehouse",
            "warehouse_name",
            "invoice_number",
            "invoice_file",
            "status",
            "expected_delivery_date",
            "received_date",
            "notes",
            "items",
            "created_at",
            "updated_at",
        ]


# =======================================================
# Maintenant nous préparons l'import manuel ou Excel.
# =======================================================

# =========================================================
# SERIAL INPUT
# =========================================================


class StockEntrySerialSerializer(serializers.Serializer):

    serial_number = serializers.CharField(max_length=255)

    mac_address = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
    )


# =========================================================
# STOCK SUMMARY
# =========================================================


class ProductStockSummarySerializer(serializers.Serializer):

    id = serializers.UUIDField()

    name = serializers.CharField()

    sku = serializers.CharField()

    category = serializers.CharField()

    central_stock = serializers.IntegerField()

    branch_stock = serializers.IntegerField()

    purchase_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    selling_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )


# =========================================================
# STOCK MOVEMENTS
# =========================================================


class StockMovementSerializer(serializers.Serializer):

    id = serializers.UUIDField()

    movement_type = serializers.CharField()

    product_name = serializers.CharField()

    serial_number = serializers.CharField()

    movement_date = serializers.DateTimeField()

    from_warehouse = serializers.CharField(
        allow_null=True,
    )

    to_warehouse = serializers.CharField(
        allow_null=True,
    )

    # =========================================================


# PRODUCTS
# =========================================================

from inventory.models import Product


class ProductSerializer(serializers.ModelSerializer):

    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
    )

    class Meta:
        model = Product

        fields = [
            "id",
            "name",
            "sku",
            "category",
            "category_name",
            "purchase_price",
            "selling_price",
            "description",
        ]


from rest_framework import serializers



# ==================================================
# ============ STOCK DASH MOVEMENT =================
# ==================================================
class DashboardMovementSerializer(serializers.Serializer):
   
    date = serializers.DateTimeField()

    type = serializers.CharField()

    product = serializers.CharField()

    quantity = serializers.IntegerField()

    from_warehouse = serializers.CharField(
        allow_null=True
    )

    to_warehouse = serializers.CharField(
        allow_null=True
    )

    status = serializers.CharField()