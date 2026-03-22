"""Tests for the accounts module: validators, sanitizers, hashers."""
import pytest
from rest_framework.exceptions import ValidationError

from accounts.validators import (
    validate_username,
    validate_password,
    validate_ip_address,
    normalize_mac_address,
    validate_password_input,
)
from accounts.sanitizers import (
    sanitize_strict,
    sanitize_permissive,
    sanitize_username_field,
    sanitize_field,
)
from accounts.hashers import hash_password, verify_password


# ---------------------------------------------------------------------------
# Username validation
# ---------------------------------------------------------------------------

class TestValidateUsername:
    def test_valid_usernames(self):
        assert validate_username("alice") == "alice"
        assert validate_username("Bob_123") == "Bob_123"
        assert validate_username("op-lead") == "op-lead"

    def test_too_short(self):
        with pytest.raises(ValidationError):
            validate_username("ab")

    def test_starts_with_digit(self):
        with pytest.raises(ValidationError):
            validate_username("1user")

    def test_empty(self):
        with pytest.raises(ValidationError):
            validate_username("")

    def test_special_chars(self):
        with pytest.raises(ValidationError):
            validate_username("user@name")


# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------

class TestValidatePassword:
    GOOD_PASSWORD = "S3cure!Pass_x"

    def test_valid_password(self):
        assert validate_password(self.GOOD_PASSWORD) == self.GOOD_PASSWORD

    def test_too_short(self):
        with pytest.raises(ValidationError, match="12 characters"):
            validate_password("Sh0rt!x")

    def test_too_long(self):
        with pytest.raises(ValidationError, match="128"):
            validate_password("A1!" + "x" * 126)

    def test_missing_uppercase(self):
        with pytest.raises(ValidationError, match="uppercase"):
            validate_password("nouppercase1!")

    def test_missing_lowercase(self):
        with pytest.raises(ValidationError, match="lowercase"):
            validate_password("NOLOWERCASE1!")

    def test_missing_digit(self):
        with pytest.raises(ValidationError, match="digit"):
            validate_password("NoDigitHere!!")

    def test_missing_special(self):
        with pytest.raises(ValidationError, match="special"):
            validate_password("NoSpecial1234")

    def test_letters_then_numbers_only(self):
        with pytest.raises(ValidationError, match="letters followed by numbers"):
            validate_password("Abcdefghij12")

    def test_consecutive_chars(self):
        with pytest.raises(ValidationError, match="consecutive"):
            validate_password("Passssword1!x")

    def test_sql_injection_blocked(self):
        with pytest.raises(ValidationError, match="disallowed"):
            validate_password("Good1!Pass--x")

    def test_xss_blocked(self):
        with pytest.raises(ValidationError, match="disallowed"):
            validate_password("Good1!<script>")


# ---------------------------------------------------------------------------
# IP validation
# ---------------------------------------------------------------------------

class TestValidateIpAddress:
    def test_valid_ipv4(self):
        assert validate_ip_address("192.168.1.1") == "192.168.1.1"
        assert validate_ip_address("10.0.0.1") == "10.0.0.1"

    def test_valid_ipv6(self):
        assert validate_ip_address("::1") == "::1"
        assert validate_ip_address("fe80::1") == "fe80::1"

    def test_invalid(self):
        with pytest.raises(ValidationError):
            validate_ip_address("not-an-ip")

    def test_out_of_range(self):
        with pytest.raises(ValidationError):
            validate_ip_address("999.999.999.999")


# ---------------------------------------------------------------------------
# MAC validation
# ---------------------------------------------------------------------------

class TestNormalizeMacAddress:
    def test_colon_format(self):
        assert normalize_mac_address("AA:BB:CC:DD:EE:FF") == "AA-BB-CC-DD-EE-FF"

    def test_dash_format(self):
        assert normalize_mac_address("aa-bb-cc-dd-ee-ff") == "AA-BB-CC-DD-EE-FF"

    def test_invalid_length(self):
        with pytest.raises(ValidationError):
            normalize_mac_address("AA:BB:CC")

    def test_invalid_chars(self):
        with pytest.raises(ValidationError):
            normalize_mac_address("GG:HH:II:JJ:KK:LL")


# ---------------------------------------------------------------------------
# Sanitizers
# ---------------------------------------------------------------------------

class TestSanitizeStrict:
    def test_strips_html(self):
        assert sanitize_strict("<b>bold</b>") == "bold"

    def test_strips_script_tags(self):
        assert sanitize_strict('<script>alert("xss")</script>hello') == "hello"

    def test_strips_event_handlers(self):
        result = sanitize_strict('onerror= bad')
        assert "onerror" not in result

    def test_empty_passthrough(self):
        assert sanitize_strict("") == ""

    def test_none_passthrough(self):
        assert sanitize_strict(None) is None


class TestSanitizePermissive:
    def test_preserves_shell_syntax(self):
        result = sanitize_permissive("cat file | grep foo")
        assert "grep" in result

    def test_escapes_angle_brackets(self):
        result = sanitize_permissive("echo <test>")
        assert "&lt;" in result
        assert "&gt;" in result

    def test_strips_script_tags(self):
        result = sanitize_permissive('<script>bad</script>cmd')
        assert "script" not in result.lower()


class TestSanitizeUsernameField:
    def test_strips_special(self):
        assert sanitize_username_field("user@name!") == "username"

    def test_allows_underscore_dash(self):
        assert sanitize_username_field("user_name-1") == "user_name-1"


class TestSanitizeField:
    def test_permissive_for_command(self):
        result = sanitize_field("command", "echo <test>")
        assert "&lt;" in result

    def test_strict_for_hostname(self):
        result = sanitize_field("hostname", "<b>host</b>")
        assert result == "host"


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

class TestPasswordHashing:
    def test_hash_and_verify(self):
        pw = "TestPassword123!"
        hashed = hash_password(pw)
        assert verify_password(pw, hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("CorrectPassword1!")
        assert not verify_password("WrongPassword1!", hashed)

    def test_hash_is_different_each_time(self):
        pw = "SamePassword1!"
        h1 = hash_password(pw)
        h2 = hash_password(pw)
        assert h1 != h2  # random salt

    def test_invalid_hash_returns_false(self):
        assert not verify_password("anything", "not-a-valid-hash")


# ---------------------------------------------------------------------------
# Password input validation (login - less strict)
# ---------------------------------------------------------------------------

class TestValidatePasswordInput:
    def test_normal_password_passes(self):
        assert validate_password_input("NormalPassword1!") == "NormalPassword1!"

    def test_empty_fails(self):
        with pytest.raises(ValidationError):
            validate_password_input("")

    def test_sql_injection_blocked(self):
        with pytest.raises(ValidationError):
            validate_password_input("pass--word")
