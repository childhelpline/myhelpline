"""myhelpline URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""

from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from django.views.static import serve
from django.views.i18n import JavaScriptCatalog
from django.contrib.staticfiles import views as staticfiles_views
from django.contrib.auth.views import login

from helpline import urls as helpline_urls
from helpline import views as helpline_views
from faq import urls as faq_urls

from messaging import urls as messaging_urls

admin.site.site_header = 'Helpline'
admin.site.site_title = 'Helpline'

urlpatterns = [
    url(r'^admin_tools/', include('admin_tools.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/v1/', include('api.urls')),
    url(r'^helpline/', include(helpline_urls)),
    url(r'^faq/', include(faq_urls)),
    url(r'^helpdesk/', include('helpdesk.urls', namespace='helpdesk')),
    url(r'^messaging/', include(messaging_urls, namespace='messaging')),
    url(r'^avatar/', include('avatar.urls')),
    url('^accounts/login/$', login, {
        'template_name': 'helpline/login.html'}, name='login'),
    url('^accounts/logout/$', helpline_views.logout, name='logout'),
    url('^$', helpline_views.helpline_home, name='helpline_home'),
    url('i18n/', include('django.conf.urls.i18n')),
]

if settings.DEBUG:
    urlpatterns += [
        url(r'^static/(?P<path>.*)$', serve),
    ]
else:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)

urlpatterns += [
    url(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]

urlpatterns += [
    url(r'^jsi18n/$', JavaScriptCatalog.as_view(), name='javascript-catalog'),
]

urlpatterns += [
    url('admin/doc/', include('django.contrib.admindocs.urls'))
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]

admin.site.site_header = settings.ADMIN_SITE_HEADER
