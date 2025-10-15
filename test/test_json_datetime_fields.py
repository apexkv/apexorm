# test/test_json_datetime_fields.py
from datetime import datetime, date, time
from apexorm import models

def register_model(orm):
    class Item(models.Model):
        id = models.IntegerField(primary_key=True)
        title = models.CharField(max_length=100, nullable=False)
        meta = models.JSONField(nullable=True)
        d = models.DateField(nullable=False)
        t = models.TimeField(nullable=False)
        dt = models.DateTimeField(nullable=False)
        score = models.FloatField(nullable=True)
    orm.register_models([Item])
    orm.migrate()
    return Item

def test_json_and_datetime_roundtrip(orm):
    Item = register_model(orm)
    now = datetime(2024, 1, 2, 3, 4, 5)
    it = Item(
        title="X",
        meta={"a": 1, "b": [2, 3]},
        d=date(2024, 1, 1),
        t=time(12, 34, 56),
        dt=now,
        score=9.5,
    ).save()

    fetched = Item.objects.get(id=it.id)
    assert fetched.title == "X"
    assert fetched.meta["a"] == 1 and fetched.meta["b"] == [2, 3]
    assert fetched.d == date(2024, 1, 1)
    assert fetched.t == time(12, 34, 56)
    # Datetime equality (naive) should round-trip in SQLite tests
    assert fetched.dt == now
    assert fetched.score == 9.5
