# tests/test_crud_and_queryset.py
import pytest
from apexorm import models
from apexorm.models.queryset import Q

def register_user(orm):
    class User(models.Model):
        id = models.IntegerField(primary_key=True)
        name = models.CharField(max_length=100, nullable=False)
        description = models.CharField(max_length=255, nullable=True)
    orm.register_models([User])
    orm.migrate()
    return User

def seed_users(User):
    data = [
        ("Joe Doe", "joe desc"),
        ("John Smith", "smith desc"),
        ("Alice Mince", "alice desc"),
        ("Bob Tob", "tob desc"),
        ("Joey Tribiani", "friends"),
    ]
    for n, d in data:
        User(name=n, description=d).save()
    return data

def test_create_update_delete_and_get(orm):
    User = register_user(orm)
    u = User(name="Init", description="init")
    u.save()
    assert u.id is not None

    # update
    u.description = "updated"
    u.save()
    fetched = User.objects.get(id=u.id)
    assert fetched.description == "updated"

    # delete
    u.delete()
    with pytest.raises(ValueError):
        User.objects.get(id=u.id)

def test_queryset_filter_lookups(orm):
    User = register_user(orm)
    seed_users(User)

    # eq
    assert User.objects.filter(name__eq="Joe Doe").count() == 1
    # have / contains (case-insensitive)
    assert User.objects.filter(name__have="jo").count() >= 2
    # in / notin
    assert User.objects.filter(name__in=["Alice Mince", "No One"]).count() == 1
    assert User.objects.filter(name__notin=["Alice Mince"]).count() >= 4
    # startswith / endswith
    assert User.objects.filter(name__startswith="Jo").count() >= 2
    assert User.objects.filter(name__endswith="Tob").count() == 1

def test_q_objects_and_search(orm):
    User = register_user(orm)
    seed_users(User)

    qs = User.objects.filter(Q(name__have="joe") | Q(description__have="friends"))
    names = [u.name for u in qs.all()]
    assert "Joey Tribiani" in names or "Joe Doe" in names

    # exclude
    excluded = User.objects.exclude(name__eq="Joe Doe").all()
    assert all(u.name != "Joe Doe" for u in excluded)

    # search (OR across fields)
    srch = User.objects.search(name__have="jo", description__have="smith").values_list("name", flat=True)
    assert any("John Smith" == n for n in srch) or any("Joey Tribiani" == n for n in srch)

def test_order_limit_offset_values(orm):
    User = register_user(orm)
    seed_users(User)

    first_two = User.objects.order_by("name").limit(2).values_list("name", flat=True)
    assert len(first_two) == 2

    # values (dicts) and values_list (tuples)
    rows = User.objects.filter(name__have="o").values("id", "name")
    assert isinstance(rows, list) and isinstance(rows[0], dict) and "name" in rows[0]

    tuples = User.objects.filter(name__have="o").values_list("id", "name")
    assert isinstance(tuples[0], tuple) and len(tuples[0]) == 2

    # flat with 1 column
    flat = User.objects.values_list("name", flat=True)
    assert isinstance(flat, list) and isinstance(flat[0], str)

    # flat invalid usage
    with pytest.raises(ValueError):
        User.objects.values_list("id", "name", flat=True)
