# test/test_queryset_index_slice.py
import pytest
from apexorm import models

def register_user(orm):
    class User(models.Model):
        id = models.IntegerField(primary_key=True)
        name = models.CharField(max_length=100, nullable=False)
    orm.register_models([User])
    orm.migrate()
    return User

def seed(User):
    for i in range(10):
        User(name=f"U{i}").save()

def test_qs_index_and_slice(orm):
    User = register_user(orm)
    seed(User)

    # __getitem__ single index
    assert User.objects.order_by("id")[0].name == "U0"
    assert User.objects.order_by("id")[3].name == "U3"

    # negative index (materializes then slices)
    assert User.objects.order_by("id")[-1].name == "U9"

    # simple slices return new QuerySet lazily
    first_five = User.objects.order_by("id")[:5]
    assert first_five.count() == 5
    assert first_five[0].name == "U0"
    assert first_five[-1].name == "U4"

    # step forces materialization
    stepped = User.objects.order_by("id")[::2]
    assert stepped[0].name == "U0" and stepped[1].name == "U2"
