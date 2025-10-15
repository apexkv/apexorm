# test/test_storage_and_utils.py
import os
from apexorm.models.storage.local import LocalStorageBackend
from apexorm.models.storage.utils import generate_uuid_filename

def test_local_storage_save_delete_and_url(tmp_path, monkeypatch):
    base_dir = tmp_path / "media"
    storage = LocalStorageBackend(base_dir=str(base_dir))

    rel = storage.save("docs", "file.txt", b"hello")
    # path shape
    assert rel.startswith("docs/") and rel.endswith(".txt")

    abs_path = storage.url(rel)
    assert os.path.isabs(abs_path) and os.path.exists(abs_path)

    # delete removes file
    storage.delete(rel)
    assert not os.path.exists(abs_path)

def test_generate_uuid_filename_extension_preserved():
    a = generate_uuid_filename("photo.jpeg")
    b = generate_uuid_filename("photo.jpeg")
    assert a.endswith(".jpeg") and b.endswith(".jpeg") and a != b
