# apexorm/models/storage/utils.py
import uuid
import os

def generate_uuid_filename(original_name: str) -> str:
    ext = os.path.splitext(original_name)[1]
    return f"{uuid.uuid4().hex}{ext}"
