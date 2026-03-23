from django.urls import path
from ingest.views import BulkIngestView, CSVIngestView

app_name = "ingest"

urlpatterns = [
    path("bulk/", BulkIngestView.as_view(), name="ingest-bulk"),
    path("csv/", CSVIngestView.as_view(), name="ingest-csv"),
]
