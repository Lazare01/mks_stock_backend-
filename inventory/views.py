from django.db.models import Count, Q

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from inventory.models import Warehouse,StockItemStatus
from inventory.serializers import WarehouseSerializer

from core.services.access_services import AccessService


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
                "stock_items",
                filter=Q(
                    stock_items__status=StockItemStatus.AVAILABLE
                )
            )

        ).prefetch_related(
            "manager_assignments__manager"
        )

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

        warehouse_ids = AccessService.get_user_warehouse_ids(
            user
        )

        # =====================================================
        # FILTRAGE SECURISE
        # =====================================================

        return queryset.filter(
            id__in=warehouse_ids
        )