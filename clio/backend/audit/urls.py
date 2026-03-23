from django.urls import path
from audit.views import AuditEventListView

app_name = "audit"

urlpatterns = [
    path("", AuditEventListView.as_view(), name="audit-list"),
]
