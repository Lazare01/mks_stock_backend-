from django.contrib import admin
from .models import (
    StockEntry,
    StockEntryItem,
    Product,
    StockMovement,
    InventoryStock,
    Transfer,
    TransferItem,
    TransferReceptionItem,
    TransferReception
)


@admin.register(StockEntry)
class StockEntryAdmin(admin.ModelAdmin):
    list_display = [
        "reference",
        "supplier",
        "warehouse",
        "invoice_number",
        "invoice_file",
        "expected_delivery_date",
        "received_date",
        "notes",
        "status",
    ]


@admin.register(StockEntryItem)
class StockentryitemAdmin(admin.ModelAdmin):
    list_display = [
        "stock_entry",
        "product",
        "product_category",
        "received_quantity",
        "unit_cost",
        "total_cost",
    ]

    def product_category(self, obj):
        return obj.product.get_category_display()

    product_category.short_description = "Catégorie"


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = [
        "movement_type",
        "from_warehouse",
        "to_warehouse",
        "notes",
        "movement_date",
    ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "category",
        "sku",
        "description",
        "selling_price",
    ]


@admin.register(InventoryStock)
class StockInventoryAdmin(admin.ModelAdmin):
    list_display = ["product", "warehouse", "quantity"]


# transfer

@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = [
        "reference",
        "from_warehouse",
        "to_warehouse",
        "status",
        "shipped_at",
        "received_at",
        "notes",
    ]


@admin.register(TransferItem)
class TransferItemAdmin(admin.ModelAdmin):
    list_display=["transfer","product","quantity_sent"]
    


@admin.register(TransferReception)
class TransferReaceptionAdmin(admin.ModelAdmin):
    list_display=["transfer","received_by","notes"]

@admin.register(TransferReceptionItem)
class TransferReaceptionItem(admin.ModelAdmin):
    list_display=["reception","transfer_item","quantity_received","status","notes"]