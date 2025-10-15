# tests/conftest.py
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # repo root (one level above tests/)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import os
import pytest
from apexorm import ApexORM
from apexorm.connection import SQLiteDB
from apexorm.testing import reset_model_state
from apexorm.models import Base
from apexorm.models.relations import MODEL_REGISTRY, PENDING_BACKREFS, M2M_ASSOC_TABLES


@pytest.fixture(autouse=True)
def clean_model_registry():
    # run BEFORE each test
    Base.registry.dispose()
    MODEL_REGISTRY.clear()
    PENDING_BACKREFS.clear()
    M2M_ASSOC_TABLES.clear()
    yield
    # run AFTER each test (belt & suspenders)
    Base.registry.dispose()
    MODEL_REGISTRY.clear()
    PENDING_BACKREFS.clear()
    M2M_ASSOC_TABLES.clear()

@pytest.fixture(autouse=True)
def _reset_state():
    # run before every test
    reset_model_state()
    yield
    reset_model_state()

@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")

@pytest.fixture
def orm(db_path):
    # new ORM per test, real SQLite file to avoid :memory: connection scoping issues
    return ApexORM(db=SQLiteDB(db_path))