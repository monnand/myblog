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
from django.views.decorators.csrf import csrf_exempt, csrf_protect
import django

from django.contrib.syndication.views import Feed
from django.contrib.sites.models import get_current_site

import datetime
import os
import os.path
import re
import json

from blog.models import Post, Author, BlogConfig, Tag, Reader, Comment
from blog.decode import decode_post, dump_html
from blog.forms import PostCommentForm
from captcha.CaptchasDotNet import CaptchasDotNet

class BlogFeed(Feed):
    def title(self):
        bc = BlogConfig.get()
        return bc.title
    def description(self):
        bc = BlogConfig.get()
        return bc.subtitle

    def link(self):
        bc = BlogConfig.get()
        return bc.link
    def items(self):
        ret = Post.objects.all()[:100]
        return ret
    def item_title(self, item):
        return item.title
    def item_description(self, item):
        return item.content_html
    def item_link(self, item):
        bc = BlogConfig.get()
        url = os.path.join(bc.link, "p", item.slug, item.language)
        return url
    def item_author_name(self, item):
        return item.author.name
    def item_author_email(self, item):
        return item.author.email
    def item_pubdate(self, item):
        return item.created

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
        bc = BlogConfig.get()
        if msg.has_key('title'):
            bc.title = msg['title']
        if msg.has_key('subtitle'):
            bc.subtitle = msg['subtitle']
        if msg.has_key('nr_posts_per_page'):
            bc.nr_posts_per_page = int(msg['nr_posts_per_page'])
        if msg.has_key('captcha_name'):
            bc.captcha_name = msg['captcha_name']
        if msg.has_key('captcha_secret'):
            bc.captcha_secret = msg['captcha_secret']
        if msg.has_key('nr_poptags'):
            bc.nr_poptags = int(msg['nr_poptags'])
        if msg.has_key('about'):
            bc.about = msg['about']
        if msg.has_key('domain_name'):
            bc.domain_name = msg['domain_name']
        if msg.has_key('link'):
            bc.link = msg['link']
        if msg.has_key('license'):
            bc.license = msg['license']

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
    allow_comment = True
    if msg.has_key('allow_comment'):
        allow_comment = bool(msg['allow_comment'])
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
            uuid="",    \
            allow_comment=allow_comment)
    post.save()
    if msg.has_key("tags"):
        for tag in msg['tags']:
            t = get_tag(tag)
            t.nr_refs += 1
            t.save()
            post.tags.add(t)
    return [post]

def get_tag(tag, create = True):
    try:
        ret = Tag.objects.get(tag=tag)
    except:
        if not create:
            return None
        ret = Tag(tag=tag, nr_refs=0)
    return ret

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
    if msg.has_key("tags"):
        for etag in post.tags.all():
            found = False
            for tag in msg['tags']:
                if tag == etag.tag:
                    found = True
                    break
            if not found:
                post.tags.remove(etag)
                etag.nr_refs -= 1
                if etag.nr_refs == 0:
                    etag.delete()
                else:
                    etag.save()
                modified = True
        for tag in msg['tags']:
            found = False
            for etag in post.tags.all():
                if tag == etag.tag:
                    found = True
                    break
            if not found:
                t = get_tag(tag)
                t.nr_refs += 1
                t.save()
                post.tags.add(t)
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

def render_to_resp(template, kv):
    bc = BlogConfig.get()
    poptags = Tag.objects.all()[:bc.nr_poptags]
    meta = {'config':bc, 'poptags':poptags}
    meta.update(kv)
    return render_to_response(template, meta)

