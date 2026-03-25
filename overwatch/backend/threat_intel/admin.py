from django.contrib import admin

from threat_intel.models import MitreTechnique, NvdCve


@admin.register(MitreTechnique)
class MitreTechniqueAdmin(admin.ModelAdmin):
    list_display = ("external_id", "name", "domain", "tactics", "platforms", "ingested_at")
    list_filter = ("domain", "ingested_at")
    search_fields = ("external_id", "name", "description", "tactics", "platforms")
    readonly_fields = ("stix_id", "ingested_at")
    ordering = ("external_id",)


@admin.register(NvdCve)
class NvdCveAdmin(admin.ModelAdmin):
    list_display = ("cve_id", "cvss_score", "published_date", "ingested_at")
    list_filter = ("published_date", "ingested_at")
    search_fields = ("cve_id", "description", "affected_products")
    readonly_fields = ("ingested_at",)
    ordering = ("-published_date", "cve_id")
    date_hierarchy = "published_date"
