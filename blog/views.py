from django.http import HttpResponse, HttpResponseRedirect
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.utils.translation import activate
from django.utils.translation import get_language
from django.utils.translation import ugettext as _
import datetime
import os
import os.path
import re

from blog.models import Post

def post_blog(request):
