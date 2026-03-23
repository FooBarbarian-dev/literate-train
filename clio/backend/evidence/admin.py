from django.contrib import admin
from evidence.models import EvidenceFile


@admin.register(EvidenceFile)
class EvidenceFileAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "log", "file_type",
                    "file_size", "uploaded_by", "upload_date")
    list_filter = ("file_type", "upload_date")
    search_fields = ("original_filename", "uploaded_by", "description")
    readonly_fields = ("upload_date", "md5_hash", "filepath", "filename")
    raw_id_fields = ("log",)
