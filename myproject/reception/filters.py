import django_filters
from django import forms
from django_filters import FilterSet
from .models import *


# class DetailedRecordListFilter(django_filters.FilterSet):
#     created_date__gte = django_filters.DateFilter(
#         field_name='created_date',
#         lookup_expr='date__gte',
#         widget=forms.DateInput(attrs={'type': 'date'})
#     )
#     created_date__lte = django_filters.DateFilter(
#         field_name='created_date',
#         lookup_expr='date__lte',
#         widget=forms.DateInput(attrs={'type': 'date'})
#     )
#
#     class Meta:
#         model = CustomerRecord
#         fields = ['created_date__gte', 'created_date__lte', 'doctor', 'department']


class CustomerRecordListFilter(FilterSet):
    created_date = django_filters.DateFilter(
        field_name='created_date',
        lookup_expr='date',
        widget=forms.DateInput(attrs={
            'type': 'date'
        })
    )

    class Meta:
        model = CustomerRecord
        fields = ['created_date', 'doctor']


class DoctorListFilter(FilterSet):
    class Meta:
        model = Doctor
        fields = {
            'departament': ['exact'],
        }
