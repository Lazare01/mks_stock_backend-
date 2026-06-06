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

    # Création entrée fournisseur

    @staticmethod
    @transaction.atomic
    def create_stock_entry(
        *,
        supplier_id,
        warehouse_id,
        invoice_number,
        expected_delivery_date,
        notes,
        items,
        created_by,
    ):

        # Validation fournisseur

        supplier = Supplier.objects.filter(
            id=supplier_id,
            is_active=True,
        ).first()

        if not supplier:
            raise ValidationError("Fournisseur introuvable.")

        # Validation warehouse

        warehouse = Warehouse.objects.filter(
            id=warehouse_id,
        ).first()

        if not warehouse:
            raise ValidationError("Entrepôt introuvable.")

        if warehouse.warehouse_type != WarehouseType.CENTRAL:
            raise ValidationError(
                "L'entrée fournisseur doit être faite vers le stock central."
            )

        # Création document

        stock_entry = StockEntry.objects.create(
            reference=StockEntryService.generate_reference(),
            supplier=supplier,
            warehouse=warehouse,
            invoice_number=invoice_number,
            expected_delivery_date=expected_delivery_date,
            notes=notes,
            created_by=created_by,
            status=StockEntryStatus.DRAFT,
        )
        
        # Création lignes
        
        for item in items:

            product = Product.objects.filter(
                id=item["product_id"]
            ).first()

            if not product:
                raise ValidationError(
                    f"Produit introuvable : {item['product_id']}"
                )

            StockEntryItem.objects.create(
                stock_entry=stock_entry,
                product=product,
                quantity=item["quantity"],
                unit_cost=item["unit_cost"],
                created_by=created_by,
            )
        return stock_entry
    
    # Validation Serial
    
    @staticmethod
    def validate_serials(serials):
        # Vérification doublons payload
        payload_serials = set()

        for row in serials:

            serial = row["serial_number"].strip()

            if serial in payload_serials:

                raise ValidationError(
                    f"Serial dupliqué : {serial}"
                )

            payload_serials.add(serial)
    
        # Vérification base
        
        existing_serials = StockItem.objects.filter(
        serial_number__in=payload_serials
            )

        if existing_serials.exists():

            serial = existing_serials.first().serial_number

            raise ValidationError(
            f"Le serial {serial} existe déjà."
            )
    
    # Réception entrée fournisseur
    
    @staticmethod
    @transaction.atomic
    def receive_stock_entry(
        *,
        stock_entry,
        items,
        notes,
        user,
    ):
        if stock_entry.status != StockEntryStatus.DRAFT:

            raise ValidationError(
                "Cette entrée a déjà été réceptionnée."
            )
    
    
    # Index lignes commande
    
        entry_items = {
        str(item.product_id): item
        for item in stock_entry.items.all()
        }
    
    # Boucle produits reçus
        for received_product in items:

            product_id = str(
                received_product["product_id"]
            )

            if product_id not in entry_items:

                raise ValidationError(
                    "Produit non présent dans la commande."
                )

            entry_item = entry_items[product_id]

            serials = received_product["serials"]
            
            # Validation quantité
            
            if len(serials) != entry_item.quantity:
                raise ValidationError(
                    f"{entry_item.product.name} : "
                    f"{entry_item.quantity} serial(s) attendu(s), "
                    f"{len(serials)} reçu(s)."
                )
            
            # Validation serials
            
            StockEntryService.validate_serials(
                serials
            )
            
            # Création StockItem
            
            for serial_data in serials:

                stock_item = StockItem.objects.create(
                    product=entry_item.product,
                    warehouse=stock_entry.warehouse,
                    serial_number=serial_data["serial_number"],
                    mac_address=serial_data.get(
                        "mac_address"
                    )
                    or None,
                    status=StockItemStatus.AVAILABLE,
                    created_by=user,
                )
            
            # Mouvement stock
            
            StockMovement.objects.create(
                    stock_item=stock_item,
                    movement_type=MovementType.IN,
                    to_warehouse=stock_entry.warehouse,
                    notes=f"Entrée fournisseur {stock_entry.reference}",
                    created_by=user,
                )