from rest_framework import serializers
from inventory.models import Product, Transfer,TransferItem
from inventory.constants import TransferReceptionStatus

import logging

logger = logging.getLogger(__name__)

# ===============================================
# ============ TRANSFER ITEMS    ================
# ===============================================


class ProductTransferSummarySerializer(serializers.Serializer):

    product_id = serializers.IntegerField()

    product_name = serializers.CharField()

    available_stock = serializers.IntegerField()


class TransferItemCreateSerializer(serializers.Serializer):

    product_id = serializers.UUIDField()

    quantity_sent = serializers.IntegerField(min_value=1)


class TransferCreateSerializer(serializers.Serializer):

    from_warehouse_id = serializers.UUIDField()

    to_warehouse_id = serializers.UUIDField()

    notes = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    items = TransferItemCreateSerializer(many=True)

    def validate(self, attrs):

        if attrs["from_warehouse_id"] == attrs["to_warehouse_id"]:
            raise serializers.ValidationError(
                "Le dépôt source et destination doivent être différents."
            )

        return attrs



class TransferGetProductItem(serializers.ModelSerializer):
    product_name=serializers.CharField(source="product.name")
    class Meta:
        model=TransferItem
        fields=["product_name","quantity_sent"]

class TransferListSerializer(serializers.ModelSerializer):

    from_warehouse = serializers.CharField(
        source="from_warehouse.name",
        read_only=True,
    )
    to_warehouse = serializers.CharField(
        source="to_warehouse.name",
        read_only=True,
    )
    total_items = serializers.SerializerMethodField()
    initiated_by = serializers.SerializerMethodField()
    items=TransferGetProductItem(many=True)
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
            "initiated_by",
            "items"
        )

    def get_total_items(
        self,
        obj,
    ):
        return obj.items.count()

    def get_initiated_by(self, obj):
        if obj.created_by:
            return obj.created_by.username
        return None
    
    


from rest_framework import serializers

from inventory.models import TransferItem


class TransferItemDetailSerializer(serializers.ModelSerializer):

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


class TransferDetailSerializer(serializers.ModelSerializer):

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


class TransferReceptionItemSerializer(serializers.Serializer):

    transfer_item_id = serializers.IntegerField()

    quantity_received = serializers.IntegerField(min_value=0)

    status = serializers.ChoiceField(choices=TransferReceptionStatus.choices)

    notes = serializers.CharField(
        required=False,
        allow_blank=True,
    )


# reception complete


class TransferReceptionSerializer(serializers.Serializer):

    notes = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    items = TransferReceptionItemSerializer(many=True)

    def validate_items(
        self,
        value,
    ):

        if not value:
            raise serializers.ValidationError("Au moins un article est requis.")

        return value
