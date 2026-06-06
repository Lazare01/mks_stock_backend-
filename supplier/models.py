from django.db import models
from core.models import TimeStampedModel

# =========================================================
# FOURNISSEURS
# =========================================================

class Supplier(TimeStampedModel):
    """
    Fournisseur de matériel.

    Exemple :

    - Huawei
    - Starlink
    - TP-Link
    - Mikrotik

    IMPORTANT :
    Même si la saisie est manuelle aujourd'hui,
    nous conservons les fournisseurs afin :

    - d'avoir l'historique des achats
    - d'éviter les doublons
    - de préparer les statistiques futures
    """

    name = models.CharField(
        max_length=255,
        unique=True,
    )

    contact_person = models.CharField(
        max_length=255,
        blank=True,
    )

    phone_number = models.CharField(
        max_length=50,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    address = models.TextField(
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        db_table = "inventory_suppliers"
        ordering = ["name"]

    def __str__(self):
        return self.name
