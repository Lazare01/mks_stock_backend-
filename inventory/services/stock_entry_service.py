from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from supplier.models import Supplier
from warehouse.models import Warehouse

from inventory.models import (
    Product,
    StockEntry,
    StockEntryItem,
    InventoryStock,
    StockMovement,
    MovementType,
)

from inventory.constants import StockEntryStatus


class StockEntryService:
        
    # crée l'entrée de stock ;
    # génère la référence ;
    # réceptionne le stock ;
    # met à jour InventoryStock ;
    # crée les mouvements dans StockMovement ;
    # empêche une double réception ;
    # annule une entrée si nécessaire.

    @staticmethod
    @transaction.atomic
    def create_stock_entry(
        *,
        supplier_name,
        warehouse_id,
        invoice_number,
        expected_delivery_date=None,
        notes=None,
        items=None,
        created_by=None,
    ):

        supplier, _ = Supplier.objects.get_or_create(
            name=supplier_name
        )

        warehouse = Warehouse.objects.get(
            id=warehouse_id
        )

        reference = StockEntryService.generate_reference()

        stock_entry = StockEntry.objects.create(
            reference=reference,
            supplier=supplier,
            warehouse=warehouse,
            invoice_number=invoice_number,
            expected_delivery_date=expected_delivery_date,
            notes=notes,
        )

        for item in items:

            product = Product.objects.get(
                id=item["product_id"]
            )
            stock_item = StockEntryItem.objects.create(
                stock_entry=stock_entry,
                product=product,
                received_quantity=item["received_quantity"],
                unit_cost=item["unit_cost"],
            )

            stock, _ = InventoryStock.objects.get_or_create(
                product=product,
                warehouse=warehouse,
                defaults={"quantity": 0},
            )

            stock.quantity += stock_item.received_quantity

            stock.save(update_fields=["quantity"])

            StockMovement.objects.create(
                product=product,
                movement_type=MovementType.IN,
                to_warehouse=warehouse,
                quantity=stock_item.received_quantity,
                notes=f"Entrée {reference}",
            )
        
        stock_entry.status = StockEntryStatus.ACTIVE
        stock_entry.received_date = timezone.now()
        stock_entry.save()

        return stock_entry
    
        
            
            

    @staticmethod
    def generate_reference():

        year = timezone.now().year

        last_entry = (
            StockEntry.objects.filter(
                reference__startswith=f"ENT-{year}"
            )
            .order_by("-reference")
            .first()
        )

        if not last_entry:
            return f"ENT-{year}-000001"

        last_number = int(
            last_entry.reference.split("-")[-1]
        )

        return f"ENT-{year}-{last_number + 1:06d}"
    
    
    @staticmethod
    @transaction.atomic
    def cancel_stock_entry(
        *,
        stock_entry_id,
    ):
        stock_entry = (
        StockEntry.objects
        .select_related("warehouse")
        .prefetch_related(
            "items",
            "items__product"
        )
        .get(id=stock_entry_id)
    )
    
        if stock_entry.status == StockEntryStatus.CANCELLED:
            raise ValidationError(
                "Cette entrée est déjà annulée."
    )
        
        for item in stock_entry.items.all():

            stock = InventoryStock.objects.get(
                product=item.product,
                warehouse=stock_entry.warehouse,
            )

            if stock.quantity < item.received_quantity:
                raise ValidationError(
                    f"Impossible d'annuler l'entrée."
                    f" Stock insuffisant pour "
                    f"{item.product.name}"
                )

            stock.quantity -= item.received_quantity

            stock.save(update_fields=["quantity"])

            StockMovement.objects.create(
                product=item.product,
                movement_type=MovementType.OUT,
                from_warehouse=stock_entry.warehouse,
                quantity=item.received_quantity,
                notes=f"Annulation entrée {stock_entry.reference}",
            )
        stock_entry.status = StockEntryStatus.CANCELLED

        stock_entry.save(
    update_fields=[
        "status",
        "updated_at",
    ]
)