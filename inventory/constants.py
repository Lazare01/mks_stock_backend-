
from django.db import models

class StockEntryStatus(models.TextChoices):

    DRAFT = "DRAFT", "Brouillon"

    RECEIVED = "RECEIVED", "Réceptionné"

    CANCELLED = "CANCELLED", "Annulé"
    


class StockItemStatus(models.TextChoices):

    AVAILABLE = "AVAILABLE", "Disponible"
    # En transfert entre agences
    IN_TRANSIT = "IN_TRANSIT", "En transit"

    SOLD = "SOLD", "Vendu"

    INSTALLED = "INSTALLED", "Installé"

    DAMAGED = "DAMAGED", "Endommagé"

