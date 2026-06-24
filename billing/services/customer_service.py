# finance/services/customer_service.py
from billing.models import Customer


class CustomerService:

    @staticmethod
    def create_customer(**data):
        return Customer.objects.create(**data)