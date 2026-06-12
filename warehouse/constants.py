
from django.db import models


class WarehouseType(models.TextChoices):

    CENTRAL = "CENTRAL", "Stock Central"
    BRANCH = "BRANCH", "Agence"