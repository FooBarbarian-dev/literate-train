from django.urls import path
from audit.views import AuditEventListView

urlpatterns = [
    path("", AuditEventListView.as_view(), name="audit-list"),
]
