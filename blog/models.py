from django.db import models
from django.contrib.auth.models import User
import markdown

class Post(models.Model):
    title = models.CharField(max_lenght=256)
    author = models.ForeignKey(User, related_name="posts")

    slug = models.SlugField()
    created = models.DateTimeField(default=datetime.now, editable=False) # when first revision was created
    updated = models.DateTimeField(null=True, blank=True, editable=False) # when last revision was create (even if not published)
    published = models.DateTimeField(null=True, blank=True, editable=False) # when last published

    content = models.TextField()
    content_html = models.TextField(editable=False)
    view_count = models.IntegerField(default=0, editable=False)

    def to_html(self):
        self.content_html = markdown.markdown(self.content)

