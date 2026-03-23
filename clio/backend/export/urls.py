from django.urls import path
from export.views import ExportJSONView, ExportCSVView

app_name = "export"

urlpatterns = [
    path("json/", ExportJSONView.as_view(), name="export-json"),
    path("csv/", ExportCSVView.as_view(), name="export-csv"),
]
