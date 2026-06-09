from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from rest_framework.exceptions import ValidationError

from supplier.models import Supplier

from inventory.models import (
    Warehouse,
    WarehouseType,
    Product,
    StockEntry,
    StockEntryItem,
    StockEntryStatus,
    StockItem,
    StockItemStatus,
    StockMovement,
    MovementType,
)


class StockEntryService:
    """
    Service métier.

    Gestion :

    - Création entrée fournisseur
    - Réception entrée fournisseur
    - Création StockItem
    - Création StockMovement
    """

    @staticmethod
    def generate_reference():

        year = timezone.now().year

        last_entry = (
            StockEntry.objects.filter(reference__startswith=f"ENT-{year}")
            .order_by("-created_at")
            .first()
        )

        if not last_entry:
            return f"ENT-{year}-000001"

        try:

            last_number = int(last_entry.reference.split("-")[-1])

        except Exception:
            last_number = 0

        next_number = last_number + 1

        return f"ENT-{year}-{next_number:06d}"
    
    
    @staticmethod
    def validate_serials(serials):

        if not serials:
            raise ValidationError(
                "Au moins un numéro de série est requis."
            )

        serial_numbers = set()

        for serial in serials:

            serial_number = (
                serial.get("serial_number", "")
                .strip()
            )

            if not serial_number:
                raise ValidationError(
                    "Le numéro de série est obligatoire."
                )

            if serial_number in serial_numbers:
                raise ValidationError(
                    f"Numéro de série dupliqué : {serial_number}"
                )

            serial_numbers.add(serial_number)

            # Vérifier qu'il n'existe pas déjà en stock
            if StockItem.objects.filter(
                serial_number=serial_number
            ).exists():
                raise ValidationError(
                    f"Le numéro de série '{serial_number}' existe déjà."
                )

    # Création entrée fournisseur

    @staticmethod
    @transaction.atomic
    def create_stock_entry(
        *,
        supplier_name,
        warehouse_id,
        invoice_number,
        expected_delivery_date,
        notes,
        items,
        created_by,
    ):

        supplier, _ = Supplier.objects.get_or_create(
            name=supplier_name.strip(),
            defaults={
                "is_active": True,
            },
        )
        
        print(" ")
        print(items)
        print(" ")

        warehouse = Warehouse.objects.filter(
            id=warehouse_id
        ).first()

        if not warehouse:
            raise ValidationError(
                "Entrepôt introuvable."
            )

        if warehouse.warehouse_type != WarehouseType.CENTRAL:
            raise ValidationError(
                "L'entrée fournisseur doit être faite vers le stock central."
            )

        stock_entry = StockEntry.objects.create(
            reference=StockEntryService.generate_reference(),
            supplier=supplier,
            warehouse=warehouse,
            invoice_number=invoice_number,
            expected_delivery_date=expected_delivery_date,
            received_date=timezone.now(),
            notes=notes,
            created_by=created_by,
            status=StockEntryStatus.RECEIVED,
        )

        for item in items:

            product = Product.objects.filter(
                id=item["product_id"]
            ).first()

            if not product:
                raise ValidationError(
                    f"Produit introuvable : {item['product_id']}"
                )

            if not product.is_serialized:
                raise ValidationError(
                    f"{product.name} : les produits non sérialisés ne sont pas encore supportés."
                )

            serials = item["serials"]

            StockEntryService.validate_serials(
                serials
            )

            entry_item = StockEntryItem.objects.create(
                stock_entry=stock_entry,
                product=product,
                received_quantity=item["received_quantity"],
                unit_cost=item["unit_cost"],
                created_by=created_by,
            )

            for serial_data in serials:

                stock_item = StockItem.objects.create(
                    product=product,
                    warehouse=warehouse,
                    serial_number=serial_data[
                        "serial_number"
                    ].strip(),
                    mac_address=(
                        serial_data.get(
                            "mac_address"
                        ) or None
                    ),
                    status=StockItemStatus.AVAILABLE,
                    created_by=created_by,
                )

                StockMovement.objects.create(
                    stock_item=stock_item,
                    movement_type=MovementType.IN,
                    to_warehouse=warehouse,
                    notes=(
                        f"Entrée fournisseur "
                        f"{stock_entry.reference}"
                    ),
                    created_by=created_by,
                )

        return stock_entry