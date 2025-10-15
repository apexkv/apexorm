# tests/test_relations.py
from apexorm import models

def register_models(orm):
    class User(models.Model):
        id = models.IntegerField(primary_key=True)
        name = models.CharField(max_length=100, nullable=False)

    class Profile(models.Model):
        id = models.IntegerField(primary_key=True)
        bio = models.CharField(max_length=255, nullable=True)
        user = models.OneToOneField("User", related_name="profile", nullable=False)

    class Post(models.Model):
        id = models.IntegerField(primary_key=True)
        title = models.CharField(max_length=200, nullable=False)
        author = models.ForeignKeyField("User", related_name="posts", nullable=False)

    class Group(models.Model):
        id = models.IntegerField(primary_key=True)
        name = models.CharField(max_length=100, nullable=False)
        members = models.ManyToManyField("User", related_name="groups")

    orm.register_models([User, Profile, Post, Group])
    orm.migrate()
    return User, Profile, Post, Group

def test_fk_o2o_m2m_and_reverse(orm):
    User, Profile, Post, Group = register_models(orm)

    u1 = User(name="A").save()
    u2 = User(name="B").save()

    p1 = Profile(bio="bio A", user=u1); p1.save()
    assert u1.profile.bio == "bio A"

    Post(title="t1", author=u1).save()
    Post(title="t2", author=u1).save()
    Post(title="t3", author=u2).save()

    assert len(u1.posts) == 2
    assert len(u2.posts) == 1

    g = Group(name="Admins"); g.save()
    g.members.add(u1, u2)
    assert any(m.name == "A" for m in g.members.all())
    assert any(gr.name == "Admins" for gr in u1.groups.all())

    # remove one
    g.members.remove(u2)
    assert all(m.name != "B" for m in g.members.all())

    # simple in-memory filter on m2m manager
    filtered = g.members.filter(name__have="A")
    assert len(filtered) == 1 and filtered[0].name == "A"
