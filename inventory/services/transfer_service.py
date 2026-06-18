from django.db import transaction
from django.utils import timezone

from rest_framework.exceptions import ValidationError

from warehouse.models import Warehouse

from inventory.models import (
    Transfer,
    TransferItem,
    TransferStatus,
    InventoryStock,
    StockMovement,
    MovementType,
    Product
)


class ProductTransferService:

    @staticmethod
    def get_transfer_summary(
        *,
        product_id,
        warehouse_id,
    ):

        product = Product.objects.get(
            id=product_id
        )

        stock = (
            InventoryStock.objects
            .filter(
                product_id=product_id,
                warehouse_id=warehouse_id,
            )
            .first()
        )

        quantity = stock.quantity if stock else 0

        return {
            "product_id": product.id,
            "product_name": product.name,
            "available_stock": quantity,
        }

class TransferItemService:

    @staticmethod
    def generate_reference():

        year = timezone.now().year

        last_transfer = (
            Transfer.objects.filter(
                reference__startswith=f"TRF-{year}"
            )
            .order_by("-reference")
            .first()
        )

        if not last_transfer:
            return f"TRF-{year}-000001"

        last_number = int(
            last_transfer.reference.split("-")[-1]
        )

        return f"TRF-{year}-{last_number + 1:06d}"

    # ========================
    #  use product to transfer
    # ========================
    @staticmethod
    @transaction.atomic
    def create_transfer(
        *,
        from_warehouse_id,
        to_warehouse_id,
        initiated_by,
        notes=None,
        items=None,
    ):

        from_warehouse = Warehouse.objects.get(
            id=from_warehouse_id
        )

        to_warehouse = Warehouse.objects.get(
            id=to_warehouse_id
        )

        if from_warehouse.id == to_warehouse.id:
            raise ValidationError(
                "Le dépôt source et destination doivent être différents."
            )

        transfer = Transfer.objects.create(
            reference=TransferItemService.generate_reference(),
            from_warehouse=from_warehouse,
            to_warehouse=to_warehouse,
            notes=notes or "",
            status=TransferStatus.DRAFT,
            created_by=initiated_by
        )

        for item in items:

            TransferItem.objects.create(
                transfer=transfer,
                product_id=item["product_id"],
                quantity_sent=item["quantity_sent"],
            )

        return transfer

    @staticmethod
    @transaction.atomic
    def ship_transfer(
        *,
        transfer_id,
    ):

        transfer = (
            Transfer.objects
            .select_related(
                "from_warehouse",
                "to_warehouse",
            )
            .prefetch_related(
                "items",
                "items__product",
            )
            .get(id=transfer_id)
        )

        if transfer.status != TransferStatus.DRAFT:
            raise ValidationError(
                "Seul un transfert brouillon peut être expédié."
            )

        for item in transfer.items.all():

            stock = InventoryStock.objects.get(
                product=item.product,
                warehouse=transfer.from_warehouse,
            )

            if stock.quantity < item.quantity_sent:
                raise ValidationError(
                    f"Stock insuffisant pour "
                    f"{item.product.name}"
                )

            stock.quantity -= item.quantity_sent

            stock.save(
                update_fields=["quantity"]
            )

            StockMovement.objects.create(
                product=item.product,
                movement_type=MovementType.TRANSFER,
                from_warehouse=transfer.from_warehouse,
                to_warehouse=transfer.to_warehouse,
                quantity=item.quantity_sent,
                notes=f"Transfert {transfer.reference}",
            )

        transfer.status = TransferStatus.IN_TRANSIT

        transfer.shipped_at = timezone.now()

        transfer.save(
            update_fields=[
                "status",
                "shipped_at",
            ]
        )

        return transfer

    
    @staticmethod
    @transaction.atomic
    def cancel_transfer(
        *,
        transfer_id,
        cancelled_by
    ):

        transfer = (
            Transfer.objects
            .select_related(
                "from_warehouse",
                "to_warehouse",
            )
            .prefetch_related(
                "items",
                "items__product",
            )
            .get(id=transfer_id)
        )

        if transfer.status == TransferStatus.CANCELLED:
            raise ValidationError(
                "Ce transfert est déjà annulé."
            )

        if transfer.status == TransferStatus.RECEIVED:
            raise ValidationError(
                "Un transfert réceptionné ne peut pas être annulé."
            )

        # -----------------------
        # Cas DRAFT
        # -----------------------
        if transfer.status == TransferStatus.DRAFT:

            transfer.status = TransferStatus.CANCELLED
            transfer.cancelled_at = timezone.now()
            transfer.cancelled_by =cancelled_by

            transfer.save(
                update_fields=["status","cancelled_at","cancelled_by"]
            )

            return transfer

        # -----------------------
        # Cas IN_TRANSIT
        # -----------------------
        if transfer.status == TransferStatus.IN_TRANSIT:

            for item in transfer.items.all():

                stock, _ = (
                    InventoryStock.objects
                    .get_or_create(
                        product=item.product,
                        warehouse=transfer.from_warehouse,
                        defaults={
                            "quantity": 0
                        }
                    )
                )

                stock.quantity += item.quantity_sent

                stock.save(
                    update_fields=["quantity"]
                )

                StockMovement.objects.create(
                    product=item.product,
                    movement_type=MovementType.TRANSFER,
                    from_warehouse=transfer.to_warehouse,
                    to_warehouse=transfer.from_warehouse,
                    quantity=item.quantity_sent,
                    notes=(
                        f"Annulation transfert "
                        f"{transfer.reference}"
                    ),
                )

            transfer.status = TransferStatus.CANCELLED
            transfer.cancelled_at = timezone.now()
            transfer.cancelled_by =cancelled_by

            transfer.save(
                update_fields=["status","cancelled_at","cancelled_by"]
            )
           

            return transfer
