"""
C2 log profile generators for realistic red-team demo data.

Each profile module exposes a ``generate_session_logs()`` function that returns
a list of dicts matching the ``Log`` model fields.  Profiles are registered in
``PROFILES`` so the ``seed_c2_logs`` management command can discover them.
"""

from ingest.c2_profiles.sliver import PROFILE as SLIVER_PROFILE
from ingest.c2_profiles.cobalt_strike import PROFILE as COBALT_STRIKE_PROFILE

PROFILES = {
    "sliver": SLIVER_PROFILE,
    "cobalt-strike": COBALT_STRIKE_PROFILE,
}
