from collections import defaultdict
from django.db.models import Sum
from warehouse.constants import WarehouseType

from inventory.models import (
    StockEntryItem,
    StockEntryStatus,
    Transfer,
    InventoryStock,
    Product
)


class DashboardMovementService:

    @staticmethod
    def get_latest_movements(limit=50):

        results = []

        # =====================================
        # ENTREES DE STOCK
        # =====================================

        stock_entries = (
            StockEntryItem.objects.select_related(
                "product",
       
        "stock_entry",
        "stock_entry__warehouse",
            )
            .filter(
                stock_entry__status=StockEntryStatus.ACTIVE
            )
            .order_by("-created_at")[:limit]
        )

        for item in stock_entries:

            results.append(
                {
                    
                    "date": (
                        item.stock_entry.received_date
                        or item.created_at
                    ),
                    "movement_type": "IN",
                    "product_name": item.product.name,
                    "product_category" : item.product.category,
                    "quantity_received": item.received_quantity,
                    "from_warehouse": item.stock_entry.supplier.name,
                    "to_warehouse": (
                        item.stock_entry.warehouse.name
                    ),
                    "status_entry": item.stock_entry.get_status_display(),
                }
            )

        # =====================================
        # TRANSFERTS
        # =====================================

        transfers = (
            Transfer.objects.select_related(
                "from_warehouse",
                "to_warehouse",
            )
            .prefetch_related(
                "items__stock_item__product"
            )
            .exclude(status="DRAFT")
            .order_by("-created_at")[:limit]
        )

        for transfer in transfers:

            grouped_products = defaultdict(int)

            for item in transfer.items.all():

                product_name = (
                    item.stock_item.product.name
                )

                grouped_products[product_name] += 1

            for product_name, quantity in grouped_products.items():

                results.append(
                    {
                        "date": transfer.created_at,
                        "type": "TRANSFER",
                        "product": product_name,
                        "quantity": quantity,
                        "from_warehouse": (
                            transfer.from_warehouse.name
                        ),
                        "to_warehouse": (
                            transfer.to_warehouse.name
                        ),
                        "status": (
                            transfer.get_status_display()
                        ),
                    }
                )

        results = sorted(
            results,
            key=lambda x: x["date"],
            reverse=True,
        )

        return results[:limit]
    
    # ====================================
    # ------------ inventory stock -------
    # ====================================
    
    @staticmethod
    def inventory_overview():

        data = []

        products = Product.objects.all()

        for product in products:

            central_stock = (
                InventoryStock.objects
                .filter(
                    product=product,
                     warehouse__warehouse_type=WarehouseType.CENTRAL
                )
                .aggregate(
                    total=Sum("quantity")
                )["total"]
                or 0
            )

            branches_stock = (
                InventoryStock.objects
                .filter(
                    product=product,
                    warehouse__warehouse_type=WarehouseType.BRANCH
                )
                .aggregate(
                    total=Sum("quantity")
                )["total"]
                or 0
            )

            data.append({
                "id": product.id,
                "name": product.name,
                "sku": product.sku,
                "stock_central": central_stock,
                "product_category": product.category,
                "stock_branches": branches_stock,
                "selling_price": product.selling_price,
                "reorder_threshold": product.reorder_threshold,
            })

        return data
