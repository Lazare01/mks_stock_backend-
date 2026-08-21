from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from billing.models import Payment,PaymentMethod
from billing.serializers.payment_serializer import PaymentSerializer,PaymentMethodSerializer
from billing.serializers.payment_cancel_serializer import PaymentCancelSerializer
from billing.services.payment_service import PaymentService





class PaymentMethodViewSet(viewsets.ModelViewSet):

    queryset = (
        PaymentMethod.objects
        .all()
        .order_by("name")
    )

    serializer_class = PaymentMethodSerializer

    permission_classes = [
        IsAuthenticated,
    ]




class PaymentViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):

    serializer_class = PaymentSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    queryset = (
        Payment.objects
        .select_related(
            "invoice",
            "invoice__customer",
            "invoice__warehouse",
            "payment_method",
            "received_by",
            "cancelled_by",
        )
        .order_by(
            "-payment_date",
            "-created_at",
        )
    )

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.validated_data

        payment = PaymentService.create_payment(
            invoice=data["invoice"],
            payment_method=data["payment_method"],
            amount=data["amount"],
            payment_date=data.get("payment_date"),
            notes=data.get("notes", ""),
            received_by=request.user,
        )

        serializer = self.get_serializer(
            payment
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="cancel",
    )
    def cancel(self, request, pk=None):

        payment = self.get_object()

        serializer = PaymentCancelSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        payment = PaymentService.cancel_payment(
            payment=payment,
            cancelled_by=request.user,
            reason=serializer.validated_data[
                "reason"
            ],
        )

        output_serializer = self.get_serializer(
            payment
        )

        return Response(
            output_serializer.data,
            status=status.HTTP_200_OK,
        )