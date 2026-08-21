from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from billing.models.expense import Expense
from billing.serializers.expense_serializer import ExpenseSerializer
from billing.services.expense_service import ExpenseService


class ExpenseViewSet(viewsets.ModelViewSet):

    queryset = (
        Expense.objects
        .select_related(
            "warehouse",
            "category",
            "created_by",
            "approved_by",
            "cancelled_by",
        )
    )

    serializer_class = ExpenseSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    @action(
        detail=True,
        methods=["post"],
        url_path="approve",
    )
    def approve(self, request, pk=None):

        expense = self.get_object()

        expense = ExpenseService.approve_expense(
            expense=expense,
            approved_by=request.user,
        )

        serializer = self.get_serializer(expense)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="cancel",
    )
    def cancel(self, request, pk=None):

        expense = self.get_object()

        reason = request.data.get("reason", "")

        expense = ExpenseService.cancel_expense(
            expense=expense,
            cancelled_by=request.user,
            reason=reason,
        )

        serializer = self.get_serializer(expense)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )