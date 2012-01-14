from django.db import models
from django.contrib.auth.models import User
import markdown
from datetime import datetime
import uuid
#from lxml import html

from captcha.CaptchasDotNet import CaptchasDotNet

class BlogConfig(models.Model):
    title = models.TextField()
    subtitle = models.TextField()
    nr_posts_per_page = models.IntegerField(default=10)
    nr_poptags = models.IntegerField(default=10)
    link = models.TextField()

    captcha_name = models.CharField(default='', max_length = 128)
    captcha_secret = models.CharField(default='', max_length = 128)

    _blog_config = None
    _captcha = None

    @staticmethod
    def get():
        if BlogConfig._blog_config is None:
            bc = BlogConfig.objects.all()
            if len(bc) == 0:
                BlogConfig._blog_config = BlogConfig(title="My Blog",
                        subtitle='This is my blog',
                        nr_posts_per_page = 10,
                        link = "http://127.0.0.1:8000/")
                BlogConfig._blog_config.save()
            else:
                BlogConfig._blog_config = bc[0]
        return BlogConfig._blog_config

    @staticmethod
    def get_captcha():
        if BlogConfig._captcha is None:
            bc = BlogConfig.get()
            if len(bc.captcha_name) == 0 or len(bc.captcha_secret) == 0:
                return None
            BlogConfig._captcha = CaptchasDotNet(client=bc.captcha_name,
                    secret=bc.captcha_secret)
        return BlogConfig._captcha

class Author(models.Model):
    name = models.CharField(max_length=256, unique=True)
    decrypt_key = models.CharField(max_length=1024)
    email = models.EmailField()
    about = models.TextField()
    can_add_user = models.BooleanField(default=False)
    can_set_config = models.BooleanField(default=False)

class Tag(models.Model):
    tag = models.TextField(unique=True)
    nr_refs = models.IntegerField(default=0)

    class Meta:
        ordering = ['-nr_refs']

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

    tags = models.ManyToManyField(Tag)
    allow_comment = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created', '-modified']

    def save(self, *args, **kwargs):
        if len(self.uuid) == 0:
            self.uuid = uuid.uuid4().hex
        if len(self.slug) == 0:
            self.slug = self.uuid
        if len(self.title) == 0 or len(self.content_html) == 0:
            return
        ch = self.content_html
        self.abstract = ch[ch.find("<p>"):ch.find("</p>")]
        super(Post, self).save(*args, **kwargs)

class Reader(models.Model):
    name = models.CharField(max_length=64)
    email = models.EmailField()
    url = models.URLField()

class Comment(models.Model):
    reader = models.ForeignKey(Reader)
    post = models.ForeignKey(Post)
    content = models.TextField()
    created = models.DateTimeField(default=datetime.now)
    class Meta:
        ordering = ['-created']

#class PostImage(models.Model):
#    post = models.ForeignKey(Post)
#    image = models.ImageField(max_length = 256)


