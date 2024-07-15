import django_filters
from core.models import *


class UserFilter(django_filters.FilterSet):
    class Meta:
        model = User
        fields = {
            'email': ['icontains'],
            'first_name': ['icontains'],
            'last_name': ['icontains'],
            'user_type': ['exact'],
            'username': ['icontains'],

        }


class TransactionFilter(django_filters.FilterSet):
    class Meta:
        model = Transaction
        fields = {
            'customer_account_number': ['icontains'],
            'transaction_code': ['exact'],
            'transaction_type': ['exact'],
            'transaction_status': ['exact'],
            'utilised': ['exact']
        }
