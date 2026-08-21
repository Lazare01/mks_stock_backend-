from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from billing.models import Invoice
from billing.models import Payment, PaymentMethod
from finance.models import FinancialTransaction


class PaymentService:

    # ============================================================
    # REFERENCES
    # ============================================================

    @staticmethod
    def generate_payment_reference():
        """
        Génère :
        PAY-2026-000001
        PAY-2026-000002
        ...
        """

        year = timezone.now().year
        prefix = f"PAY-{year}-"

        last_payment = (
            Payment.objects
            .filter(reference__startswith=prefix)
            .order_by("-created_at")
            .first()
        )

        if not last_payment:
            sequence = 1
        else:
            try:
                sequence = int(
                    last_payment.reference.split("-")[-1]
                ) + 1
            except (ValueError, IndexError):
                sequence = (
                    Payment.objects
                    .filter(reference__startswith=prefix)
                    .count()
                    + 1
                )

        return f"{prefix}{sequence:06d}"

    @staticmethod
    def generate_financial_reference():
        """
        Génère :
        FIN-2026-000001
        FIN-2026-000002
        ...
        """

        year = timezone.now().year
        prefix = f"FIN-{year}-"

        last_transaction = (
            FinancialTransaction.objects
            .filter(reference__startswith=prefix)
            .order_by("-created_at")
            .first()
        )

        if not last_transaction:
            sequence = 1
        else:
            try:
                sequence = int(
                    last_transaction.reference.split("-")[-1]
                ) + 1
            except (ValueError, IndexError):
                sequence = (
                    FinancialTransaction.objects
                    .filter(reference__startswith=prefix)
                    .count()
                    + 1
                )

        return f"{prefix}{sequence:06d}"

    # ============================================================
    # VALIDATION DU MONTANT
    # ============================================================

    @staticmethod
    def _normalize_amount(amount):
        try:
            amount = Decimal(str(amount))
        except (InvalidOperation, TypeError, ValueError):
            raise ValidationError({
                "amount": "Montant invalide."
            })

        if amount <= Decimal("0"):
            raise ValidationError({
                "amount": "Le montant doit être supérieur à zéro."
            })

        return amount

    # ============================================================
    # MISE À JOUR DU STATUT DE LA FACTURE
    # ============================================================

    @staticmethod
    def _update_invoice_status(invoice):
        """
        Calcule automatiquement le statut de la facture
        selon les paiements actifs.
        """

        paid_amount = invoice.paid_amount
        total_amount = invoice.total_amount

        if paid_amount <= Decimal("0.00"):

            invoice.status = Invoice.Status.ISSUED

        elif paid_amount < total_amount:

            invoice.status = Invoice.Status.PARTIALLY_PAID

        else:

            invoice.status = Invoice.Status.PAID

        invoice.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return invoice

    # ============================================================
    # CREATION PAIEMENT
    # ============================================================

    @staticmethod
    @transaction.atomic
    def create_payment(
        *,
        invoice,
        payment_method,
        amount,
        received_by,
        payment_date=None,
        notes="",
    ):

        # --------------------------------------------------------
        # 1. Verrouillage facture
        # --------------------------------------------------------

        invoice = (
            Invoice.objects
            .select_for_update()
            .select_related(
                "customer",
                "warehouse",
            )
            .get(pk=invoice.pk)
        )

        # --------------------------------------------------------
        # 2. Validation statut facture
        # --------------------------------------------------------

        if invoice.status == Invoice.Status.DRAFT:
            raise ValidationError(
                "Impossible d'enregistrer un paiement "
                "sur une facture brouillon."
            )

        if invoice.status == Invoice.Status.CANCELLED:
            raise ValidationError(
                "Impossible d'enregistrer un paiement "
                "sur une facture annulée."
            )

        # --------------------------------------------------------
        # 3. Méthode de paiement
        # --------------------------------------------------------

        if not payment_method:
            raise ValidationError({
                "payment_method":
                    "Une méthode de paiement est obligatoire."
            })

        if not payment_method.is_active:
            raise ValidationError({
                "payment_method":
                    "Cette méthode de paiement est désactivée."
            })

        # --------------------------------------------------------
        # 4. Montant
        # --------------------------------------------------------

        amount = PaymentService._normalize_amount(amount)

        balance_due = invoice.balance_due

        if balance_due <= Decimal("0.00"):
            raise ValidationError(
                "Cette facture est déjà totalement payée."
            )

        if amount > balance_due:
            raise ValidationError({
                "amount": (
                    f"Le montant du paiement ({amount}) "
                    f"dépasse le solde restant ({balance_due})."
                )
            })

        # --------------------------------------------------------
        # 5. Date
        # --------------------------------------------------------

        if payment_date is None:
            payment_date = timezone.now()

        # --------------------------------------------------------
        # 6. Création paiement
        # --------------------------------------------------------

        payment_reference = (
            PaymentService.generate_payment_reference()
        )

        payment = Payment.objects.create(
            reference=payment_reference,
            invoice=invoice,
            payment_method=payment_method,
            amount=amount,
            payment_date=payment_date,
            notes=notes or "",
            received_by=received_by,
        )

        # --------------------------------------------------------
        # 7. Création transaction financière
        # --------------------------------------------------------

        financial_reference = (
            PaymentService.generate_financial_reference()
        )

        FinancialTransaction.objects.create(
            reference=financial_reference,

            nature=FinancialTransaction.Nature.INCOME,

            source=(
                FinancialTransaction.Source.INVOICE_PAYMENT
            ),

            source_reference=payment.reference,

            amount=payment.amount,

            transaction_date=payment.payment_date,

            warehouse=invoice.warehouse,

            description=(
                f"Paiement {payment.reference} "
                f"de la facture {invoice.reference}"
            ),

            created_by=received_by,
        )

        # --------------------------------------------------------
        # 8. Mise à jour facture
        # --------------------------------------------------------

        PaymentService._update_invoice_status(invoice)

        return payment

    # ============================================================
    # ANNULATION PAIEMENT
    # ============================================================

    @staticmethod
    @transaction.atomic
    def cancel_payment(
        *,
        payment,
        cancelled_by,
        reason,
    ):

        # --------------------------------------------------------
        # 1. Validation raison
        # --------------------------------------------------------

        if not reason or not reason.strip():
            raise ValidationError({
                "reason":
                    "Une raison d'annulation est obligatoire."
            })

        # --------------------------------------------------------
        # 2. Verrouillage paiement
        # --------------------------------------------------------

        payment = (
            Payment.objects
            .select_for_update()
            .select_related(
                "invoice",
                "invoice__warehouse",
                "payment_method",
                "received_by",
            )
            .get(pk=payment.pk)
        )

        # --------------------------------------------------------
        # 3. Vérifier annulation existante
        # --------------------------------------------------------

        if payment.is_cancelled:
            raise ValidationError(
                "Ce paiement est déjà annulé."
            )

        # --------------------------------------------------------
        # 4. Verrouillage facture
        # --------------------------------------------------------

        invoice = (
            Invoice.objects
            .select_for_update()
            .get(pk=payment.invoice_id)
        )

        # --------------------------------------------------------
        # 5. Retrouver transaction financière originale
        # --------------------------------------------------------

        original_transaction = (
            FinancialTransaction.objects
            .select_for_update()
            .filter(
                source=(
                    FinancialTransaction
                    .Source
                    .INVOICE_PAYMENT
                ),
                source_reference=payment.reference,
            )
            .first()
        )

        if not original_transaction:
            raise ValidationError(
                "La transaction financière correspondant "
                "à ce paiement est introuvable."
            )

        # --------------------------------------------------------
        # 6. Vérifier si remboursement existe déjà
        # --------------------------------------------------------

        already_reversed = (
            FinancialTransaction.objects
            .filter(
                reversal_of=original_transaction
            )
            .exists()
        )

        if already_reversed:
            raise ValidationError(
                "La transaction financière de ce paiement "
                "a déjà été annulée."
            )

        # --------------------------------------------------------
        # 7. Annuler paiement
        # --------------------------------------------------------

        payment.is_cancelled = True
        payment.cancelled_at = timezone.now()
        payment.cancelled_by = cancelled_by
        payment.cancellation_reason = reason.strip()

        payment.save(
            update_fields=[
                "is_cancelled",
                "cancelled_at",
                "cancelled_by",
                "cancellation_reason",
                "updated_at",
            ]
        )

        # --------------------------------------------------------
        # 8. Transaction financière inverse
        # --------------------------------------------------------

        reversal_reference = (
            PaymentService.generate_financial_reference()
        )

        FinancialTransaction.objects.create(
            reference=reversal_reference,

            nature=FinancialTransaction.Nature.EXPENSE,

            source=FinancialTransaction.Source.REFUND,

            source_reference=payment.reference,

            amount=payment.amount,

            transaction_date=timezone.now(),

            warehouse=invoice.warehouse,

            description=(
                f"Annulation du paiement "
                f"{payment.reference} "
                f"- Facture {invoice.reference}. "
                f"Motif : {reason.strip()}"
            ),

            created_by=cancelled_by,

            reversal_of=original_transaction,
        )

        # --------------------------------------------------------
        # IMPORTANT
        # --------------------------------------------------------
        #
        # Nous NE mettons PAS :
        #
        # original_transaction.is_cancelled = True
        #
        # Pourquoi ?
        #
        # Parce que le grand livre doit conserver :
        #
        # + 500   paiement
        # - 500   remboursement
        #
        # = 0
        #
        # Si nous supprimions/excluions comptablement
        # la transaction originale, nous obtiendrions -500.
        #
        # --------------------------------------------------------

        # --------------------------------------------------------
        # 9. Recalcul statut facture
        # --------------------------------------------------------

        PaymentService._update_invoice_status(invoice)

        return payment