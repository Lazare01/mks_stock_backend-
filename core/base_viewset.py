# core/base_viewsets.py

from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet


class SoftDeleteModelViewSet(ModelViewSet):

    def destroy(self, request, *args, **kwargs):

        instance = self.get_object()

        instance.soft_delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )