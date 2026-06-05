from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import viewsets, views, status
from rest_framework.response import Response

from rest_framework.permissions import IsAuthenticated

from inventory.models import Warehouse, StockItemStatus
from inventory.serializers import WarehouseSerializer

from core.services.access_services import AccessService
from core.permissions import CanUserManager

from core.models import UserWarehouseAccess,User
from core.constants.user_roles import UserRole

from .models import Warehouse, WarehouseType, ManagerAssignment


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
