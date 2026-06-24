# finance/models/invoice_line.py

from django.db import models
from core.models import TimeStampedModel
from inventory.models import Product
from billing.models import Service,Invoice



class InvoiceLine(TimeStampedModel):

    class LineType(models.TextChoices):
        PRODUCT = "PRODUCT", "Produit"
        SERVICE = "SERVICE", "Service"

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="lines"
    )

    line_type = models.CharField(
        max_length=20,
        choices=LineType.choices
    )

    product = models.ForeignKey(
        Product,
        null=True,
        blank=True,
        on_delete=models.PROTECT
    )

    service = models.ForeignKey(
        Service,
        null=True,
        blank=True,
        on_delete=models.PROTECT
    )

    description = models.CharField(
        max_length=255
    )

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )