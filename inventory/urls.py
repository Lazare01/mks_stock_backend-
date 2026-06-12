from django.urls import path, include

from rest_framework.routers import DefaultRouter

from inventory.views import (
  
    SupplierViewSet,
    StockEntryViewSet,
    StockMovementListView,
    ProductViewSet,
    DashboardMovementListView,
    DashboardInventoryStockListView
    
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