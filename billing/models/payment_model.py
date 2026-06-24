from django.db import models
from core.models import TimeStampedModel
from core.models import User
from billing.models import Invoice


class PaymentMethod(TimeStampedModel):

    name = models.CharField(
        max_length=100,
        unique=True
    )

    is_active = models.BooleanField(
        default=True
    )

    def __str__(self):
        return self.name
    


class Payment(TimeStampedModel):

    reference = models.CharField(
        max_length=50,
        unique=True
    )

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name="payments"
    )

    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    payment_date = models.DateTimeField()

    notes = models.TextField(
        blank=True
    )

    received_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT
    )

    is_cancelled = models.BooleanField(
        default=False
    )