# finance/models/service.py

from django.db import models
from core.models import TimeStampedModel


class Service(TimeStampedModel):

    name = models.CharField(
        max_length=255,
        unique=True
    )

    description = models.TextField(
        blank=True,null=True
    )

    default_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    is_active = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name