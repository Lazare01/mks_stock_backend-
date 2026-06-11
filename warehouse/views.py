from django.shortcuts import render
from rest_framework import viewsets
from .models import Warehouse
from rest_framework.permissions import IsAuthenticated
from .serializers import WarehouseSerializer
from core.services.access_services import AccessService

# Create your views here.


class WarehouseViewSet(viewsets.ModelViewSet):

    permission_classes = [IsAuthenticated]

    serializer_class = WarehouseSerializer

    def get_queryset(self):

        user = self.request.user

        # =====================================================
        # QUERYSET DE BASE
        # =====================================================

        queryset = Warehouse.objects.all()
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

