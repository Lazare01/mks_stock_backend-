from rest_framework.serializers import ModelSerializer
from .models import Citys


class CitysSerializer(ModelSerializer):
    class Meta:
        model = Citys
        fields = ["id", "name"]
