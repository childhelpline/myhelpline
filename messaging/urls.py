#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls import url
from . import views


urlpatterns = (
    url(r'^$', views.messaging, name='messaging'),
    url(r'^send/$', views.send, name='send_message'),
    url('^ajax/sms/actions$', views.sms_actions, name='sms_actions'),
    url('^ajax/sms/count$', views.sms_count, name='sms_count'),
    url(r'^sms/send/$', views.sms_send, name='send_message'),
    url('^sms/$', views.sms, name='sms_home'),
    url('^sms/new/$', views.sms_new, name='sms_new'),
)
