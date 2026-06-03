from .serializers import CitysSerializer
from rest_framework.viewsets import ModelViewSet,ReadOnlyModelViewSet
from .models import Citys


class CitysViewSet(ReadOnlyModelViewSet):
    serializer_class=CitysSerializer
    def get_queryset(self):
         return Citys.objects.all()
     
