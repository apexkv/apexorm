# apexorm/core/validators.py
import re
from urllib.parse import urlparse
import uuid
import ipaddress
from datetime import date, datetime, time

class ValidationError(Exception):
    pass


def validate_email(value: str):
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
        raise ValidationError("Enter a valid email address.")


def validate_url(value: str):
    parts = urlparse(value)
    if not all([parts.scheme, parts.netloc]):
        raise ValidationError("Enter a valid URL.")


def validate_uuid(value):
    try:
        uuid.UUID(str(value))
    except Exception:
        raise ValidationError("Enter a valid UUID.")


def validate_ip_address(value):
    try:
        ipaddress.ip_address(value)
    except ValueError:
        raise ValidationError("Enter a valid IPv4 or IPv6 address.")
