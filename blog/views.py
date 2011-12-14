from django.http import HttpResponse, HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.utils.translation import activate
from django.utils.translation import get_language
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt
import datetime
import os
import os.path
import re
import json

from blog.models import Post, Author
from blog.decode import decode_post, dump_html

@csrf_exempt
def add_author(request):
    if request.method == 'POST':
        msg = request.POST['msg']
        authorname = request.POST['author']
        key = request.POST['key']
        author = Author.objects.filter(name=authorname)
        if len(author) == 0:
            nr_authors = Author.objects.count()
            # This is our first author. He should be able to add users
            if nr_authors == 0:
                msg = json.loads(msg)
                msg['can_add_user'] = True
            else:
                return HttpResponseForbidden("Failed\r\n")
        else:
            author = author[0]
            if author.can_add_user:
                msg = decode_post(msg, author.decrypt_key, key)
            else:
                return HttpResponseForbidden("Failed\r\n")
        new_author = Author(name=msg['name'], decrypt_key=msg['decrypt_key'], \
                email=msg['email'], about=msg['about'], can_add_user=msg['can_add_user'])
        new_author.save()
        return HttpResponse("Success\r\n")
    return HttpResponseForbidden("Not implemented\r\n")

def get_post(msg, create=False):
    slug = msg['slug']
    language = ""
    if msg.has_key('language'):
        language = msg['language']
    post = None
    if language:
        post = Post.objects.filter(slug=slug, language=language)
    else:
        post = Post.objects.filter(slug=slug)
    if len(post) > 0:
        return post
    if not create:
        return None
    title = msg['title']
    content = msg['content']
    content_format = msg['content_format']
    language = msg['language']

    content_html = dump_html(content, content_format)
    now = datetime.datetime.now()
    post = Post(title=title, \
            author=msg['author'],   \
            slug=slug,  \
            created=now,    \
            modified=now,   \
            content_format=content_format,  \
            content=content,    \
            content_html=content_html,  \
            view_count=0,   \
            language=language,  \
            uuid="")
    return [post]

def modify_post(msg, post):
    modified = False
    if post.title != msg['title']:
        post.title = msg['title']
        modified = True
    if post.content != msg['content']:
        post.content = msg['content']
        post.content_html = dump_html(content, content_format)
        modified = True
    if post.content_format != msg['content_format']:
        post.content_format = msg['content_format']
        post.content_html = dump_html(content, content_format)
        modified = True

    if modified:
        post.modified = datetime.datetime.now()
    return post

def is_unique_post_spec(msg):
    if msg.has_key('slug') and msg.has_key('language'):
        return True
    return False

def is_full_post_spec(msg):
    if not is_unique_post_spec(msg):
        return False
    if msg.has_key('author') \
            and msg.has_key('content') \
            and msg.has_key('content_format'):
        return True
    return False

@csrf_exempt
def post_blog(request):
    if request.method == 'POST':
        import pdb
        pdb.set_trace()
        if not request.POST.has_key('msg') or \
                not request.POST.has_key('author'):
            return HttpResponseForbidden("Failed\r\n")
        msg = request.POST['msg']
        authorname = request.POST['author']
        key = request.POST['key']
        author = Author.objects.filter(name=authorname)
        if len(author) == 0:
            return HttpResponseForbidden("Failed\r\n")
        author = author[0]
        msg = decode_post(msg, author.decrypt_key, key)
        if msg is None:
            return HttpResponseForbidden("Failed\r\n")
        if not is_full_post_spec(msg):
            return HttpResponseForbidden("Failed\r\n")
        msg['author'] = author
        post = get_post(msg, True)
        if len(post) <= 0:
            return HttpResponseForbidden("Failed\r\n")
        post = post[0]
        if len(post.uuid) != 0:
            post = modify_post(msg, post)
        post.save()
        return HttpResponse("Success\r\n")
    return HttpResponseForbidden("Not implemented\r\n")

