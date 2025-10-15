# apexorm/models/__init__.py
import re
from sqlalchemy.orm import declarative_base, DeclarativeMeta, relationship
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey
from .fields import *
from .manager import Manager
from .relations import (
    MODEL_REGISTRY, PENDING_BACKREFS, register_model,
    camel_to_snake, get_tablename_for_classname, finalize_backrefs, ensure_m2m_table
)
from .m2m import ManyToManyDescriptor

Base = declarative_base()


class ModelMeta(DeclarativeMeta):
    """Intercept model creation and replace Field() with Column()/relationship() objects."""
    def __new__(mcls, name, bases, attrs):
        if name == "Model":
            return super().__new__(mcls, name, bases, attrs)

        # Auto-generate __tablename__
        if "__tablename__" not in attrs or not attrs["__tablename__"]:
            attrs["__tablename__"] = re.sub(r'(?<!^)(?=[A-Z])', "_", name).lower()

        # Collect relation specs first
        fk_specs = []   # (field_name, ForeignKeyField, is_o2o)
        m2m_specs = []  # (field_name, ManyToManyField)

        # Replace simple Field with Column; stash FK / M2M to wire after class exists
        for key, value in list(attrs.items()):
            if isinstance(value, Field) and not isinstance(value, ForeignKeyField):
                attrs[key] = Column(
                    value.get_column_type(),
                    primary_key=value.primary_key,
                    nullable=value.nullable,
                    unique=value.unique,
                    default=value.default,
                )
            elif isinstance(value, ForeignKeyField):
                fk_specs.append((key, value, isinstance(value, OneToOneField)))
                del attrs[key]
            elif isinstance(value, ManyToManyField):
                m2m_specs.append((key, value))
                del attrs[key]

        for key, value in attrs.items():
            if isinstance(value, Field):
                value.attr_name = key

        # Create class first
        cls = super().__new__(mcls, name, bases, attrs)
        register_model(cls)

        declaring_module = cls.__module__

        # ---- FK / O2O ----
        for field_name, fk_field, is_o2o in fk_specs:
            # Build fully-qualified target path
            if isinstance(fk_field.to, str):
                target_fq = fk_field.to if "." in fk_field.to else f"{declaring_module}.{fk_field.to}"
                target_simple = target_fq.rsplit(".", 1)[-1]
            else:
                target_fq = f"{fk_field.to.__module__}.{fk_field.to.__name__}"
                target_simple = fk_field.to.__name__

            target_table = camel_to_snake(target_simple)

            # '<field>_id' column
            col_name = f"{field_name}_id"
            setattr(
                cls,
                col_name,
                Column(
                    Integer,
                    ForeignKey(f"{target_table}.id"),
                    nullable=fk_field.nullable,
                    unique=fk_field.unique,
                ),
            )

            # relationship on this side (pass FQCN string)
            rel_kwargs = {"uselist": False}
            if fk_field.related_name:
                rel_kwargs["back_populates"] = fk_field.related_name
            setattr(cls, field_name, relationship(target_fq, **rel_kwargs))

            # schedule reverse
            if fk_field.related_name:
                source_fq = f"{cls.__module__}.{cls.__name__}"
                PENDING_BACKREFS.append(
                    (target_fq, fk_field.related_name, source_fq, field_name,
                     not is_o2o, "o2o" if is_o2o else "fk")
                )

        # ---- M2M ----
        for field_name, mm_field in m2m_specs:
            if isinstance(mm_field.to, str):
                target_fq = mm_field.to if "." in mm_field.to else f"{declaring_module}.{mm_field.to}"
            else:
                target_fq = f"{mm_field.to.__module__}.{mm_field.to.__name__}"

            private_attr = f"_{field_name}_rel"
            if not hasattr(cls, "__m2m_private_map__"):
                cls.__m2m_private_map__ = {}
            cls.__m2m_private_map__[field_name] = private_attr

            source_fq = f"{cls.__module__}.{cls.__name__}"
            PENDING_BACKREFS.append(
                (target_fq, mm_field.related_name, source_fq, field_name, True, "m2m")
            )

            setattr(cls, field_name, ManyToManyDescriptor(private_attr))

        # ✅ Make sure we return the class object
        return cls



