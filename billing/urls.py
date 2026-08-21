from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomerViewSet,
    ServiceViewSet,
    ExpenseCategoryViewSet,
    ExpenseViewSet,

    PaymentViewSet,
    PaymentMethodViewSet,
)


router = DefaultRouter()


router.register(
    r"customers",
    CustomerViewSet,
    basename="customers",
)

router.register(
    r"services",
    ServiceViewSet,
    basename="services",
)

router.register(
    r"expense-categories",
    ExpenseCategoryViewSet,
    basename="expense-category",
)

router.register(
    r"expenses",
    ExpenseViewSet,
    basename="expense",
)

router.register(
    r"payment-methods",
    PaymentMethodViewSet,
    basename="payment-method",
)

router.register(
    r"payments",
    PaymentViewSet,
    basename="payment",
)


urlpatterns = [
    path(
        "",
        include(router.urls),
    ),
]