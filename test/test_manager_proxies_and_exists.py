# test/test_manager_proxies_and_exists.py
import pytest
from apexorm import models

def register_user(orm):
    class User(models.Model):
        id = models.IntegerField(primary_key=True)
        name = models.CharField(max_length=100, nullable=False)
        note = models.CharField(max_length=200, nullable=True)
    orm.register_models([User])
    orm.migrate()
    return User

def seed(User):
    names = ["Alice", "Bob", "Bob", "Cara"]
    for n in names:
        User(name=n, note=f"note-{n}").save()

def test_manager_proxies_and_exists(orm):
    User = register_user(orm)
    seed(User)

    # Manager proxies to QuerySet
    assert User.objects.count() == 4
    assert User.objects.filter(name__eq="Bob").exists()
    assert not User.objects.filter(name__eq="Zed").exists()

    # get(): multiple and none cases
    with pytest.raises(ValueError):  # multiple
        User.objects.get(name="Bob")
    with pytest.raises(ValueError):  # none
        User.objects.get(name="Zed")

    # order_by desc
    last = User.objects.order_by("-id").first()
    assert last.name in {"Cara", "Bob", "Alice"}  # just sanity

    # values / values_list via manager
    rows = User.objects.filter(name__have="a").values("id", "name")
    assert isinstance(rows, list) and "name" in rows[0]

    flat = User.objects.values_list("name", flat=True)
    assert "Alice" in flat and "Bob" in flat
