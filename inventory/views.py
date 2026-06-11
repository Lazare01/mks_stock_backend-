from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from django.db.models import Count
from django.utils import timezone

from rest_framework import viewsets, views, status
from rest_framework.views import APIView
from rest_framework.response import Response

from rest_framework.permissions import IsAuthenticated

from warehouse.models import Warehouse,   Warehouse,WarehouseType, ManagerAssignment



from core.permissions import CanUserManager

from core.models import UserWarehouseAccess, User
from core.constants.user_roles import UserRole

from .models import (
  
    Product,
    StockEntry,
    StockMovement,
)


from supplier.models import Supplier
from supplier.serializers import SupplierSerializer

from core.permissions import CanManageStock


from inventory.serializers import (
    StockEntryCreateSerializer,
    StockEntryListSerializer,
    StockEntryDetailSerializer,
    ProductStockSummarySerializer,
    StockMovementSerializer,
    ProductSerializer,
    DashboardMovementSerializer
)

from inventory.services.stock_entry_service import (
    StockEntryService,
)

from inventory.constants import StockItemStatus

from inventory.services.stock_dash_service import DashboardMovementService

# ================================================================================================
# ================================================================================================
# ================================================================================================


# =========================================================
# PRODUCTS
# =========================================================


class ProductViewSet(viewsets.ModelViewSet):

    permission_classes = [IsAuthenticated, CanManageStock]

    serializer_class = ProductSerializer

    queryset = Product.objects.all().order_by("name")


# =============================================
# =================== Assigment views
# =============================================


class AssignBranchManagerView(views.APIView):

    permission_classes = [CanUserManager]

    def post(self, request, user_id):

        warehouse_id = request.data.get("warehouse_id")

        manager = get_object_or_404(User, id=user_id)

        warehouse = get_object_or_404(Warehouse, id=warehouse_id)

        if manager.role != UserRole.BRANCH_MGR:
            return Response(
                {
                    "detail": (
                        "Cet utilisateur n'est pas un " "gestionnaire de succursale."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if warehouse.warehouse_type != WarehouseType.BRANCH:
            return Response(
                {"detail": ("Le manager doit être affecté " "à une succursale.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ==========================================
        # Accès à la succursale
        # ==========================================

        UserWarehouseAccess.objects.update_or_create(
            user=manager,
            warehouse=warehouse,
            defaults={
                "can_view": True,
                "can_manage_stock": True,
                "can_transfer_stock": True,
                "can_manage_sales": True,
                "can_manage_installations": True,
                "is_active": True,
            },
        )

        # ==========================================
        # Affectation du manager
        # ==========================================

        assignment = ManagerAssignment.objects.create(
            manager=manager,
            warehouse=warehouse,
            start_date=timezone.now().date(),
            is_active=True,
        )

        return Response(
            {
                "message": "Manager affecté avec succès.",
                "assignment_id": assignment.id,
            },
            status=status.HTTP_201_CREATED,
        )


# =========================================================
# SUPPLIERS
# =========================================================


class SupplierViewSet(viewsets.ModelViewSet):

    queryset = Supplier.objects.all()

    serializer_class = SupplierSerializer

    permission_classes = [
        IsAuthenticated,
        CanManageStock,
    ]


# =========================================================
# STOCK ENTRY
# =========================================================


class StockEntryViewSet(viewsets.ModelViewSet):

    permission_classes = [
        IsAuthenticated,
        CanManageStock,
    ]

    def get_queryset(self):

        return (
            StockEntry.objects.select_related(
                "supplier",
                "warehouse",
            )
            .prefetch_related(
                "items",
                "items__product",
            )
            .order_by("-created_at")
        )

    def get_serializer_class(self):

        if self.action == "create":
            return StockEntryCreateSerializer

        if self.action == "retrieve":
            return StockEntryDetailSerializer

        return StockEntryListSerializer

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        stock_entry = StockEntryService.create_stock_entry(
            supplier_name=serializer.validated_data["supplier_name"],
            warehouse_id=serializer.validated_data["warehouse_id"],
            invoice_number=serializer.validated_data["invoice_number"],
            expected_delivery_date=serializer.validated_data.get(
                "expected_delivery_date"
            ),
            notes=serializer.validated_data.get("notes"),
            items=serializer.validated_data["items"],
            created_by=request.user,
        )

        return Response(
            StockEntryDetailSerializer(stock_entry).data,
            status=status.HTTP_201_CREATED,
        )

# =========================================================
# STOCK SUMMARY
# =========================================================



class StockEntryViewSetTest(viewsets.ModelViewSet):

    permission_classes = [
        IsAuthenticated,
        CanManageStock,
    ]

    def get_queryset(self):

        return StockEntry.objects.all()

    def get_serializer_class(self):

        if self.action == "create":
            return StockEntryCreateSerializer

        if self.action == "retrieve":
            return StockEntryDetailSerializer

        return StockEntryListSerializer




REORDER_THRESHOLD = 5

class StockSummaryView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        products = Product.objects.annotate(
            central_stock=Count(
                "stock_items",
                filter=Q(
                    stock_items__status=StockItemStatus.AVAILABLE,
                    stock_items__warehouse__warehouse_type=WarehouseType.CENTRAL,
                ),
            ),
            branch_stock=Count(
                "stock_items",
                filter=Q(
                    stock_items__status=StockItemStatus.AVAILABLE,
                    stock_items__warehouse__warehouse_type=WarehouseType.BRANCH,
                ),
            ),
        )

        results = []

        for product in products:

            total_stock = (
                product.central_stock +
                product.branch_stock
            )

            results.append(
                {
                    "id": product.id,
                    "name": product.name,
                    "sku": product.sku,
                    "category": product.get_category_display(),
                    "central_stock": product.central_stock,
                    "branch_stock": product.branch_stock,
                    "total_stock": total_stock,
                    "purchase_price": product.purchase_price,
                    "selling_price": product.selling_price,
                    "reorder_threshold": REORDER_THRESHOLD,
                    "needs_restock": total_stock < REORDER_THRESHOLD,
                }
            )

        serializer = ProductStockSummarySerializer(
            results,
            many=True,
        )

        return Response(serializer.data)

# =========================================================
# STOCK MOVEMENTS
# =========================================================


class StockMovementListView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):

        results = []

        movements = StockMovement.objects.select_related(
            "stock_item",
            "stock_item__product",
            "from_warehouse",
            "to_warehouse",
        ).order_by("-movement_date")[:200]

        for movement in movements:

            results.append(
                {
                    "id": movement.id,
                    "movement_type": movement.get_movement_type_display(),
                    "product_name": movement.stock_item.product.name,
                    "serial_number": movement.stock_item.serial_number,
                    "movement_date": movement.movement_date,
                    "from_warehouse": (
                        movement.from_warehouse.name
                        if movement.from_warehouse
                        else None
                    ),
                    "to_warehouse": (
                        movement.to_warehouse.name if movement.to_warehouse else None
                    ),
                }
            )

        serializer = StockMovementSerializer(
            results,
            many=True,
        )

        return Response(serializer.data)



class DashboardMovementListView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):

        data = (
            DashboardMovementService
            .get_latest_movements(limit=100)
        )

        serializer = DashboardMovementSerializer(
            data,
            many=True,
        )

        return Response(serializer.data)