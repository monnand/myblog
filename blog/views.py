from django.http import HttpResponse, HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.http import HttpRequest
from django.http import Http404
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

from blog.models import Post, Author, BlogConfig
from blog.decode import decode_post, dump_html

def get_blog_config():
    return BlogConfig.get()

@csrf_exempt
def set_config(request):
    if request.method == 'POST':
        msg = request.POST['msg']
        authorname = request.POST['author']
        key = request.POST['key']
        author = Author.objects.filter(name=authorname)
        if len(author) == 0:
            return HttpResponseForbidden("Failed\r\n")
        author = author[0]
        if not author.can_set_config:
            return HttpResponseForbidden("Failed\r\n")
        msg = decode_post(msg, author.decrypt_key, key)
        bc = get_blog_config()
        if msg.has_key('title'):
            bc.title = msg['title']
        if msg.has_key('subtitlte'):
            bc.subtitle = msg['subtitle']
        if msg.has_key('nr_posts_per_page'):
            bc.nr_posts_per_page = int(msg['nr_posts_per_page'])
        bc.save()
        return HttpResponse("Success\r\n")
    return HttpResponseForbidden("Not implemented\r\n")

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
                msg['can_set_config'] = True
            else:
                return HttpResponseForbidden("Failed\r\n")
        else:
            author = author[0]
            if author.can_add_user:
                msg = decode_post(msg, author.decrypt_key, key)
                if not msg.has_key('can_set_config'):
                    msg['can_set_config'] = False
            else:
                return HttpResponseForbidden("Failed\r\n")
        new_author = Author(name=msg['name'], decrypt_key=msg['decrypt_key'], \
                email=msg['email'], about=msg['about'], \
                can_add_user=msg['can_add_user'], \
                can_set_config=msg['can_set_config'])
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
        if post.content_format != msg['content_format']:
            post.content_format = msg['content_format']
        post.content_html = dump_html(post.content, post.content_format)
        modified = True
    if post.content_format != msg['content_format']:
        post.content_format = msg['content_format']
        post.content_html = dump_html(post.content, post.content_format)
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

def view_post_content(request, slug, lang='enUS'):
    if request.method == 'POST':
        return HttpResponseForbidden("Not implemented\r\n")
    msg = {}
    msg['slug'] = slug
    msg['language'] = lang
    post = get_post(msg)
    if post is None or len(post) > 1:
        raise Http404
    post = post[0]
    bc = get_blog_config()
    return render_to_response('post.html', {'config':bc, 'post': post})

def view_posts_list(request, page_nr = 1, post_per_page = 10):
    if request.method == 'POST':
        return HttpResponseForbidden("Not implemented\r\n")
    page_nr = int(page_nr) - 1
    if page_nr < 0:
        page_nr = 0
    post_per_page = int(post_per_page)
    start = int(page_nr) * int(post_per_page)
    end = start + int(post_per_page)
    posts = Post.objects.all()[start:end]
    nr_posts = Post.objects.count()
    nr_pages = nr_posts/post_per_page
    if nr_posts % post_per_page:
        nr_pages += 1
    bc = get_blog_config()
    return render_to_response('postslist.html', {'config': bc, \
            'posts': posts, \
            'pages':range(1, nr_pages + 1), 'postsperpage': post_per_page})

