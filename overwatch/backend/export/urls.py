from django.urls import path
from export.views import ExportJSONView, ExportCSVView
from export.htmx_views import export_page

app_name = "export"

urlpatterns = [
    path("", export_page, name="export-page"),
    path("json/", ExportJSONView.as_view(), name="export-json"),
    path("csv/", ExportCSVView.as_view(), name="export-csv"),
]
