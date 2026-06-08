from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from django.db.models import Count
from django.utils import timezone

from rest_framework import viewsets, views, status
from rest_framework.views import APIView
from rest_framework.response import Response

from rest_framework.permissions import IsAuthenticated

from inventory.models import Warehouse, StockItemStatus
from inventory.serializers import WarehouseSerializer

from core.services.access_services import AccessService
from core.permissions import CanUserManager

from core.models import UserWarehouseAccess, User
from core.constants.user_roles import UserRole

from .models import (
    Warehouse,
    WarehouseType,
    ManagerAssignment,
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
)

from inventory.services.stock_entry_service import (
    StockEntryService,
)

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


class WarehouseViewSet(viewsets.ModelViewSet):

    permission_classes = [IsAuthenticated]

    serializer_class = WarehouseSerializer

    def get_queryset(self):

        user = self.request.user

        # =====================================================
        # QUERYSET DE BASE
        # =====================================================

        queryset = Warehouse.objects.annotate(
            available_stock_count=Count(
                "stock_items", filter=Q(stock_items__status=StockItemStatus.AVAILABLE)
            )
        ).prefetch_related("manager_assignments__manager")

        # =====================================================
        # SUPER ADMIN
        # =====================================================

        if user.is_superuser:
            return queryset

        # =====================================================
        # SUPER ADMIN
        # =====================================================

        if user.role == "CENTRAL_MGR":
            return queryset

        # =====================================================
        # IDS DES AGENCES AUTORISEES
        # =====================================================

        warehouse_ids = AccessService.get_user_warehouse_ids(user)

        # =====================================================
        # FILTRAGE SECURISE
        # =====================================================

        return queryset.filter(id__in=warehouse_ids)


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


class StockSummaryView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):

        results = []

        products = Product.objects.select_related("category").all()

        for product in products:

            central_stock = product.stock_items.filter(
                status=StockItemStatus.AVAILABLE,
                warehouse__warehouse_type=WarehouseType.CENTRAL,
            ).count()

            branch_stock = product.stock_items.filter(
                status=StockItemStatus.AVAILABLE,
                warehouse__warehouse_type=WarehouseType.BRANCH,
            ).count()

            results.append(
                {
                    "id": product.id,
                    "name": product.name,
                    "sku": product.sku,
                    "category": product.category.name,
                    "central_stock": central_stock,
                    "branch_stock": branch_stock,
                    "purchase_price": product.purchase_price,
                    "selling_price": product.selling_price,
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
                    "movement_type": movement.movement_type,
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
