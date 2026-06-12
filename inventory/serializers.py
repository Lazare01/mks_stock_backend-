# serializers.py

from rest_framework import serializers

from .models import Warehouse

from supplier.models import Supplier

from inventory.models import (
    Warehouse,
    Product,
    StockEntry,
    StockEntryItem,
    Transfer
)
from supplier.serializers import SupplierSerializer

from .constants import TransferReceptionStatus

# =========================================================
# STOCK ENTRY ITEM Utilisé pour l'affichage.
# =========================================================


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "category",
            "sku",
            "description",
            "selling_price",
            "reorder_threshold",
        ]


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


from rest_framework import serializers


# ==================================================
# ============ STOCK DASH MOVEMENT =================
# ==================================================
class DashboardMovementSerializer(serializers.Serializer):

    date = serializers.DateTimeField()

    product_category = serializers.CharField()

    movement_type = serializers.CharField()

    product_name = serializers.CharField()

    quantity_received = serializers.IntegerField()

    from_warehouse = serializers.CharField(allow_null=True)
    to_warehouse = serializers.CharField(allow_null=True)
    status_entry = serializers.CharField()


# ==================================================
# ============ STOCK DASH inventory =================
# ==================================================


class DashboardInventorySerializer(serializers.Serializer):

    id = serializers.IntegerField()

    name = serializers.CharField()

    sku = serializers.CharField()

    product_category = serializers.CharField()

    stock_central = serializers.IntegerField()

    stock_branches = serializers.IntegerField()

    selling_price = serializers.DecimalField(max_digits=12, decimal_places=2)

    reorder_threshold = serializers.IntegerField()



# ==================================================
# ============ STOCK branch summary ================
# ==================================================

class DashboardStockbrachSummary(serializers.Serializer):
    warehouse_id = serializers.UUIDField()
    warehouse_name = serializers.CharField()
    critical=serializers.IntegerField()
    low=serializers.IntegerField()
    healthy=serializers.IntegerField()
    
    


# ===============================================
# ============ TRANSFER ITEMS    ================
# ===============================================

class UseDetailProductToTransfer(serializers.Serializer):
    product_id = serializers.UUIDField()
    product_category = serializers.CharField()
    product_quantity_stock = serializers.IntegerField()
    
    

class TransferItemCreateSerializer(
    serializers.Serializer
):

    product_id = serializers.IntegerField()

    quantity_sent = serializers.IntegerField(
        min_value=1
    )

class TransferCreateSerializer(
    serializers.Serializer
):

    from_warehouse_id = serializers.IntegerField()

    to_warehouse_id = serializers.IntegerField()

    notes = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    items = TransferItemCreateSerializer(
        many=True
    )

    def validate(self, attrs):

        if (
            attrs["from_warehouse_id"]
            ==
            attrs["to_warehouse_id"]
        ):
            raise serializers.ValidationError(
                "Le dépôt source et destination doivent être différents."
            )

        return attrs

class TransferListSerializer(
    serializers.ModelSerializer
):

    from_warehouse = serializers.CharField(
        source="from_warehouse.name",
        read_only=True,
    )

    to_warehouse = serializers.CharField(
        source="to_warehouse.name",
        read_only=True,
    )

    total_items = serializers.SerializerMethodField()

    class Meta:

        model = Transfer

        fields = (
            "id",
            "reference",
            "status",
            "from_warehouse",
            "to_warehouse",
            "total_items",
            "shipped_at",
            "received_at",
            "created_at",
        )

    def get_total_items(
        self,
        obj,
    ):
        return obj.items.count()

from rest_framework import serializers

from inventory.models import TransferItem


class TransferItemDetailSerializer(
    serializers.ModelSerializer
):

    product_name = serializers.CharField(
        source="product.name",
        read_only=True,
    )

    product_sku = serializers.CharField(
        source="product.sku",
        read_only=True,
    )

    product_category = serializers.CharField(
        source="product.category",
        read_only=True,
    )

    class Meta:

        model = TransferItem

        fields = (
            "id",
            "product",
            "product_name",
            "product_sku",
            "product_category",
            "quantity_sent",
        )

class TransferDetailSerializer(
    serializers.ModelSerializer
):

    from_warehouse = serializers.CharField(
        source="from_warehouse.name",
        read_only=True,
    )

    to_warehouse = serializers.CharField(
        source="to_warehouse.name",
        read_only=True,
    )

    items = TransferItemDetailSerializer(
        many=True,
        read_only=True,
    )

    class Meta:

        model = Transfer

        fields = (
            "id",
            "reference",
            "status",
            "from_warehouse",
            "to_warehouse",
            "notes",
            "shipped_at",
            "received_at",
            "created_at",
            "items",
        )

class TransferReceptionItemSerializer(
    serializers.Serializer
):

    transfer_item_id = serializers.IntegerField()

    quantity_received = serializers.IntegerField(
        min_value=0
    )

    status = serializers.ChoiceField(
        choices=TransferReceptionStatus.choices
    )

    notes = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    


# reception complete 

class TransferReceptionSerializer(
    serializers.Serializer
):

    notes = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    items = TransferReceptionItemSerializer(
        many=True
    )

    def validate_items(
        self,
        value,
    ):

        if not value:
            raise serializers.ValidationError(
                "Au moins un article est requis."
            )

        return value