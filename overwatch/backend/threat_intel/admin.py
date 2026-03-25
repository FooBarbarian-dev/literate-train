"""
threat_intel admin — UX Audit 2026-03-25
========================================

Changes vs baseline:
- MitreTechniqueAdmin: added domain_badge, description_preview, fieldsets,
  date_hierarchy, show_full_result_count = False, Media css
- NvdCveAdmin: added severity_badge, affected_products_preview, fieldsets,
  list_select_related, Media css
- ChatSessionAdmin (NEW): session overview, SessionSourceInline, source_count,
  readonly thread_id, fieldsets
- SessionSourceAdmin (NEW): source_type_badge, clickable source_link,
  session_link back to parent, list_select_related

All classes reference the shared custom.css from the logs app.
"""

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from threat_intel.models import ChatSession, MitreTechnique, NvdCve, SessionSource

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CVSS_COLORS = [
    (9.0, "#991b1b", "#fee2e2"),   # Critical
    (7.0, "#c2410c", "#ffedd5"),   # High
    (4.0, "#854d0e", "#fef9c3"),   # Medium
    (0.1, "#166534", "#dcfce7"),   # Low
]


def _cvss_badge(score):
    """Return a colour-coded HTML pill for a CVSS score, or '–' if None."""
    if score is None:
        return "–"
    for threshold, fg, bg in _CVSS_COLORS:
        if score >= threshold:
            label = (
                "Critical" if score >= 9.0
                else "High" if score >= 7.0
                else "Medium" if score >= 4.0
                else "Low"
            )
            return format_html(
                '<span style="background:{bg};color:{fg};padding:2px 8px;'
                'border-radius:12px;font-size:0.78rem;font-weight:600;">'
                "{score:.1f} {label}</span>",
                bg=bg,
                fg=fg,
                score=score,
                label=label,
            )
    return format_html('<span style="color:#6b7280;">{}</span>', score)


_SOURCE_COLORS = {
    "mitre": ("#1e40af", "#dbeafe"),
    "nvd":   ("#7c3aed", "#ede9fe"),
    "db":    ("#374151", "#f3f4f6"),
}


def _source_type_badge(source_type, label=None):
    fg, bg = _SOURCE_COLORS.get(source_type, ("#374151", "#f3f4f6"))
    display = label or source_type.upper()
    return format_html(
        '<span style="background:{bg};color:{fg};padding:2px 8px;'
        'border-radius:12px;font-size:0.78rem;font-weight:600;">{display}</span>',
        bg=bg,
        fg=fg,
        display=display,
    )


# ---------------------------------------------------------------------------
# MitreTechnique
# ---------------------------------------------------------------------------

@admin.register(MitreTechnique)
class MitreTechniqueAdmin(admin.ModelAdmin):
    # ---- UX Audit ----
    list_display = (
        "external_id",
        "name",
        "domain_badge",
        "tactics",
        "platforms",
        "description_preview",
        "ingested_at",
    )
    list_filter = ("domain",)
    search_fields = ("external_id", "name", "description", "tactics", "platforms")
    readonly_fields = ("stix_id", "ingested_at")
    ordering = ("external_id",)
    date_hierarchy = "ingested_at"
    list_per_page = 100
    show_full_result_count = False

    fieldsets = (
        (
            "Identity",
            {
                "fields": ("external_id", "name", "domain", "stix_id"),
            },
        ),
        (
            "Classification",
            {
                "fields": ("tactics", "platforms"),
            },
        ),
        (
            "Detail",
            {
                "fields": ("description",),
                "classes": ("collapse",),
            },
        ),
        (
            "Audit",
            {
                "fields": ("ingested_at",),
                "classes": ("collapse",),
            },
        ),
    )

    class Media:
        css = {"all": ("admin/custom.css",)}

    @admin.display(description="Domain", ordering="domain")
    def domain_badge(self, obj):
        colors = {
            "enterprise-attack": ("#1d4ed8", "#dbeafe"),
            "mobile-attack":     ("#6d28d9", "#ede9fe"),
            "ics-attack":        ("#b45309", "#fef3c7"),
        }
        fg, bg = colors.get(obj.domain, ("#374151", "#f3f4f6"))
        label = obj.domain.replace("-attack", "").capitalize()
        return format_html(
            '<span style="background:{bg};color:{fg};padding:2px 8px;'
            'border-radius:12px;font-size:0.78rem;font-weight:600;">{label}</span>',
            bg=bg, fg=fg, label=label,
        )

    @admin.display(description="Description")
    def description_preview(self, obj):
        text = obj.description[:120]
        if len(obj.description) > 120:
            text += "…"
        return text


# ---------------------------------------------------------------------------
# NvdCve
# ---------------------------------------------------------------------------

