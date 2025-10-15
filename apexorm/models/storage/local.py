# apexorm/models/storage/local.py
import os
from apexorm.models.storage.base import BaseStorageBackend
from apexorm.models.storage.utils import generate_uuid_filename

class LocalStorageBackend(BaseStorageBackend):
    """Default backend for saving files locally."""

    def __init__(self, base_dir: str = "media"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def save(self, folder: str, file_name: str, file_data: bytes) -> str:
        os.makedirs(os.path.join(self.base_dir, folder), exist_ok=True)
        unique_name = generate_uuid_filename(file_name)
        save_path = os.path.join(self.base_dir, folder, unique_name)
        with open(save_path, "wb") as f:
            f.write(file_data)
        return os.path.join(folder, unique_name).replace("\\", "/")

    def delete(self, path: str):
        if not path:
            return
        abs_path = os.path.join(self.base_dir, path)
        if os.path.exists(abs_path):
            os.remove(abs_path)

    def url(self, path: str) -> str:
        return os.path.abspath(os.path.join(self.base_dir, path))
