# tests/test_eager_loading.py
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

def seed(User, Profile, Post, Group):
    u = User(name="U"); u.save()
    Profile(bio="bio", user=u).save()
    p = Post(title="T", author=u); p.save()
    g = Group(name="G"); g.save()
    g.members.add(u)
    return u, p, g

def test_select_related_and_prefetch(orm):
    User, Profile, Post, Group = register_models(orm)
    u, p, g = seed(User, Profile, Post, Group)

    # select_related on FK / O2O
    posts = Post.objects.select_related("author").all()
    assert posts and posts[0].author.name == "U"

    users = User.objects.select_related("profile").all()
    assert users[0].profile.bio == "bio"

    # prefetch on collections (and nested)
    users2 = User.objects.prefetch_related("posts", "groups").all()
    assert users2 and len(users2[0].posts) == 1 and len(users2[0].groups) == 1

    # nested prefetch
    posts2 = Post.objects.prefetch_related("author__groups").all()
    assert posts2[0].author.groups and posts2[0].author.groups[0].name == "G"
