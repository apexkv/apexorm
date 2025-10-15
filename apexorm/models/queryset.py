# apexorm/models/queryset.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, not_
from sqlalchemy.orm import joinedload, selectinload


class _ListWithAll(list):
    """List that also supports .all() for chaining symmetry with QuerySet."""
    def all(self):
        return self


class _ResultList(list):
    """
    List of model instances returned by QuerySet.all().
    Adds conveniences to project into dicts/tuples like Django's values().
    """
    def __init__(self, iterable, model_class):
        super().__init__(iterable)
        self._model_class = model_class

    def values(self, *fields):
        if not fields:
            fields = [col.name for col in self._model_class.__table__.columns]
        rows = []
        for obj in self:
            row = {}
            for f in fields:
                row[f] = getattr(obj, f)
            rows.append(row)
        return _ListWithAll(rows)

    def values_list(self, *fields, flat=False):
        if not fields:
            fields = [col.name for col in self._model_class.__table__.columns]
        if flat and len(fields) != 1:
            raise ValueError("`flat=True` is only valid when a single field is selected.")
        out = []
        for obj in self:
            if flat:
                out.append(getattr(obj, fields[0]))
            else:
                out.append(tuple(getattr(obj, f) for f in fields))
        return _ListWithAll(out)


def _split_path(path: str):
    # support django-style "a__b__c" or "a.b.c"
    return path.replace(".", "__").split("__")

def _resolve_attr_chain(model_cls, path: str):
    """
    Returns: (attrs_list, kinds_list)
    attrs_list: [InstrumentedAttribute, ...]
    kinds_list: ["scalar"|"collection", ...] for each hop
    """
    parts = _split_path(path)
    attrs = []
    kinds = []
    current_cls = model_cls

    for seg in parts:
        # map m2m descriptor public name -> private relationship attr if needed
        m2m_map = getattr(current_cls, "__m2m_private_map__", {}) or {}
        attr_name = m2m_map.get(seg, seg)

        inst_attr = getattr(current_cls, attr_name, None)
        if inst_attr is None:
            raise AttributeError(f"{current_cls.__name__} has no attribute '{seg}' (resolved '{attr_name}')")

        # must be relationship
        prop = getattr(inst_attr, "property", None)
        if prop is None or not hasattr(prop, "mapper"):
            raise ValueError(f"'{path}': segment '{seg}' is not a relationship on {current_cls.__name__}")

        attrs.append(inst_attr)
        kinds.append("collection" if prop.uselist else "scalar")
        current_cls = prop.mapper.class_

    return attrs, kinds


class Q:
    """Django-like Q object for complex filtering."""
    def __init__(self, **kwargs):
        self.children = []
        self.negated = False
        self.connector = and_

        if kwargs:
            self.children.append(kwargs)

    def __or__(self, other):
        q = Q()
        q.connector = or_
        q.children = [self, other]
        return q

    def __and__(self, other):
        q = Q()
        q.connector = and_
        q.children = [self, other]
        return q

    def __invert__(self):
        q = Q()
        q.negated = not self.negated
        q.children = [self]
        return q

    def build(self, model_class):
        """Recursively convert Q() tree into SQLAlchemy expressions."""
        conditions = []
        for child in self.children:
            if isinstance(child, Q):
                condition = child.build(model_class)
                conditions.append(~condition if child.negated else condition)
            elif isinstance(child, dict):
                for key, value in child.items():
                    parts = key.split("__")
                    field_name = parts[0]
                    lookup = parts[1] if len(parts) > 1 else "eq"
                    col = getattr(model_class, field_name)

                    if lookup == "eq":
                        conditions.append(col == value)
                    elif lookup == "lt":
                        conditions.append(col < value)
                    elif lookup == "lte":
                        conditions.append(col <= value)
                    elif lookup == "gt":
                        conditions.append(col > value)
                    elif lookup == "gte":
                        conditions.append(col >= value)
                    elif lookup == "in":
                        conditions.append(col.in_(value))
                    elif lookup == "notin":
                        conditions.append(~col.in_(value))
                    elif lookup in ("have", "contains"):
                        conditions.append(col.ilike(f"%{value}%"))
                    elif lookup in ("startswith", "istartswith"):
                        conditions.append(col.ilike(f"{value}%"))
                    elif lookup in ("endswith", "iendswith"):
                        conditions.append(col.ilike(f"%{value}"))
                    else:
                        raise ValueError(f"Unsupported lookup: {lookup}")
            else:
                raise ValueError(f"Invalid Q child type: {type(child)}")

        if len(conditions) == 1:
            expr = conditions[0]
        elif self.connector == or_:
            expr = or_(*conditions)
        else:
            expr = and_(*conditions)

        return ~expr if self.negated else expr

    def __repr__(self):
        return f"<Q negated={self.negated} children={self.children}>"


