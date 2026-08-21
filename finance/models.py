from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from core.models import TimeStampedModel
from warehouse.models import Warehouse


class FinancialTransaction(TimeStampedModel):

    class Nature(models.TextChoices):
        INCOME = "INCOME", "Entrée"
        EXPENSE = "EXPENSE", "Sortie"

    class Source(models.TextChoices):
        INVOICE_PAYMENT = "INVOICE_PAYMENT", "Paiement facture"
        EXPENSE = "EXPENSE", "Dépense"
        REFUND = "REFUND", "Remboursement"
        CASH_ADJUSTMENT = "CASH_ADJUSTMENT", "Ajustement de caisse"
        OPENING_BALANCE = "OPENING_BALANCE", "Solde initial"
        OTHER = "OTHER", "Autre"

    reference = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
    )

    nature = models.CharField(
        max_length=10,
        choices=Nature.choices,
    )

    source = models.CharField(
        max_length=30,
        choices=Source.choices,
    )

    source_reference = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.01")),
        ],
    )

    transaction_date = models.DateTimeField()

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="financial_transactions",
    )

    description = models.TextField()

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="financial_transactions",
    )

    reversal_of = models.OneToOneField(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reversal_transaction",
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
        related_name="cancelled_financial_transactions",
    )

    cancellation_reason = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = [
            "-transaction_date",
            "-created_at",
        ]

    def __str__(self):
        return f"{self.reference} - {self.amount}"