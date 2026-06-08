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


class Category(models.TextChoices):
    KIT_STANDARD = "KIT_STANDARD", "kit standard"
    KIT_MINI = "KIT_MINI", "kit mini"
    AUTRES = "AUTRES","Autres"
    
    @classmethod
    def sku_prefix(cls, category):
        mapping = {
            cls.KIT_STANDARD: "KIT",
            cls.KIT_MINI: "MINI",
            cls.AUTRES : "PRD"
        }
        return mapping.get(category, "PRD")


# fonction de generation automatique des skus 


def generate_sku(category):
        prefix = Category.sku_prefix(category)

        last_product = (
            Product.objects
            .filter(sku__startswith=prefix)
            .order_by("-sku")
            .first()
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

    category = models.CharField(max_length=250, choices=Category.choices)

    sku = models.CharField(max_length=100, unique=True,blank=True)

    description = models.TextField(blank=True,null=True)

    purchase_price = models.DecimalField(max_digits=12, decimal_places=2,default=0)
    
    is_serialized = models.BooleanField(
        default=True,
        verbose_name="Produit sérialisé"
    )


    selling_price = models.DecimalField(max_digits=12, decimal_places=2,default=0)

    class Meta:
        db_table = "inventory_products"

    def __str__(self):
        return self.name
        
    def save(self, *args, **kwargs):

        if not self.sku:
            self.sku = generate_sku(self.category)

        super().save(*args, **kwargs)


class ManagerAssignment(TimeStampedModel):
    """
    Historique des affectations des managers.

    Pourquoi ce modèle est important ?

    Dans un vrai ERP :
    - un manager peut changer d'agence
    - une agence peut changer de manager
    - on doit garder l'historique

    Exemple :
    Janvier :
        Jean -> Kinshasa

    Mars :
        Jean -> Kolwezi

    On ne doit JAMAIS perdre cette information.
    """

    manager = models.ForeignKey(
        "core.User", on_delete=models.PROTECT, related_name="manager_assignments"
    )

    warehouse = models.ForeignKey(
        "inventory.Warehouse",
        on_delete=models.PROTECT,
        related_name="manager_assignments",
    )

    start_date = models.DateField()

    # Null = affectation encore active
    end_date = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = "inventory_manager_assignments"

        ordering = ["-start_date"]

        constraints = [
            # =================================================
            # Une seule affectation active par agence
            # =================================================
            models.UniqueConstraint(
                fields=["warehouse"],
                condition=Q(is_active=True),
                name="unique_active_manager_per_warehouse",
            ),
            # =================================================
            # Un manager ne peut gérer
            # qu'une seule agence active
            # =================================================
            models.UniqueConstraint(
                fields=["manager"],
                condition=Q(is_active=True),
                name="unique_active_warehouse_per_manager",
            ),
        ]

    def __str__(self):
        return f"{self.manager} -> {self.warehouse}"

    def save(self, *args, **kwargs):

        if self.is_active:

            # Désactive anciennes affectations du manager
            ManagerAssignment.objects.filter(
                manager=self.manager, is_active=True
            ).exclude(pk=self.pk).update(
                is_active=False, end_date=timezone.now().date()
            )

            # Désactive anciens managers du warehouse
            ManagerAssignment.objects.filter(
                warehouse=self.warehouse, is_active=True
            ).exclude(pk=self.pk).update(
                is_active=False, end_date=timezone.now().date()
            )

        super().save(*args, **kwargs)


class WarehouseType(models.TextChoices):

    CENTRAL = "CENTRAL", "Stock Central"
    BRANCH = "BRANCH", "Agence"


class Warehouse(TimeStampedModel):
    """
    Entrepôt ou agence.

    Exemple :
    - Lubumbashi Central
    - Kinshasa Branch
    """

    name = models.CharField(max_length=255, unique=True)

    warehouse_type = models.CharField(max_length=20, choices=WarehouseType.choices)

    city = models.ForeignKey(Citys, verbose_name=_("citys"), on_delete=models.PROTECT)

    address = models.TextField(blank=True, null=True)

    status = models.BooleanField(default=True)

    class Meta:
        db_table = "inventory_warehouses"

    def __str__(self):
        return self.name

    @property
    def available_stock(self):
        """
        Retourne le stock disponible.

        IMPORTANT :
        Les kits en transit NE doivent PAS apparaître.
        """

        return self.stock_items.filter(status=StockItemStatus.AVAILABLE).count()

    def available_product_stock(self, product):
        """
        Stock disponible pour un produit précis.
        """

        return self.stock_items.filter(
            product=product, status=StockItemStatus.AVAILABLE
        ).count()

    @property
    def current_manager(self):

        assignment = (
            self.manager_assignments.filter(is_active=True)
            .select_related("manager")
            .first()
        )

        if assignment:
            return assignment.manager

        return None


class StockItemStatus(models.TextChoices):

    AVAILABLE = "AVAILABLE", "Disponible"
    # En transfert entre agences
    IN_TRANSIT = "IN_TRANSIT", "En transit"

    SOLD = "SOLD", "Vendu"

    INSTALLED = "INSTALLED", "Installé"

    DAMAGED = "DAMAGED", "Endommagé"


class StockItem(TimeStampedModel):
    """
    Représente un kit physique unique.

    Chaque kit possède :
    - un serial number
    - éventuellement une MAC address
    """

    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="stock_items"
    )

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="stock_items",
        null=True,
        blank=True,
    )

    serial_number = models.CharField(max_length=255)

    mac_address = models.CharField(max_length=100, null=True, blank=True, unique=True)

    status = models.CharField(
        max_length=20,
        choices=StockItemStatus.choices,
        default=StockItemStatus.AVAILABLE,
    )

    class Meta:
        db_table = "inventory_stock_items"

        # IMPORTANT :
        # Empêche deux kits avec même serial
        # dans un même warehouse.
        unique_together = ("warehouse", "serial_number")

    def __str__(self):
        return f"{self.product.name} - {self.serial_number}"


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

    stock_item = models.ForeignKey(
        StockItem, on_delete=models.PROTECT, related_name="movements"
    )

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

    notes = models.TextField(blank=True)

    movement_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "inventory_stock_movements"

    def __str__(self):
        return f"{self.movement_type} - {self.stock_item.serial_number}"


