from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from core.models import TimeStampedModel
from billing.models import Invoice


class PaymentMethod(TimeStampedModel):

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Payment(TimeStampedModel):

    reference = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
    )

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name="payments",
    )

    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT,
        related_name="payments",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.01")),
        ],
    )

    payment_date = models.DateTimeField()

    notes = models.TextField(
        blank=True,
    )

    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="received_payments",
    )

    is_cancelled = models.BooleanField(
        default=False,
    )

    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="cancelled_payments",
    )

    cancellation_reason = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = [
            "-payment_date",
            "-created_at",
        ]

    def __str__(self):
        return f"{self.reference} - {self.amount}"