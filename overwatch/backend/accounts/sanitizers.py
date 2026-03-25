import re
import html


def sanitize_strict(value: str) -> str:
    """Strict sanitization - strips all HTML, scripts, event handlers."""
    if not value:
        return value
    value = re.sub(r"<script[\s\S]*?</script>", "", value, flags=re.IGNORECASE)
    value = re.sub(r"<style[\s\S]*?</style>", "", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"javascript:", "", value, flags=re.IGNORECASE)
    value = re.sub(r"data:", "", value, flags=re.IGNORECASE)
    value = re.sub(r"vbscript:", "", value, flags=re.IGNORECASE)
    value = re.sub(r"on\w+\s*=", "", value, flags=re.IGNORECASE)
    return value.strip()


def sanitize_permissive(value: str) -> str:
    """Permissive sanitization - preserves shell syntax but escapes HTML angle brackets."""
    if not value:
        return value
    value = re.sub(r"<script[\s\S]*?</script>", "", value, flags=re.IGNORECASE)
    value = re.sub(r"<style[\s\S]*?</style>", "", value, flags=re.IGNORECASE)
    value = re.sub(r"javascript:", "", value, flags=re.IGNORECASE)
    value = re.sub(r"vbscript:", "", value, flags=re.IGNORECASE)
    value = re.sub(r"on\w+\s*=", "", value, flags=re.IGNORECASE)
    value = value.replace("<", "&lt;").replace(">", "&gt;")
    return value.strip()


def sanitize_username_field(value: str) -> str:
    """Strip username to allowed characters only."""
    return re.sub(r"[^a-zA-Z0-9_\\/\-]", "", value)


PERMISSIVE_FIELDS = {"command", "notes", "filename", "secrets"}


def sanitize_field(field_name: str, value: str) -> str:
    if not isinstance(value, str):
        return value
    if field_name in PERMISSIVE_FIELDS:
        return sanitize_permissive(value)
    if field_name == "username":
        return sanitize_username_field(sanitize_strict(value))
    return sanitize_strict(value)
