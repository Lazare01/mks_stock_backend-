
from django.db import models

class StockEntryStatus(models.TextChoices):

    DRAFT = "DRAFT", "Brouillon"

    ACTIVE = "RECEIVED", "Réceptionné"

    CANCELLED = "CANCELLED", "Annulé"
    


class StockItemStatus(models.TextChoices):

    AVAILABLE = "AVAILABLE", "Disponible"
    # En transfert entre agences
    IN_TRANSIT = "IN_TRANSIT", "En transit"

    SOLD = "SOLD", "Vendu"

    INSTALLED = "INSTALLED", "Installé"

    DAMAGED = "DAMAGED", "Endommagé"



class CategoryProduct(models.TextChoices):
    NETWORK = "NETWORK", "Equipements reseaux"
    ACCESSORY = "ACCESSORY", "Accessoires"
    AUTRES = "AUTRES", "Autres"

    @classmethod
    def sku_prefix(cls, category):
        mapping = {cls.NETWORK: "EQR", cls.ACCESSORY: "ACC", cls.AUTRES: "PRD"}
        return mapping.get(category, "PRD")


class TransferStatus(models.TextChoices):

    DRAFT = "DRAFT", "Brouillon"

    IN_TRANSIT = "IN_TRANSIT", "En transit"

    PARTIALLY_RECEIVED = (
        "PARTIALLY_RECEIVED",
        "Réception partielle",
    )

    RECEIVED = "RECEIVED", "Réceptionné"

    CANCELLED = "CANCELLED", "Annulé"



class TransferReceptionStatus(models.TextChoices):

    RECEIVED = (
        "RECEIVED",
        "Reçu"
    )

    MISSING = (
        "MISSING",
        "Manquant"
    )

    DAMAGED = (
        "DAMAGED",
        "Endommagé"
    )