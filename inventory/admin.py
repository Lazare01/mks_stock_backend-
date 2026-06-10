from django.contrib import admin
from .models import StockEntry, StockEntryItem, Product, StockItem, StockMovement


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


class StockentryitemAdmin(admin.ModelAdmin):
    list_display = [
        "stock_entry",
        "product",
        "received_quantity",
        "unit_cost",
        "total_cost",
    ]


class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "category",
        "sku",
        "description",
        "purchase_price",
        "is_serialized",
        "selling_price",
    ]


class StockItemAdmin(admin.ModelAdmin):
    list_display = ["product", "warehouse", "serial_number", "mac_address", "status"]


class StockMovementAdmin(admin.ModelAdmin):
    list_display = [
        "stock_item",
        "movement_type",
        "from_warehouse",
        "to_warehouse",
        "notes",
        "movement_date",
    ]


admin.site.register(StockEntry, StockEntryAdmin)
admin.site.register(StockEntryItem, StockentryitemAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(StockItem, StockItemAdmin)
admin.site.register(StockMovement, StockMovementAdmin)