class QuerySet:
    def __init__(self, model_class, session: Session):
        self.model_class = model_class
        self.session = session
        self.query = session.query(model_class)

    # ------------------- FILTERING -------------------
    def filter(self, *args, **kwargs):
        """
        Supports:
        - Keyword filters (e.g. name__in=['A'])
        - Q objects (for complex conditions)
        """
        conditions = []

        # Handle Q() objects first
        for q in args:
            if isinstance(q, Q):
                conditions.append(q.build(self.model_class))
            else:
                raise TypeError(f"Invalid argument {q}, expected Q object")

        # Handle regular kwargs
        if kwargs:
            for key, value in kwargs.items():
                parts = key.split("__")
                field_name = parts[0]
                lookup = parts[1] if len(parts) > 1 else "eq"
                col = getattr(self.model_class, field_name)

                if lookup == "eq":
                    conditions.append(col == value)
                elif lookup == "lt":
                    conditions.append(col < value)
                elif lookup == "lte":
                    conditions.append(col <= value)
                elif lookup == "gt":
                    conditions.append(col > value)
                elif lookup == "gte":
                    conditions.append(col >= value)
                elif lookup == "in":
                    conditions.append(col.in_(value))
                elif lookup == "notin":
                    conditions.append(~col.in_(value))
                elif lookup in ("have", "contains"):
                    conditions.append(col.ilike(f"%{value}%"))
                elif lookup in ("startswith", "istartswith"):
                    conditions.append(col.ilike(f"{value}%"))
                elif lookup in ("endswith", "iendswith"):
                    conditions.append(col.ilike(f"%{value}"))
                else:
                    raise ValueError(f"Unsupported lookup: {lookup}")

        new_qs = QuerySet(self.model_class, self.session)
        if conditions:
            new_qs.query = self.query.filter(and_(*conditions))
        else:
            new_qs.query = self.query
        return new_qs

    # ------------------- SEARCH -------------------
    def search(self, **kwargs):
        """
        Perform OR-based string search across multiple fields.
        Example:
            User.objects.search(name__have='joe', description__have='dev')
        """
        or_conditions = []

        for key, value in kwargs.items():
            parts = key.split("__")
            field_name = parts[0]
            lookup = parts[1] if len(parts) > 1 else "have"
            col = getattr(self.model_class, field_name)

            if lookup in ("have", "contains"):
                or_conditions.append(col.ilike(f"%{value}%"))
            elif lookup in ("startswith", "istartswith"):
                or_conditions.append(col.ilike(f"{value}%"))
            elif lookup in ("endswith", "iendswith"):
                or_conditions.append(col.ilike(f"%{value}"))
            else:
                raise ValueError(f"Unsupported search lookup: {lookup}")

        new_qs = QuerySet(self.model_class, self.session)
        new_qs.query = self.query.filter(or_(*or_conditions))
        return new_qs

    # --- ordering ---
    def order_by(self, *fields):
        columns = []
        for field in fields:
            if field.startswith('-'):
                columns.append(getattr(self.model_class, field[1:]).desc())
            else:
                columns.append(getattr(self.model_class, field).asc())
        new_qs = QuerySet(self.model_class, self.session)
        new_qs.query = self.query.order_by(*columns)
        return new_qs

    # --- slicing ---
    def limit(self, n):
        new_qs = QuerySet(self.model_class, self.session)
        new_qs.query = self.query.limit(n)
        return new_qs

    def offset(self, n):
        new_qs = QuerySet(self.model_class, self.session)
        new_qs.query = self.query.offset(n)
        return new_qs

    # --- retrieval ---
    def all(self):
        # return a list-like object that also supports .values(), .values_list()
        return _ResultList(self.query.all(), self.model_class)

    def first(self):
        return self.query.first()

    def last(self):
        return self.query.order_by(self.model_class.id.desc()).first()

    def count(self):
        return self.query.count()

    def exists(self):
        return self.query.first() is not None

    def get(self, **kwargs):
        results = self.query.filter_by(**kwargs).all()
        if len(results) == 0:
            raise ValueError(f"{self.model_class.__name__} matching {kwargs} does not exist.")
        elif len(results) > 1:
            raise ValueError(f"Multiple {self.model_class.__name__} objects returned for {kwargs}.")
        return results[0]
    
    def exclude(self, **kwargs):
        conditions = []
        for key, value in kwargs.items():
            parts = key.split("__")
            field_name = parts[0]
            lookup = parts[1] if len(parts) > 1 else "eq"
            col = getattr(self.model_class, field_name)

            if lookup == "eq":
                conditions.append(col == value)
            elif lookup == "lt":
                conditions.append(col < value)
            # (reuse same logic)
        new_qs = QuerySet(self.model_class, self.session)
        new_qs.query = self.query.filter(~and_(*conditions))
        return new_qs
    
    # --- VALUES / VALUES_LIST ---
    def values(self, *fields):
        """
        Return a list-like (with .all()) of dictionaries for the selected fields.
        """
        results = self.query.all()
        if not fields:
            fields = [col.name for col in self.model_class.__table__.columns]

        values_list = []
        for obj in results:
            row = {}
            for field in fields:
                row[field] = getattr(obj, field)
            values_list.append(row)
        return _ListWithAll(values_list)

    def values_list(self, *fields, flat=False):
        """
        Return a list-like (with .all()) of tuples (or list if flat=True).
        """
        results = self.query.all()
        if not fields:
            fields = [col.name for col in self.model_class.__table__.columns]
        if flat and len(fields) != 1:
            raise ValueError("`flat=True` is only valid when a single field is selected.")

        out = []
        for obj in results:
            if flat:
                out.append(getattr(obj, fields[0]))
            else:
                out.append(tuple(getattr(obj, f) for f in fields))
        return _ListWithAll(out)
    
    def select_related(self, *paths):
        """
        Eager JOIN load for single-valued relations (FK / OneToOne).
        Nested paths allowed: "author__profile".
        """
        loaders = []
        for path in paths:
            attrs, kinds = _resolve_attr_chain(self.model_class, path)
            # ensure all hops are scalar (like Django)
            if any(k == "collection" for k in kinds):
                raise ValueError(f"select_related('{path}') includes a collection; use prefetch_related instead")

            # build chained joinedload
            loader = joinedload(attrs[0])
            for attr in attrs[1:]:
                loader = loader.joinedload(attr)
            loaders.append(loader)

        new_qs = QuerySet(self.model_class, self.session)
        new_qs.query = self.query.options(*loaders)
        return new_qs

    def prefetch_related(self, *paths):
        """
        Eager SELECT IN load for collections (O2M, M2M), also works for FK/O2O.
        Nested paths allowed: "author__groups".
        """
        loaders = []
        for path in paths:
            attrs, _kinds = _resolve_attr_chain(self.model_class, path)

            # build chained selectinload
            loader = selectinload(attrs[0])
            for attr in attrs[1:]:
                loader = loader.selectinload(attr)
            loaders.append(loader)

        new_qs = QuerySet(self.model_class, self.session)
        new_qs.query = self.query.options(*loaders)
        return new_qs

    # --- iteration magic ---
    def __iter__(self):
        return iter(self.all())

    def __len__(self):
        return self.count()

    def __repr__(self):
        return f"<QuerySet model={self.model_class.__name__}>"

    def __getitem__(self, key):
        """
        Support qs[0] and qs[5:10]-style access.
        - Single index returns a model instance (executes the query).
        - Slice returns a new QuerySet if step is 1/None; else materializes and slices.
        """
        if isinstance(key, slice):
            start = 0 if key.start is None else key.start
            stop = key.stop
            step = key.step

            # If user asks for a step (e.g., [::2]), materialize the list and slice.
            if step not in (None, 1):
                return self.all()[key]

            # Return a sliced QuerySet without executing yet.
            if stop is None:
                return self.offset(start)
            return self.offset(start).limit(max(0, stop - start))

        if isinstance(key, int):
            # Handle negative indices by materializing (simple & predictable)
            if key < 0:
                data = self.all()
                try:
                    return data[key]
                except IndexError:
                    raise IndexError("QuerySet index out of range") from None

            obj = self.offset(key).limit(1).first()
            if obj is None:
                raise IndexError("QuerySet index out of range")
            return obj

        raise TypeError(f"QuerySet indices must be integers or slices, not {type(key).__name__}")
