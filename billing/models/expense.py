from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from core.models import TimeStampedModel
from billing.models.expense_category import ExpenseCategory
from warehouse.models import Warehouse


class Expense(TimeStampedModel):

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Brouillon"
        APPROVED = "APPROVED", "Approuvée"
        CANCELLED = "CANCELLED", "Annulée"

    reference = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
    )

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="expenses",
    )

    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.PROTECT,
        related_name="expenses",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.01")),
        ],
    )

    expense_date = models.DateField()

    description = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_expenses",
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="approved_expenses",
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="cancelled_expenses",
    )

    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    cancellation_reason = models.TextField(
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = [
            "-expense_date",
            "-created_at",
        ]

    def __str__(self):
        return f"{self.reference} - {self.amount}"