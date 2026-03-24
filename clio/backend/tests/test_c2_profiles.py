"""Tests for C2 log profile generators."""

import pytest

from ingest.c2_profiles import PROFILES
from ingest.c2_profiles.sliver import generate_session_logs as sliver_generate
from ingest.c2_profiles.cobalt_strike import generate_session_logs as cs_generate


# Fields every log entry must have (matching Log model)
REQUIRED_FIELDS = {
    "timestamp_offset_hours",
    "hostname",
    "command",
    "notes",
    "analyst",
    "op",
    "tags",
    "status",
}


class TestProfileRegistry:
    def test_profiles_registered(self):
        assert "sliver" in PROFILES
        assert "cobalt-strike" in PROFILES

    def test_profile_has_required_keys(self):
        for key, profile in PROFILES.items():
            assert "name" in profile, f"{key} missing 'name'"
            assert "description" in profile, f"{key} missing 'description'"
            assert "default_operation" in profile, f"{key} missing 'default_operation'"
            assert "generate" in profile, f"{key} missing 'generate'"
            assert callable(profile["generate"]), f"{key} 'generate' not callable"


class TestSliverProfile:
    def test_generates_logs(self):
        logs = sliver_generate()
        assert len(logs) > 0

    def test_log_entry_structure(self):
        logs = sliver_generate()
        for i, entry in enumerate(logs):
            for field in REQUIRED_FIELDS:
                assert field in entry, f"Sliver log[{i}] missing field '{field}'"

    def test_tags_are_lists_of_strings(self):
        logs = sliver_generate()
        for entry in logs:
            assert isinstance(entry["tags"], list)
            for tag in entry["tags"]:
                assert isinstance(tag, str)

    def test_includes_sliver_tag(self):
        logs = sliver_generate()
        all_tags = set()
        for entry in logs:
            all_tags.update(entry["tags"])
        assert "sliver" in all_tags

    def test_covers_attack_lifecycle(self):
        logs = sliver_generate()
        all_tags = set()
        for entry in logs:
            all_tags.update(entry["tags"])
        # Should cover key phases
        expected_phases = {
            "initial-access",
            "discovery",
            "privilege-escalation",
            "credential-access",
            "lateral-movement",
            "command-and-control",
            "persistence",
        }
        assert expected_phases.issubset(all_tags)

    def test_chronological_order(self):
        logs = sliver_generate()
        offsets = [e["timestamp_offset_hours"] for e in logs]
        assert offsets == sorted(offsets)

    def test_custom_parameters(self):
        logs = sliver_generate(
            analyst="custom-analyst",
            operation_name="CUSTOM OP",
        )
        for entry in logs:
            assert entry["analyst"] == "custom-analyst"
            assert entry["op"] == "CUSTOM OP"


class TestCobaltStrikeProfile:
    def test_generates_logs(self):
        logs = cs_generate()
        assert len(logs) > 0

    def test_log_entry_structure(self):
        logs = cs_generate()
        for i, entry in enumerate(logs):
            for field in REQUIRED_FIELDS:
                assert field in entry, f"CS log[{i}] missing field '{field}'"

    def test_includes_cobalt_strike_tag(self):
        logs = cs_generate()
        all_tags = set()
        for entry in logs:
            all_tags.update(entry["tags"])
        assert "cobalt-strike" in all_tags

    def test_covers_attack_lifecycle(self):
        logs = cs_generate()
        all_tags = set()
        for entry in logs:
            all_tags.update(entry["tags"])
        expected_phases = {
            "initial-access",
            "discovery",
            "privilege-escalation",
            "credential-access",
            "lateral-movement",
            "command-and-control",
            "persistence",
            "defense-evasion",
            "exfiltration",
        }
        assert expected_phases.issubset(all_tags)

    def test_chronological_order(self):
        logs = cs_generate()
        offsets = [e["timestamp_offset_hours"] for e in logs]
        assert offsets == sorted(offsets)

    def test_includes_file_hashes(self):
        """CS profile should include payload hash for at least one entry."""
        logs = cs_generate()
        has_hash = any(e.get("hash_value") for e in logs)
        assert has_hash