@admin.register(NvdCve)
class NvdCveAdmin(admin.ModelAdmin):
    list_display = (
        "cve_id",
        "severity_badge",
        "published_date",
        "affected_products_preview",
        "ingested_at",
    )
    list_filter = ("published_date",)
    search_fields = ("cve_id", "description", "affected_products")
    readonly_fields = ("ingested_at",)
    ordering = ("-published_date", "cve_id")
    date_hierarchy = "published_date"
    list_per_page = 100
    show_full_result_count = False

    fieldsets = (
        (
            "Identity",
            {
                "fields": ("cve_id", "cvss_score", "published_date"),
            },
        ),
        (
            "Detail",
            {
                "fields": ("description", "affected_products"),
                "classes": ("collapse",),
            },
        ),
        (
            "Audit",
            {
                "fields": ("ingested_at",),
                "classes": ("collapse",),
            },
        ),
    )

    class Media:
        css = {"all": ("admin/custom.css",)}

    @admin.display(description="CVSS", ordering="cvss_score")
    def severity_badge(self, obj):
        return _cvss_badge(obj.cvss_score)

    @admin.display(description="Affected Products")
    def affected_products_preview(self, obj):
        lines = [ln.strip() for ln in obj.affected_products.splitlines() if ln.strip()]
        if not lines:
            return "—"
        preview = lines[0]
        if len(lines) > 1:
            preview += f"  (+{len(lines) - 1} more)"
        return preview


# ---------------------------------------------------------------------------
# SessionSource inline (used inside ChatSessionAdmin)
# ---------------------------------------------------------------------------

class SessionSourceInline(admin.TabularInline):
    model = SessionSource
    extra = 0
    can_delete = False
    fields = ("source_type", "record_id", "source_url", "retrieved_at")
    readonly_fields = ("source_type", "record_id", "source_url", "retrieved_at")
    ordering = ("retrieved_at",)
    show_change_link = True

    class Media:
        css = {"all": ("admin/custom.css",)}


# ---------------------------------------------------------------------------
# ChatSession
# ---------------------------------------------------------------------------

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "username",
        "thread_id",
        "source_count",
        "created_at",
        "updated_at",
    )
    list_filter = ("created_at", "updated_at")
    search_fields = ("name", "username")
    readonly_fields = ("thread_id", "created_at", "updated_at", "source_count")
    ordering = ("-updated_at",)
    date_hierarchy = "updated_at"
    list_per_page = 50
    show_full_result_count = False
    inlines = [SessionSourceInline]

    fieldsets = (
        (
            "Session",
            {
                "fields": ("name", "username"),
            },
        ),
        (
            "AI Thread",
            {
                "fields": ("thread_id",),
                "description": (
                    "Integer PK of the django-ai-assistant Thread backing this session.  "
                    "Null means the Thread was not created yet (will be created on first message)."
                ),
            },
        ),
        (
            "Stats",
            {
                "fields": ("source_count",),
                "classes": ("collapse",),
            },
        ),
        (
            "Audit",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    class Media:
        css = {"all": ("admin/custom.css",)}

    @admin.display(description="Sources")
    def source_count(self, obj):
        count = obj.sources.count()
        if count == 0:
            return "—"
        url = (
            reverse("admin:threat_intel_sessionsource_changelist")
            + f"?session__id__exact={obj.pk}"
        )
        return format_html('<a href="{url}">{count}</a>', url=url, count=count)


# ---------------------------------------------------------------------------
# SessionSource
# ---------------------------------------------------------------------------

@admin.register(SessionSource)
class SessionSourceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "session_link",
        "source_type_badge",
        "record_id",
        "source_link",
        "retrieved_at",
    )
    list_filter = ("source_type", "retrieved_at")
    search_fields = ("record_id", "session__name", "session__username")
    readonly_fields = (
        "session",
        "source_type",
        "record_id",
        "source_url",
        "retrieved_at",
        "session_link",
        "source_link",
    )
    ordering = ("-retrieved_at",)
    date_hierarchy = "retrieved_at"
    list_per_page = 100
    show_full_result_count = False
    list_select_related = ("session",)

    fieldsets = (
        (
            "Citation",
            {
                "fields": ("session_link", "source_type", "record_id", "source_link"),
            },
        ),
        (
            "Audit",
            {
                "fields": ("retrieved_at",),
                "classes": ("collapse",),
            },
        ),
    )

    class Media:
        css = {"all": ("admin/custom.css",)}

    @admin.display(description="Type", ordering="source_type")
    def source_type_badge(self, obj):
        labels = {
            "mitre": "MITRE ATT&CK",
            "nvd":   "NVD CVE",
            "db":    "DB",
        }
        return _source_type_badge(obj.source_type, labels.get(obj.source_type))

    @admin.display(description="URL")
    def source_link(self, obj):
        if not obj.source_url:
            return "—"
        return format_html(
            '<a href="{url}" target="_blank" rel="noopener">{url}</a>',
            url=obj.source_url,
        )

    @admin.display(description="Session", ordering="session__name")
    def session_link(self, obj):
        url = reverse("admin:threat_intel_chatsession_change", args=[obj.session_id])
        label = obj.session.name or f"Session #{obj.session_id}"
        return format_html('<a href="{url}">{label}</a>', url=url, label=label)
