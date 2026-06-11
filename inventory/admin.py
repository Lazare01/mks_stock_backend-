from django.contrib import admin
from .models import StockEntry, StockEntryItem, Product, StockMovement,InventoryStock


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
        "product_category",
        "received_quantity",
        "unit_cost",
        "total_cost",
    ]

    def product_category(self, obj):
        return obj.product.get_category_display()

    product_category.short_description = "Catégorie"




class StockMovementAdmin(admin.ModelAdmin):
    list_display = [
        "movement_type",
        "from_warehouse",
        "to_warehouse",
        "notes",
        "movement_date",
    ]


class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "category",
        "sku",
        "description",
        "selling_price",
    ]
    

class StockInventoryAdmin(admin.ModelAdmin):
    list_display=[
        "product",
        "warehouse",
        "quantity"
    ]


admin.site.register(Product, ProductAdmin)
admin.site.register(StockEntry, StockEntryAdmin)
admin.site.register(StockEntryItem, StockentryitemAdmin)
admin.site.register(StockMovement, StockMovementAdmin)
admin.site.register(InventoryStock,StockInventoryAdmin)