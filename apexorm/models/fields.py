# apexorm/models/fields.py
import os
import uuid
from sqlalchemy import Integer, String, Boolean, DateTime, Float, Text, JSON, Date, Time
from apexorm.models.validators import (
    validate_email, validate_url, validate_uuid, validate_ip_address, ValidationError
)
from apexorm.models.storage.local import LocalStorageBackend


_default_storage = LocalStorageBackend()


class Field:
    def __init__(self, primary_key: bool=False, nullable: bool=True, unique: bool=False, default=None, validators=None):
        self.primary_key = primary_key
        self.nullable = nullable
        self.unique = unique
        self.default = default
        self.validators = validators or []

    def validate(self, value):
        for validator in self.validators:
            validator(value)
    
    def get_column_type(self):
        raise NotImplementedError
    
    def get_default_value(self):
        """Return default, calling it if it's callable."""
        if callable(self.default):
            return self.default()
        return self.default


class IntegerField(Field):
    def get_column_type(self):
        return Integer


class CharField(Field):
    def __init__(self, max_length: int, primary_key: bool=False, nullable: bool=True, unique: bool=False, default=None, validators=None):
        self.max_length = max_length
        super().__init__(primary_key, nullable, unique, default, validators)

    def get_column_type(self):
        return String(self.max_length)
    

class BooleanField(Field):
    def get_column_type(self):
        return Boolean
    

class DateTimeField(Field):
    def get_column_type(self):
        return DateTime
    

class FloatField(Field):
    def get_column_type(self):
        return Float
    

class TextField(Field):
    def get_column_type(self):
        return Text
    

class ForeignKeyField(Field):
    """
    author = ForeignKeyField("User", related_name="posts", nullable=False)
    """
    def __init__(self, to: str, related_name: str|None=None, nullable: bool=True, unique: bool=False, on_delete: str|None=None):
        super().__init__(primary_key=False, nullable=nullable, unique=unique, default=None)
        self.to = to
        self.related_name = related_name
        self.on_delete = on_delete  # not yet enforced, placeholder


class OneToOneField(ForeignKeyField):
    """
    profile = OneToOneField("User", related_name="profile")
    """
    def __init__(self, to: str, related_name: str|None=None, nullable: bool=True, on_delete: str|None=None):
        super().__init__(to=to, related_name=related_name, nullable=nullable, unique=True, on_delete=on_delete)


class ManyToManyField:
    """
    members = ManyToManyField("User", related_name="groups")
    """
    def __init__(self, to: str, related_name: str|None=None):
        self.to = to
        self.related_name = related_name


class EmailField(CharField):
    def __init__(self, max_length=255, **kwargs):
        validators = kwargs.pop("validators", [])
        validators.append(validate_email)
        super().__init__(max_length=max_length, validators=validators, **kwargs)


class URLField(CharField):
    def __init__(self, max_length=200, **kwargs):
        validators = kwargs.pop("validators", [])
        validators.append(validate_url)
        super().__init__(max_length=max_length, validators=validators, **kwargs)


class UUIDField(Field):
    def __init__(self, default=uuid.uuid4, **kwargs):
        validators = kwargs.pop("validators", [])
        validators.append(validate_uuid)
        super().__init__(default=default, validators=validators, **kwargs)
    def get_column_type(self): return String(36)


class IPAddressField(CharField):
    def __init__(self, **kwargs):
        validators = kwargs.pop("validators", [])
        validators.append(validate_ip_address)
        super().__init__(max_length=45, validators=validators, **kwargs)


class JSONField(Field):
    def get_column_type(self): return JSON


class DateField(Field):
    def get_column_type(self): return Date


class TimeField(Field):
    def get_column_type(self): return Time


class DateTimeField(Field):
    def get_column_type(self): return DateTime


class FloatField(Field):
    def get_column_type(self): return Float


class ChoiceField(CharField):
    def __init__(self, choices: list[tuple], **kwargs):
        self.choices = choices
        super().__init__(max_length=max(len(c[0]) for c in choices), **kwargs)
    def validate(self, value):
        if value not in [c[0] for c in self.choices]:
            raise ValidationError(f"{value} is not a valid choice.")
        

class FileField(Field):
    """
    Represents a file path in the database.
    Automatically handles saving and deleting files in the backend.
    """

    def __init__(self, upload_to="uploads", storage=None, **kwargs):
        self.upload_to = upload_to
        self.storage = storage or _default_storage
        super().__init__(**kwargs)

    def get_column_type(self):
        return String(255)

    def save_file(self, instance, file_name: str, file_data: bytes):
        """Save a new file and delete old file if present."""
        old_path = getattr(instance, self.attr_name, None)
        if old_path:
            self.storage.delete(old_path)
        rel_path = self.storage.save(self.upload_to, file_name, file_data)
        setattr(instance, self.attr_name, rel_path)
        return rel_path

    def delete_file(self, instance):
        """Delete the file if it exists."""
        file_path = getattr(instance, self.attr_name, None)
        if file_path:
            self.storage.delete(file_path)
            setattr(instance, self.attr_name, None)


class ImageField(FileField):
    """
    Validates image extensions and saves them using the same backend.
    """
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

    def save_file(self, instance, file_name: str, file_data: bytes):
        ext = os.path.splitext(file_name)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValidationError(f"Unsupported image format: {ext}")
        return super().save_file(instance, file_name, file_data)