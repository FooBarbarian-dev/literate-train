from django.urls import path

from threat_intel.views import ChatAPIView, MitreFacetsView, MitreTechniqueListView, NvdCveListView

app_name = "threat_intel"

urlpatterns = [
    path("api/chat/", ChatAPIView.as_view(), name="threat-intel-chat-api"),
    path("api/threat-intel/mitre/", MitreTechniqueListView.as_view(), name="mitre-list"),
    path("api/threat-intel/mitre/facets/", MitreFacetsView.as_view(), name="mitre-facets"),
    path("api/threat-intel/cves/", NvdCveListView.as_view(), name="cve-list"),
]
