from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from billing.models.expense_category import ExpenseCategory
from billing.serializers.expense_category_serializer import ExpenseCategorySerializer


class ExpenseCategoryViewSet(viewsets.ModelViewSet):

    queryset = ExpenseCategory.objects.all()

    serializer_class = ExpenseCategorySerializer

    permission_classes = [
        IsAuthenticated,
    ]