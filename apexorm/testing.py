# apexorm/testing.py
def reset_model_state():
    from apexorm.models import Base
    from apexorm.models.relations import MODEL_REGISTRY, PENDING_BACKREFS, M2M_ASSOC_TABLES
    MODEL_REGISTRY.clear()
    PENDING_BACKREFS.clear()
    M2M_ASSOC_TABLES.clear()
    # Clear in-memory table metadata (no engine drop here)
    Base.metadata.clear()