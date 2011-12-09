from django.db import models
from django.contrib.auth.models import User
import markdown
from datetime import datetime
import uuid

class Author(models.Model):
    name = models.CharField(max_length=256, unique=True)
    decrypt_key = models.CharField(max_length=1024)
    email = models.EmailField()
    about = models.TextField()
    can_add_user = models.Boolean(default=False)

class Post(models.Model):
    title = models.CharField(max_length=256)
    author = models.ForeignKey(Author, related_name="posts")

    slug = models.CharField(max_lenght=256, unique=True)
    created = models.DateTimeField(default=datetime.now)
    modified = models.DateTimeField(default=datetime.now)
    content_format = models.CharField(max_length=32, default="markdown")

    content = models.TextField()
    content_html = models.TextField()
    view_count = models.IntegerField(default=0, editable=False)

    uuid = models.CharField(max_length=32)

    class Meta:
        ordering = ['-created', '-modified']

    def save(self, *args, **kwargs):
        if len(post.uuid) == 0:
            post.uuid = uuid.uuid4().hex
        if len(post.slug) == 0:
            post.slug = post.uuid
        if len(post.title) == 0 or len(post.content_html) == 0:
            return
        super(Post, self).save(*args, **kwargs)
