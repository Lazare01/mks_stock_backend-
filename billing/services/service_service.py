# finance/services/service_service.py

from billing.models import Service


class ServiceCatalogService:

    @staticmethod
    def create_service(**data):
        return Service.objects.create(**data)