class Model(Base, metaclass=ModelMeta):
    __abstract__ = True
    __tablename__ = None
    _session = None
    objects:Manager = None
    __m2m_private_map__ = {}

    def __init__(self, **kwargs):
        super().__init__()

        # 1) Assign columns (with defaults) exactly as you do now
        column_names = {c.name for c in self.__table__.columns}
        for col in self.__table__.columns:
            field_obj = getattr(self.__class__, col.name, None)
            if isinstance(field_obj, Field):
                default_value = (
                    field_obj.default() if callable(field_obj.default) else field_obj.default
                )
                setattr(self, col.name, kwargs.get(col.name, default_value))
            else:
                setattr(self, col.name, kwargs.get(col.name))

        # 2) Assign relationship attributes from kwargs
        for key, value in kwargs.items():
            if key in column_names:
                continue  # already handled

            # If it's a relationship attribute on the class, set it.
            attr = getattr(self.__class__, key, None)
            prop = getattr(attr, "property", None)
            if prop is not None and hasattr(prop, "mapper"):
                setattr(self, key, value)
                continue

            # (optional) allow other known attributes, else raise to catch typos
            if hasattr(self.__class__, key):
                setattr(self, key, value)
            else:
                # You can choose to silently ignore, but raising helps catch mistakes
                raise TypeError(f"Unknown field/relationship '{key}' for {self.__class__.__name__}")

    @classmethod
    def __generate_table_name__(cls, name):
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        table_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        cls.__tablename__ = table_name
        return table_name

    def save(self, commit: bool = True):
        """
        Save the model instance to the database.
        Ensures FK/O2O relationships are synchronized before flush.
        Prevents noisy autoflush warnings by using no_autoflush while wiring.
        """
        if not getattr(self, "_session", None):
            raise RuntimeError("This model is not bound to a database session.")
        s = self._session

        from apexorm.models.validators import ValidationError
        from sqlalchemy.orm import object_session, class_mapper

        # Ensure the instance itself is in the session ASAP (prevents cascade warnings).
        if object_session(self) is not s:
            s.add(self)

        # ----- apply defaults & validators -----
        for col in self.__table__.columns:
            val = getattr(self, col.name)
            field_obj = getattr(self.__class__, col.name, None)

            if val is None and getattr(field_obj, "default", None) is not None:
                default = field_obj.default
                val = default() if callable(default) else default
                setattr(self, col.name, val)

            if hasattr(field_obj, "validators"):
                if val is None and getattr(field_obj, "nullable", True):
                    continue
                for v in field_obj.validators:
                    v(val)

        mapper = class_mapper(self.__class__)

        # ✅ Wire FK/O2O inside no_autoflush to avoid implicit flush during attribute access
        with s.no_autoflush:
            for rel in mapper.relationships:
                if rel.uselist:
                    continue  # skip collections (M2M / O2M)

                rel_name = rel.key
                related_obj = getattr(self, rel_name, None)

                # Friendly guard: if relation is required but missing, fail early
                if related_obj is None:
                    needs_value = any(
                        (not local_col.nullable) and getattr(self, local_col.key, None) is None
                        for local_col, _remote_col in rel.local_remote_pairs
                    )
                    if needs_value:
                        raise ValidationError(f"'{rel_name}' is required.")
                    continue

                # Make sure related object is attached
                if object_session(related_obj) is not s:
                    s.add(related_obj)

                # Ensure related has PK so we can copy FK(s)
                if getattr(related_obj, "id", None) is None:
                    s.flush()  # assign PK on related

                # Copy FK values from related onto this object
                for local_col, remote_col in rel.local_remote_pairs:
                    local_val = getattr(self, local_col.key, None)
                    remote_val = getattr(related_obj, remote_col.key, None)
                    if remote_val is not None and local_val != remote_val:
                        setattr(self, local_col.key, remote_val)

        # optional model-level validation
        if hasattr(self, "clean"):
            self.clean()

        try:
            s.flush()  # flush after all FK assignments are done
            if commit:
                s.commit()
            return self
        except ValidationError as e:
            s.rollback()
            raise e
        except Exception:
            s.rollback()
            raise
  
    def delete(self, commit: bool = True):
        if not getattr(self, "_session", None):
            raise RuntimeError("This model is not bound to a database session.")
        s = self._session
        try:
            s.delete(self)
            if commit:
                s.commit()
        except Exception:
            s.rollback()
            raise
