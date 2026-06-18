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
from warehouse.models import Warehouse


class DashboardStockService:

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
                    "quantity": item.received_quantity,
                    "from_warehouse": item.stock_entry.supplier.name,
                    "to_warehouse": (
                        item.stock_entry.warehouse.name
                    ),
                    "status": item.stock_entry.get_status_display(),
                }
            )

        # =====================================
        # TRANSFERTS
        # =====================================

        transfers = (
            Transfer.objects
            .select_related(
                "from_warehouse",
                "to_warehouse",
            )
            .prefetch_related(
                "items__product"
            )
            .exclude(status="DRAFT")
            .order_by("-created_at")[:limit]
        )

        for transfer in transfers:

            for item in transfer.items.all():

                results.append(
                    {
                        "date": (
                            transfer.shipped_at
                            or transfer.created_at
                        ),
                        "movement_type": "TRANSFER",
                        "product_name": item.product.name,
                        "product_category": item.product.category,
                        "quantity": item.quantity_sent,
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

        # =====================================
        # TRI GLOBAL
        # =====================================

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
    
        
    # ====================================
    # ------------  stock brach summury --
    # ====================================
    
    @staticmethod
    def get_branches_summary():

        branches = Warehouse.objects.filter(
            warehouse_type=WarehouseType.BRANCH
        )

        result = []

        for branch in branches:

            critical = 0
            low = 0
            healthy = 0

            stocks = (
                InventoryStock.objects
                .select_related("product")
                .filter(
                    warehouse=branch
                )
            )

            for stock in stocks:

                threshold = (
                    stock.product.reorder_threshold
                )

                if stock.quantity == 0:
                    critical += 1

                elif stock.quantity <= threshold:
                    low += 1

                else:
                    healthy += 1

            result.append({
                "warehouse_id": branch.id,
                "warehouse_name": branch.name,
                "critical": critical,
                "low": low,
                "healthy": healthy,
            })

        return result
