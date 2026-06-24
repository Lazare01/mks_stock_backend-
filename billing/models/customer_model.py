# finance/models/customer.py

from django.db import models
from core.models import TimeStampedModel

                             
class Customer(TimeStampedModel):

    class CustomerType(models.TextChoices):
        INDIVIDUAL = "INDIVIDUAL", "Particulier"
        COMPANY = "COMPANY", "Entreprise"

    name = models.CharField(
        max_length=255
    )

    customer_type = models.CharField(
        max_length=20,
        choices=CustomerType.choices,
        default=CustomerType.INDIVIDUAL
    )

    phone = models.CharField(
        max_length=50,
        blank=True
    )

    email = models.EmailField(
        blank=True
    )

    address = models.TextField(
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    notes = models.TextField(
        blank=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name