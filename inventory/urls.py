from django.urls import path, include

from rest_framework.routers import DefaultRouter

from inventory.views import (
    SupplierViewSet,
    StockEntryViewSet,
    StockMovementListView,
    ProductViewSet,
    DashboardMovementListView,
    DashboardInventoryStockListView,
    DashsStockBranchInventory,
    TransferViewSet
)

router = DefaultRouter()



router.register(
    r"suppliers",
    SupplierViewSet,
    basename="supplier",
)

router.register(
    r"stock-entries",
    StockEntryViewSet,
    basename="stock-entry",
)

router.register(
    r"products",
    ProductViewSet,
    basename="products",
)


router.register(
    r"transfers",
    TransferViewSet,
    basename="transfers",
)

urlpatterns = [
    path(
        "dash-stock/movements/",
        DashboardMovementListView.as_view(),
        name="dashboard-movements",
    ),
    path(
        "stock-inventory/",
        DashboardInventoryStockListView.as_view(),
        name="stock-summary",
    ),path
        (  "stock-branch-summary/",
        DashsStockBranchInventory.as_view(),
        name="stock-branch-summary",
    ),
    path(
    "stock-movements/",
    StockMovementListView.as_view(),
    name="stock-movements",
),
    path(
        "",
        include(router.urls),
    ),
]