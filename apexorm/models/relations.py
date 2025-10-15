# apexorm/models/relations.py
import re
from typing import Dict, List, Tuple
from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship


def fqcn_from_cls(cls) -> str:
    return f"{cls.__module__}.{cls.__name__}"


def camel_to_snake(name: str) -> str:
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

# Global registries
MODEL_REGISTRY: Dict[str, type] = {}
PENDING_BACKREFS: List[Tuple[str, str, str, str, bool, str]] = []
# (target_class_name, related_attr, source_class_name, source_attr, uselist, rel_type)
# rel_type ∈ {"fk", "o2o", "m2m"}

M2M_ASSOC_TABLES: Dict[str, Table] = {}  # key = "<left>_<attr>"

def register_model(cls):
    MODEL_REGISTRY[fqcn_from_cls(cls)] = cls

def get_tablename_for_classname(class_name: str) -> str:
    # Default mapping per your ModelMeta: snake_case(class_name)
    return camel_to_snake(class_name)

def ensure_m2m_table(metadata, left_cls, left_attr: str, right_cls):
    key = f"{left_cls.__name__}_{left_attr}"
    if key in M2M_ASSOC_TABLES:
        return M2M_ASSOC_TABLES[key]

    left_table = left_cls.__tablename__
    right_table = right_cls.__tablename__

    table_name = f"{left_table}_{left_attr}"
    assoc = Table(
        table_name,
        metadata,
        Column(f"{left_table}_id", Integer, ForeignKey(f"{left_table}.id"), primary_key=True),
        Column(f"{right_table}_id", Integer, ForeignKey(f"{right_table}.id"), primary_key=True),
    )
    M2M_ASSOC_TABLES[key] = assoc
    return assoc

def finalize_backrefs(Base):
    for target_name, related_attr, source_name, source_attr, uselist, rel_type in list(PENDING_BACKREFS):
        target_cls = MODEL_REGISTRY.get(target_name)
        source_cls = MODEL_REGISTRY.get(source_name)
        if not target_cls or not source_cls:
            continue

        if rel_type in ("fk", "o2o"):
            if related_attr and not hasattr(target_cls, related_attr):
                setattr(
                    target_cls,
                    related_attr,
                    relationship(
                        source_name,  # FQCN string is unambiguous
                        back_populates=source_attr,
                        uselist=True if rel_type == "fk" else False,
                    ),
                )
        elif rel_type == "m2m":
            # Create ONE association table for this M2M and use it on BOTH sides.
            assoc = ensure_m2m_table(Base.metadata, source_cls, source_attr, target_cls)

            # Forward private relationship on the declaring class (source)
            forward_attr = f"_{source_attr}_rel"
            if not hasattr(source_cls, forward_attr):
                setattr(
                    source_cls,
                    forward_attr,
                    relationship(
                        target_name,           # FQCN string
                        secondary=assoc,       # <-- same assoc reused
                        back_populates=f"_{related_attr}_rel" if related_attr else None,
                        lazy="selectin",
                    ),
                )

            if related_attr:
                # Back private relationship on the target class reuses the SAME assoc
                back_private = f"_{related_attr}_rel"
                if not hasattr(target_cls, back_private):
                    setattr(
                        target_cls,
                        back_private,
                        relationship(
                            source_name,         # FQCN string
                            secondary=assoc,     # <-- reuse assoc, do NOT create a new one
                            back_populates=forward_attr,
                            lazy="selectin",
                        ),
                    )

                # Map public -> private so prefetch/select_related can resolve paths
                if not hasattr(target_cls, "__m2m_private_map__"):
                    target_cls.__m2m_private_map__ = {}
                target_cls.__m2m_private_map__[related_attr] = back_private

                # Expose the public descriptor (User.groups)
                from .m2m import ManyToManyDescriptor
                if not hasattr(target_cls, related_attr):
                    setattr(target_cls, related_attr, ManyToManyDescriptor(back_private))

    PENDING_BACKREFS.clear()
