# apexorm/models/m2m.py
from .queryset import QuerySet
from sqlalchemy.orm import with_parent


class ManyToManyManager:
    """
    Bound to a parent instance. Exposes Django-like API: add(), remove(), all(), filter().
    Now 'all()' and 'filter()' are database-backed using SQLAlchemy's with_parent()
    so membership and extra filtering are executed in SQL, not in memory.
    Also supports len(), iteration, membership tests, and indexing on the collection.
    """
    def __init__(self, instance, private_attr: str):
        self.instance = instance
        self.private_attr = private_attr  # e.g. "_members_rel"

    # ----- internals -----
    @property
    def _session(self):
        s = getattr(self.instance, "_session", None)
        if not s:
            raise RuntimeError("Model instance is not bound to a session.")
        return s

    def _collection(self):
        # SQLAlchemy InstrumentedList of related objects
        return getattr(self.instance, self.private_attr)

    def _relationship_attr(self):
        # Instrumented relationship attribute on the class
        return getattr(self.instance.__class__, self.private_attr)

    def _related_model_class(self):
        # Resolve via the relationship mapper on the class attribute
        return self._relationship_attr().property.mapper.class_

    # ----- mutations -----
    def add(self, *objs):
        col = self._collection()
        for obj in objs:
            col.append(obj)
        self._session.commit()

    def remove(self, *objs):
        col = self._collection()
        for obj in objs:
            col.remove(obj)
        self._session.commit()

    # ----- list-like behavior on the loaded collection -----
    def __len__(self):
        return len(self._collection())

    def __iter__(self):
        return iter(self._collection())

    def __contains__(self, item):
        return item in self._collection()

    def __getitem__(self, idx):
        """
        Support list-style indexing and slicing, e.g. user.groups[0]
        and user.groups[0:10]. This uses the (possibly prefetched) collection.
        """
        return self._collection()[idx]

    # ----- DB-backed querying -----
    
    def all(self):
        """
        Return a QuerySet of related instances, with membership enforced in SQL.
        """
        related_model = self._related_model_class()
        rel_attr = self._relationship_attr()  # instrumented attr on the class

        qs = QuerySet(related_model, self._session)
        qs.query = (
            self._session
            .query(related_model)
            .filter(with_parent(self.instance, rel_attr))  # modern API
        )
        return qs

    def filter(self, **kwargs):
        """
        Return a DB-backed QuerySet with additional filters applied.
        """
        return self.all().filter(**kwargs)
    
    # convenience: make manager quack like a QuerySet
    def values(self, *fields):
        return self.all().values(*fields)

    def values_list(self, *fields, flat=False):
        return self.all().values_list(*fields, flat=flat)

    def __getattr__(self, name):
        """
        Delegate unknown attributes to the underlying QuerySet so calls like
        .order_by(), .count(), .exists(), .search(), etc. work directly on the manager.
        """
        qs = self.all()
        try:
            return getattr(qs, name)
        except AttributeError:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
    

class ManyToManyDescriptor:
    def __init__(self, private_attr):
        self.private_attr = private_attr

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return ManyToManyManager(instance, self.private_attr)
