# test/test_m2m_manager_extras.py
from apexorm import models

def register_models(orm):
    class User(models.Model):
        id = models.IntegerField(primary_key=True)
        name = models.CharField(max_length=100, nullable=False)

    class Group(models.Model):
        id = models.IntegerField(primary_key=True)
        name = models.CharField(max_length=100, nullable=False)
        members = models.ManyToManyField("User", related_name="groups")

    orm.register_models([User, Group])
    orm.migrate()
    return User, Group

def test_m2m_manager_behaviors(orm):
    User, Group = register_models(orm)
    a = User(name="Alice").save()
    b = User(name="Bob").save()
    g = Group(name="G").save()

    # add, __len__, __contains__, iteration
    g.members.add(a, b)
    assert len(g.members) == 2
    assert a in g.members and b in g.members
    names = [m.name for m in g.members]
    assert set(names) == {"Alice", "Bob"}

    # values / values_list via manager (DB-backed)
    assert set(g.members.values_list("name", flat=True)) == {"Alice", "Bob"}
    only_a = g.members.filter(name__have="Ali").all()
    assert [u.name for u in only_a] == ["Alice"]

    # index and slice on collection (uses loaded collection)
    assert g.members[0].name in {"Alice", "Bob"}
    first = g.members[:1]
    assert len(first) == 1

    # remove
    g.members.remove(b)
    assert len(g.members) == 1 and a in g.members and b not in g.members
