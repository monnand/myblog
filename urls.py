from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'myblog.views.home', name='home'),
    # url(r'^myblog/', include('myblog.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    (r'postblog/$', 'myblog.blog.views.post_blog'),
    (r'newauthor/$', 'myblog.blog.views.add_author'),
    (r'p/([^/]+/[^/]+)', 'myblog.blog.views.view_post_content'),
    (r'p/([^/]+)', 'myblog.blog.views.view_post_content'),
)
