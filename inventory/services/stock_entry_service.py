from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from rest_framework.exceptions import ValidationError

from supplier.models import Supplier

from warehouse.models import Warehouse, WarehouseType

from inventory.models import (
    Product,
    StockEntry,
    StockEntryItem,
    StockEntryStatus,
    StockMovement,
    MovementType,
)

from inventory.constants import StockItemStatus


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
        supplier_name,
        warehouse_id,
        invoice_number,
        expected_delivery_date,
        notes,
        items,
        created_by,
    ):
        pass
