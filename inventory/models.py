# =========================================================
# inventory/models.py
# =========================================================

import uuid
from django.db.models import Q
from django.db import models
from django.conf import settings
from core.models import TimeStampedModel
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from app.models import Citys
from supplier.models import Supplier
from warehouse.models import Warehouse
from .constants import StockEntryStatus,CategoryProduct,TransferStatus,TransferReceptionStatus



# fonction de generation automatique des skus




def generate_sku(category):
    prefix = CategoryProduct.sku_prefix(category)

    last_product = (
        Product.objects.filter(sku__startswith=prefix).order_by("-sku").first()
    )

    if not last_product:
        return f"{prefix}-000001"

    last_number = int(last_product.sku.split("-")[1])

    return f"{prefix}-{last_number + 1:06d}"

class Product(TimeStampedModel):
    """
    Produit générique.

    Exemple :
    - Kit Starlink
    - Routeur TP-Link
    """

    name = models.CharField(max_length=255)
    category = models.CharField(max_length=250, choices=CategoryProduct.choices)
    sku = models.CharField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_threshold = models.PositiveIntegerField(default=5)

    class Meta:
        db_table = "inventory_products"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):

        if not self.sku:
            self.sku = generate_sku(self.category)
            
        
        if self.pk:

            old_product = Product.objects.filter(pk=self.pk).first()

            if (
                old_product
                and old_product.selling_price != self.selling_price
            ):
                ProductPriceHistory.objects.create(
                    product=self,
                    old_price=old_product.selling_price,
                    new_price=self.selling_price,
                )

        super().save(*args, **kwargs)


# =========================================
#       -- product price history --
# =========================================


class ProductPriceHistory(TimeStampedModel):

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="price_history"
    )

    old_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    new_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    reason = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]


class MovementType(models.TextChoices):

    IN = "IN", "Entrée"
    OUT = "OUT", "Sortie"
    TRANSFER = "TRANSFER", "Transfert"


class StockMovement(TimeStampedModel):
    """
    Historique des mouvements de stock.

    Ce modèle sert à :
    - audit
    - historique
    - reporting
    """

    product = models.ForeignKey(Product,on_delete=models.PROTECT)

    movement_type = models.CharField(max_length=20, choices=MovementType.choices)

    from_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="outgoing_movements",
    )

    to_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="incoming_movements",
    )

    quantity = models.PositiveIntegerField()

    notes = models.TextField(blank=True)

    movement_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "inventory_stock_movements"

    def __str__(self):
        return f"{self.product.name} - " f"{self.movement_type} - " f"{self.quantity}"


# =========================================================
# ENTREES STOCK CENTRAL
# =========================================================




class StockEntry(TimeStampedModel):
    """
    Entrée de stock provenant d'un fournisseur.

    Exemple :

    Huawei
        ↓
    ENT-2026-000001
        ↓
    100 Kits Starlink
    """

    reference = models.CharField(
        max_length=50,
        unique=True,
    )

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="stock_entries",
    )

    warehouse = models.ForeignKey(
        "warehouse.Warehouse",
        on_delete=models.PROTECT,
        related_name="stock_entries",
    )

    invoice_number = models.CharField(
        max_length=150,
    )

    invoice_file = models.FileField(
        upload_to="supplier_invoices/",
        null=True,
        blank=True,
    )

    expected_delivery_date = models.DateField(
        null=True,
        blank=True,
    )

    received_date = models.DateTimeField(
        null=True,
        blank=True,
    )

    notes = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=StockEntryStatus.choices,
        default=StockEntryStatus.DRAFT,
    )

    class Meta:
        db_table = "inventory_stock_entries"

    def __str__(self):
        return self.reference


class StockEntryItem(TimeStampedModel):
    """
    Lignes d'une entrée de stock.
    """

    stock_entry = models.ForeignKey(
        StockEntry,
        on_delete=models.CASCADE,
        related_name="items",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="stock_entry_items",
    )

    received_quantity = models.PositiveIntegerField(default=0)

    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    class Meta:
        db_table = "inventory_stock_entry_items"

    @property
    def total_cost(self):
        return self.received_quantity * self.unit_cost

    def __str__(self):
        return f"{self.product.name}"


# ========================================================
#               -- inventory class --
# =======================================================


class InventoryStock(TimeStampedModel):

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="product_inventory",
    )

    warehouse = models.ForeignKey(
        "warehouse.Warehouse",
        on_delete=models.PROTECT,
        related_name="stocks",
    )

    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "inventory_stocks"

        unique_together = (
            "product",
            "warehouse",
        )

    def __str__(self):
        return f"{self.product.name} - " f"{self.warehouse.name} " f"({self.quantity})"





# =========================================================
# TRANSFERTS AGENCES
# =========================================================


class Transfer(TimeStampedModel):

    reference = models.CharField(
        max_length=50,
        unique=True,
    )

    from_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="outgoing_transfers",
    )

    to_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="incoming_transfers",
    )

    status = models.CharField(
        max_length=30,
        choices=TransferStatus.choices,
        default=TransferStatus.DRAFT,
    )

    shipped_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    received_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    class Meta:
        db_table = "inventory_transfers"

    def __str__(self):
        return self.reference
    
    
    
class TransferItem(TimeStampedModel):

    transfer = models.ForeignKey(
        Transfer,
        on_delete=models.CASCADE,
        related_name="items",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
    )

    quantity_sent = models.PositiveIntegerField()

    class Meta:
        db_table = "inventory_transfer_items"

    def __str__(self):
        return self.product.name
    
    
    
    
class TransferReception(TimeStampedModel):

    transfer = models.OneToOneField(
        Transfer,
        on_delete=models.PROTECT,
        related_name="reception",
    )

    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="validated_receptions",
    )

    notes = models.TextField(
        blank=True,
    )

    class Meta:
        db_table = "inventory_transfer_receptions"





class TransferReceptionItem(TimeStampedModel):

    reception = models.ForeignKey(
        TransferReception,
        on_delete=models.CASCADE,
        related_name="items",
    )

    transfer_item = models.ForeignKey(
        TransferItem,
        on_delete=models.PROTECT,
        related_name="reception_items",
    )

    quantity_received = models.PositiveIntegerField()

    status = models.CharField(
        max_length=20,
        choices=TransferReceptionStatus.choices,
    )

    notes = models.TextField(
        blank=True,
    )

    class Meta:
        db_table = "inventory_transfer_reception_items"