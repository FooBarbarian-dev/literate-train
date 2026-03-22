import re
from rest_framework.exceptions import ValidationError


USERNAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]{2,49}$")

IP_V4_PATTERN = re.compile(
    r"^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$"
)
IP_V6_PATTERN = re.compile(r"^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$")

MAC_PATTERN = re.compile(
    r"^([0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}$"
)

SQL_INJECTION_PATTERNS = [
    r"--", r";", r"/\*", r"\*/",
    r"\bUNION\b", r"\bSELECT\b", r"\bDROP\b", r"\bINSERT\b",
    r"\bDELETE\b", r"\bUPDATE\b", r"\bEXEC\b", r"\bEXECUTE\b",
]

XSS_PATTERNS = [
    r"<script", r"javascript:", r"onerror\s*=", r"onload\s*=",
    r"onclick\s*=", r"onmouseover\s*=", r"onfocus\s*=", r"onblur\s*=",
    r"data:", r"vbscript:",
]


def validate_username(username: str) -> str:
    if not username or not USERNAME_PATTERN.match(username):
        raise ValidationError(
            "Username must start with a letter and be 3-50 characters (letters, digits, _ -)."
        )
    return username


def validate_password(password: str) -> str:
    if len(password) < 12:
        raise ValidationError("Password must be at least 12 characters.")
    if len(password) > 128:
        raise ValidationError("Password must be at most 128 characters.")
    if not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValidationError("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        raise ValidationError("Password must contain at least one digit.")
    if not re.search(r"[^a-zA-Z0-9]", password):
        raise ValidationError("Password must contain at least one special character.")
    if re.match(r"^[a-zA-Z]+\d+$", password):
        raise ValidationError("Password cannot be only letters followed by numbers.")
    if re.search(r"(.)\1{2,}", password):
        raise ValidationError("Password cannot contain 3+ consecutive identical characters.")
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, password, re.IGNORECASE):
            raise ValidationError("Password contains disallowed patterns.")
    for pattern in XSS_PATTERNS:
        if re.search(pattern, password, re.IGNORECASE):
            raise ValidationError("Password contains disallowed patterns.")
    return password


def validate_ip_address(value: str) -> str:
    if not IP_V4_PATTERN.match(value) and not IP_V6_PATTERN.match(value):
        raise ValidationError(f"Invalid IP address: {value}")
    return value


def normalize_mac_address(value: str) -> str:
    cleaned = re.sub(r"[:\-.]", "", value.upper())
    if len(cleaned) != 12 or not re.match(r"^[0-9A-F]{12}$", cleaned):
        raise ValidationError(f"Invalid MAC address: {value}")
    return "-".join(cleaned[i:i+2] for i in range(0, 12, 2))


def validate_password_input(password: str) -> str:
    """Validate password on login (less strict - just check for injection)."""
    if not password or len(password) > 128:
        raise ValidationError("Invalid password.")
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, password, re.IGNORECASE):
            raise ValidationError("Invalid input.")
    for pattern in XSS_PATTERNS:
        if re.search(pattern, password, re.IGNORECASE):
            raise ValidationError("Invalid input.")
    return password
