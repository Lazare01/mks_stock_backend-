from django.db import models

from core.models import TimeStampedModel


class ExpenseCategory(TimeStampedModel):
    name = models.CharField(
        max_length=100,
        unique=True,
    )

    description = models.TextField(
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Expense Category"
        verbose_name_plural = "Expense Categories"

    def __str__(self):
        return self.name
    
    
""""
EXEMPLE /  


Transport
Carburant
Loyer
Électricité
Internet
Salaires
Marketing
Fournitures
Maintenance
Autres

"""