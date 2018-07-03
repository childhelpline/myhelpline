from django.conf.urls import url
from panel import views

urlpatterns = [
    url('^$', views.home, name='home'),
    url('^$', views.home, name='all_queues'),
    url('^queues/$', views.queues, name='queues'),
    url('^queue/(?P<name>\w+)/$', views.queue, name='queue'),
    url('^spy/$', views.spy, name='spy'),
    url('^whisper/$', views.spy, name='whisper'),
    url('^barge/$', views.spy, name='barge'),
    url('^$', views.home, name='stats'),
    url('^$', views.home, name='check_new_version'),
    url('^$', views.home, name='language'),
]
