# apexorm/models/storage/base.py
from abc import ABC, abstractmethod

class BaseStorageBackend(ABC):
    """Abstract base class for file storage backends."""

    @abstractmethod
    def save(self, folder: str, file_name: str, file_data: bytes) -> str:
        """Save file and return its relative path."""
        pass

    @abstractmethod
    def delete(self, path: str):
        """Delete a file by its relative path."""
        pass

    @abstractmethod
    def url(self, path: str) -> str:
        """Return a URL or absolute path to access the file."""
        pass