@csrf_exempt
def post_comment(request, postid):
    if request.method == 'POST':
        post = Post.objects.filter(id=int(postid))
        if len(post) == 0:
            raise Http404
        post = post[0]
        form = PostCommentForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            url = form.cleaned_data['url']
            email = form.cleaned_data['email']
            content= form.cleaned_data['content']
            password = form.cleaned_data['password']
            random = request.POST['random']
            now = datetime.datetime.now()
            reader = Reader.objects.filter(name=name)

            captcha = BlogConfig.get_captcha()
            if captcha is not None:
                if not captcha.validate(random):
                    return HttpResponseRedirect('/id/' + postid + "/captchaerr")
                if not captcha.verify(password):
                    return HttpResponseRedirect('/id/' + postid + "/captchaerr")

            if len(reader) == 0:
                reader = Reader(name=name, url=url, email=email)
                reader.save()
            else:
                reader = reader[0]
                if len(url) != 0:
                    if reader.url != url:
                        reader.url = url
                if len(email) != 0:
                    if reader.email != email:
                        reader.email = email
                reader.save()
            comment = Comment(reader=reader, \
                    post=post,\
                    content=content, \
                    created=now)
            comment.save()
            return HttpResponseRedirect('/id/' + postid)

    return HttpResponseForbidden("Not implemented\r\n")

def respond_post(post):
    comments = Comment.objects.filter(post__id=post.id)
    form = PostCommentForm()
    captcha = BlogConfig.get_captcha()
    random = captcha.random()
    form.fields['random'] = django.forms.CharField(initial=random, \
            widget=django.forms.widgets.HiddenInput())
    nr_comments = len(comments)
    return render_to_resp('post.html', \
            {'post': post, 'commentform':form, 'comments':comments, \
            'captcha_img': captcha.image(), \
            'captcha_audio': captcha.audio_url(), \
            'errormsg': '', 'nr_comments':nr_comments})


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
    return respond_post(post)

def view_post_by_id(request, postid, err = ''):
    if request.method == 'POST':
        return HttpResponseForbidden("Not implemented\r\n")
    post = Post.objects.filter(id=postid)
    if len(post) == 0:
        raise Http404
    post = post[0]
    return respond_post(post)

def resp_posts_list(posts, page_nr = 1, url_before_pgn = "l", url_after_pgn = ""):
    bc = BlogConfig.get()
    post_per_page = bc.nr_posts_per_page
    page_nr = page_nr - 1
    if page_nr < 0:
        page_nr = 0
    start = page_nr * post_per_page
    end = start + post_per_page
    nr_posts = posts.count()
    nr_pages = nr_posts/post_per_page
    if nr_posts % post_per_page:
        nr_pages += 1
    return render_to_resp('postslist.html', {'posts': posts[start:end], \
            'pages':range(1, nr_pages + 1), 'url_before_pgn': url_before_pgn, \
            'url_after_pgn': url_after_pgn})


def view_posts_list(request, page_nr = 1, lang = 'all'):
    if request.method == 'POST':
        return HttpResponseForbidden("Not implemented\r\n")
    posts = []
    if len(lang) != 4:
        posts = Post.objects.all()
        lang = 'all'
    else:
        posts = Post.objects.filter(language=lang)
    return resp_posts_list(posts, int(page_nr), "l", lang)

#    bc = get_blog_config()
#    post_per_page = bc.nr_posts_per_page
#    page_nr = int(page_nr) - 1
#    if page_nr < 0:
#        page_nr = 0
#    start = int(page_nr) * post_per_page
#    end = start + post_per_page
#    posts = []
#    if len(lang) != 4:
#        posts = Post.objects.all()
#        lang = 'all'
#    else:
#        posts = Post.objects.filter(language=lang)
#    nr_posts = posts.count()
#    nr_pages = nr_posts/post_per_page
#    if nr_posts % post_per_page:
#        nr_pages += 1
#    return render_to_resp('postslist.html', {'posts': posts[start:end], \
#            'pages':range(1, nr_pages + 1), 'lang': lang})

def view_author(request, authorname):
    author = Author.objects.filter(name=authorname)
    if len(author) == 0:
        raise Http404
    author = author[0]
    return render_to_resp('author.html', {'author':author})

def view_about(request):
    return render_to_resp('about.html', {})

def view_tag(request, tid, page_nr = 1):
    if request.method == 'POST':
        return HttpResponseForbidden("Not implemented\r\n")
    posts = Post.objects.filter(tags__id=int(tid))
    if not page_nr:
        page_nr = 1
    return resp_posts_list(posts, int(page_nr), "tag/" + str(tid), "")