# =========================================================
# ENTREES STOCK CENTRAL
# =========================================================


class StockEntryStatus(models.TextChoices):

    DRAFT = "DRAFT", "Brouillon"

    RECEIVED = "RECEIVED", "Réceptionné"

    CANCELLED = "CANCELLED", "Annulé"


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
        "inventory.Warehouse",
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

    notes = models.TextField(
        blank=True,
    )

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

    quantity = models.PositiveIntegerField()
    
  

    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    class Meta:
        db_table = "inventory_stock_entry_items"

    @property
    def total_cost(self):
        return self.quantity * self.unit_cost

    def __str__(self):
        return f"{self.product.name}"


# =========================================================
# TRANSFERTS AGENCES
# =========================================================


class TransferStatus(models.TextChoices):

    DRAFT = "DRAFT", "Brouillon"

    IN_TRANSIT = "IN_TRANSIT", "En transit"

    PARTIALLY_RECEIVED = (
        "PARTIALLY_RECEIVED",
        "Réception partielle",
    )

    RECEIVED = "RECEIVED", "Réceptionné"

    CANCELLED = "CANCELLED", "Annulé"


class Transfer(TimeStampedModel):
    """
    Réapprovisionnement agence.

    Central
        ↓
    Agence
    """

    reference = models.CharField(
        max_length=50,
        unique=True,
    )

    from_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="created_transfers",
    )

    to_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="received_transfers",
    )

    notes = models.TextField(
        blank=True,
    )

    shipped_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    received_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=30,
        choices=TransferStatus.choices,
        default=TransferStatus.DRAFT,
    )

    class Meta:
        db_table = "inventory_transfers"

    def __str__(self):
        return self.reference


class TransferItem(TimeStampedModel):
    """
    Kits envoyés dans un transfert.
    """

    transfer = models.ForeignKey(
        Transfer,
        on_delete=models.CASCADE,
        related_name="items",
    )

    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.PROTECT,
        related_name="transfer_items",
    )

    class Meta:
        db_table = "inventory_transfer_items"

        unique_together = (
            "transfer",
            "stock_item",
        )


class TransferReceptionStatus(models.TextChoices):

    RECEIVED = "RECEIVED", "Reçu"

    MISSING = "MISSING", "Manquant"

    DAMAGED = "DAMAGED", "Endommagé"


# =================================
# Document de validation agence.
# =================================


class TransferReception(TimeStampedModel):
    """
    Validation de réception
    par le manager agence.
    """

    transfer = models.OneToOneField(
        Transfer,
        on_delete=models.PROTECT,
        related_name="reception",
    )

    notes = models.TextField(
        blank=True,
    )

    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="validated_receptions",
    )

    class Meta:
        db_table = "inventory_transfer_receptions"


# =================================
# Gestion des réceptions partielles.
# =================================


class TransferReceptionItem(TimeStampedModel):
    """
    Résultat de contrôle
    de chaque kit reçu.
    """

    reception = models.ForeignKey(
        TransferReception,
        on_delete=models.CASCADE,
        related_name="items",
    )

    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.PROTECT,
    )

    status = models.CharField(
        max_length=20,
        choices=TransferReceptionStatus.choices,
    )

    notes = models.TextField(
        blank=True,
    )

    class Meta:
        db_table = "inventory_transfer_reception_items"
