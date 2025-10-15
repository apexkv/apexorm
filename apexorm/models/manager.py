# apexorm/models/manager.py
from sqlalchemy.orm import Session
from .queryset import QuerySet

class Manager:
    def __init__(self, model_class):
        self.model_class = model_class

    def _get_session(self) -> Session:
        session = getattr(self.model_class, "_session", None)
        if not session:
            raise RuntimeError(f"Model {self.model_class.__name__} is not bound to a database session.")
        return session

    # Return QuerySet instance
    def all(self):
        return QuerySet(self.model_class, self._get_session())

    def filter(self, *args, **kwargs):
        return self.all().filter(*args, **kwargs)

    def order_by(self, *fields):
        return self.all().order_by(*fields)

    def get(self, **kwargs):
        return self.all().get(**kwargs)

    def count(self):
        return self.all().count()

    def first(self):
        return self.all().first()

    def last(self):
        return self.all().last()

    def exists(self, **kwargs):
        return self.all().filter(**kwargs).exists()

    def search(self, **kwargs):
        """Shortcut for QuerySet.search()"""
        return self.all().search(**kwargs)
    
    def exclude(self, *args, **kwargs):
        """Shortcut for QuerySet.exclude()"""
        return self.all().exclude(*args, **kwargs)
    
    def select_related(self, *paths):
        return self.all().select_related(*paths)

    def prefetch_related(self, *paths):
        return self.all().prefetch_related(*paths)
    
    def values(self, *fields):
        return self.all().values(*fields)

    def values_list(self, *fields, flat=False):
        return self.all().values_list(*fields, flat=flat)