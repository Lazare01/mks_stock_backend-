from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from core.permissions import CanManageStock
from inventory.models import Transfer

from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action

from inventory.fold_serializers.transfer_item import (
    TransferCreateSerializer,
    TransferDetailSerializer,
    TransferReceptionSerializer,
    TransferListSerializer,
  
)

# =================== services

from inventory.services.transfer_service import TransferItemService

from inventory.models import Product


class TransferViewSet(viewsets.ModelViewSet):

    permission_classes = [
        IsAuthenticated,
        CanManageStock,
    ]

    def get_queryset(self):

        return (
            Transfer.objects.select_related(
                "from_warehouse",
                "to_warehouse",
            )
            .prefetch_related(
                "items",
                "items__product",
            )
            .order_by("-created_at")
        )

    def get_serializer_class(self):

        if self.action == "create":
            return TransferCreateSerializer

        if self.action == "retrieve":
            return TransferDetailSerializer

        if self.action == "receive":
            return TransferReceptionSerializer

        return TransferListSerializer

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        transfer = TransferItemService.create_transfer(
            from_warehouse_id=serializer.validated_data["from_warehouse_id"],
            to_warehouse_id=serializer.validated_data["to_warehouse_id"],
            notes=serializer.validated_data.get("notes"),
            items=serializer.validated_data["items"],
        )

        return Response(
            TransferDetailSerializer(transfer).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="ship",
    )
    def ship(self, request, pk=None):

        transfer = TransferItemService.ship_transfer(
            transfer_id=pk,
        )

        return Response(TransferDetailSerializer(transfer).data)

    @action(
        detail=True,
        methods=["post"],
        url_path="receive",
    )
    def receive(self, request, pk=None):

        serializer = TransferReceptionSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        transfer = TransferItemService.receive_transfer(
            transfer_id=pk,
            items=serializer.validated_data["items"],
            notes=serializer.validated_data.get("notes"),
            received_by=request.user,
        )

        return Response(TransferDetailSerializer(transfer).data)

    @action(
        detail=True,
        methods=["post"],
        url_path="cancel",
    )
    def cancel(self, request, pk=None):

        transfer = TransferItemService.cancel_transfer(transfer_id=pk)

        return Response(TransferDetailSerializer(transfer).data)

