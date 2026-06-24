# finance/models/invoice.py

from django.db import models
from core.models import TimeStampedModel
from billing.models import Customer
from inventory.models import Warehouse
from django.conf import settings
from decimal import Decimal
from django.db.models import utils


class Invoice(TimeStampedModel):

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Brouillon"
        ISSUED = "ISSUED", "Emise"
        PARTIALLY_PAID = "PARTIALLY_PAID", "Partiellement payée"
        PAID = "PAID", "Payée"
        CANCELLED = "CANCELLED", "Annulée"

    reference = models.CharField(max_length=50, unique=True)

    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="invoices"
    )

    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name="invoices"
    )

    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    balance_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    status = models.CharField(
        max_length=30, choices=Status.choices, default=Status.DRAFT
    )

    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_invoices",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.reference
    
    @property
    def paid_amount(self):

        return (
            self.payments
            .filter(is_cancelled=False)
            .aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0")
        )
