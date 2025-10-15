# test/test_select_related_errors_and_nested.py
import pytest
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

    orm.register_models([User, Profile, Post])
    orm.migrate()
    return User, Profile, Post

def seed(User, Profile, Post):
    u = User(name="U"); u.save()
    Profile(bio="bio", user=u).save()
    Post(title="T1", author=u).save()
    Post(title="T2", author=u).save()
    return u

def test_select_related_raises_on_collection(orm):
    User, Profile, Post = register_models(orm)
    seed(User, Profile, Post)
    with pytest.raises(ValueError):
        # 'posts' is a collection; select_related must reject it
        User.objects.select_related("posts").all()

def test_nested_select_related(orm):
    User, Profile, Post = register_models(orm)
    u = seed(User, Profile, Post)

    # Nested scalar path: author__profile
    posts = Post.objects.select_related("author__profile").all()
    assert posts and posts[0].author.profile.bio == "bio"

def test_scalar_prefetch(orm):
    User, Profile, Post = register_models(orm)
    u = seed(User, Profile, Post)

    # prefetch also allowed on scalar per implementation
    posts = Post.objects.prefetch_related("author").all()
    # author should be available without extra attributes failing
    assert posts[0].author.name == "U"
