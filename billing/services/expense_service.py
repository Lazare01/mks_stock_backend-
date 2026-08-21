from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from billing.models.expense import Expense
from billing.models.expense_category  import ExpenseCategory


class ExpenseService:

    @staticmethod
    def generate_reference():
        year = timezone.now().year

        last_expense = (
            Expense.objects
            .filter(reference__startswith=f"EXP-{year}-")
            .order_by("-created_at")
            .first()
        )

        if not last_expense:
            sequence = 1
        else:
            try:
                sequence = int(last_expense.reference.split("-")[-1]) + 1
            except (ValueError, IndexError):
                sequence = Expense.objects.filter(
                    reference__startswith=f"EXP-{year}-"
                ).count() + 1

        return f"EXP-{year}-{sequence:06d}"

    @staticmethod
    @transaction.atomic
    def create_expense(
        *,
        warehouse,
        category,
        amount,
        expense_date,
        description,
        created_by,
        notes="",
    ):
        if amount <= 0:
            raise ValidationError(
                "Le montant de la dépense doit être supérieur à zéro."
            )

        if not category.is_active:
            raise ValidationError(
                "Cette catégorie de dépense est désactivée."
            )

        reference = ExpenseService.generate_reference()

        expense = Expense.objects.create(
            reference=reference,
            warehouse=warehouse,
            category=category,
            amount=amount,
            expense_date=expense_date,
            description=description,
            created_by=created_by,
            notes=notes,
            status=Expense.Status.DRAFT,
        )

        return expense

    @staticmethod
    @transaction.atomic
    def approve_expense(
        *,
        expense,
        approved_by,
    ):
        if expense.status == Expense.Status.CANCELLED:
            raise ValidationError(
                "Une dépense annulée ne peut pas être approuvée."
            )

        if expense.status == Expense.Status.APPROVED:
            raise ValidationError(
                "Cette dépense est déjà approuvée."
            )

        expense.status = Expense.Status.APPROVED
        expense.approved_by = approved_by
        expense.approved_at = timezone.now()

        expense.save(
            update_fields=[
                "status",
                "approved_by",
                "approved_at",
                "updated_at",
            ]
        )

        # FinancialTransaction sera créée ici
        # lorsque le Module 5 sera implémenté.

        return expense

    @staticmethod
    @transaction.atomic
    def cancel_expense(
        *,
        expense,
        cancelled_by,
        reason,
    ):
        if expense.status == Expense.Status.CANCELLED:
            raise ValidationError(
                "Cette dépense est déjà annulée."
            )

        if not reason or not reason.strip():
            raise ValidationError(
                "Une raison est obligatoire pour annuler une dépense."
            )

        expense.status = Expense.Status.CANCELLED
        expense.cancelled_by = cancelled_by
        expense.cancelled_at = timezone.now()
        expense.cancellation_reason = reason

        expense.save(
            update_fields=[
                "status",
                "cancelled_by",
                "cancelled_at",
                "cancellation_reason",
                "updated_at",
            ]
        )

        return expense