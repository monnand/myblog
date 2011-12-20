from django.db import models
from django.contrib.auth.models import User
import markdown
from datetime import datetime
import uuid
import html

class Author(models.Model):
    name = models.CharField(max_length=256, unique=True)
    decrypt_key = models.CharField(max_length=1024)
    email = models.EmailField()
    about = models.TextField()
    can_add_user = models.BooleanField(default=False)

class Post(models.Model):
    title = models.CharField(max_length=256)
    author = models.ForeignKey(Author, related_name="posts")

    slug = models.CharField(max_length=256)
    created = models.DateTimeField(default=datetime.now)
    modified = models.DateTimeField(default=datetime.now)
    content_format = models.CharField(max_length=32, default="markdown")
    language = models.CharField(max_length=4, default="enUS")

    content = models.TextField()
    content_html = models.TextField()
    abstract = models.TextField()
    view_count = models.IntegerField(default=0, editable=False)

    uuid = models.CharField(max_length=32)

    class Meta:
        ordering = ['-created', '-modified']

    def save(self, *args, **kwargs):
        if len(self.uuid) == 0:
            self.uuid = uuid.uuid4().hex
        if len(self.slug) == 0:
            self.slug = self.uuid
        if len(self.title) == 0 or len(self.content_html) == 0:
            return
        self.abstract = html.parse(url).xpath('//p/text()')[0]
        super(Post, self).save(*args, **kwargs)
