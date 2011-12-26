from django.db import models
from django.contrib.auth.models import User
import markdown
from datetime import datetime
import uuid
from lxml import html

class BlogConfig(models.Model):
    title = models.TextField()
    subtitle = models.TextField()
    nr_posts_per_page = models.IntegerField(default=10)

    _blog_config = None

    @staticmethod
    def get():
        if BlogConfig._blog_config is None:
            bc = BlogConfig.objects.all()
            if len(bc) == 0:
                BlogConfig._blog_config = BlogConfig(title="My Blog",
                        subtitle='This is my blog',
                        nr_posts_per_page = 10)
                BlogConfig._blog_config.save()
            else:
                BlogConfig._blog_config = bc[0]
        return BlogConfig._blog_config

class Author(models.Model):
    name = models.CharField(max_length=256, unique=True)
    decrypt_key = models.CharField(max_length=1024)
    email = models.EmailField()
    about = models.TextField()
    can_add_user = models.BooleanField(default=False)
    can_set_config = models.BooleanField(default=False)

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
        doc = html.document_fromstring(self.content_html)
        self.abstract = doc.xpath('//p/text()')[0]
        super(Post, self).save(*args, **kwargs)
