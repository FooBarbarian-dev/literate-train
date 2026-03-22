import django_filters
from django.db import models
from logs.models import Log


class LogFilterSet(django_filters.FilterSet):
    hostname = django_filters.CharFilter(lookup_expr="icontains")
    internal_ip = django_filters.CharFilter(lookup_expr="exact")
    command = django_filters.CharFilter(lookup_expr="icontains")
    username = django_filters.CharFilter(lookup_expr="icontains")
    analyst = django_filters.CharFilter(lookup_expr="icontains")
    date_from = django_filters.DateTimeFilter(field_name="timestamp", lookup_expr="gte")
    date_to = django_filters.DateTimeFilter(field_name="timestamp", lookup_expr="lte")
    search = django_filters.CharFilter(method="filter_search")

    class Meta:
        model = Log
        fields = ["hostname", "internal_ip", "command", "username", "analyst"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            models.Q(hostname__icontains=value)
            | models.Q(command__icontains=value)
            | models.Q(username__icontains=value)
            | models.Q(notes__icontains=value)
            | models.Q(domain__icontains=value)
            | models.Q(filename__icontains=value)
        )
