# -*- coding: utf-8 -*-
"""Helpline views """

from django.conf.urls import include, url
from django.contrib.auth.views import login

import notifications.urls

from helpline import views

urlpatterns = [
    url('^$', views.home, name='dashboard_home'),
    url('^wall/$', views.wall, name='wall'),
    url('^leta/$', views.leta, name='leta'),
    url('^call/check/$', views.check_call, name='check_call'),
    url('^call/check/json/$', views.check_call, name='check_call'),
    url('^get-districts/$', views.get_districts, name='get_districts'),
    url('^sources/$', views.sources, name='nosources'),
    url('^sources/(?P<source>\w+)/$', views.sources, name='mysources'),
    url('^myaccount/$', views.myaccount, name='myaccount'),
    url('^myaccount/edit/$', views.edit_myaccount, name='edit_myaccount'),
    url('^manageusers/$', views.manage_users, name='manageusers'),
    url('^queue/log/$', views.queue_log, name='queue_log'),
    url('^queue/leave/$', views.queue_leave, name='queue_leave'),
    url(r'^queue/remove/(?P<auth>\w+)/$', views.queue_remove,
        name='queue_remove'),
    url('^queue/pause/$', views.queue_pause, name='queue_pause'),
    url('^queue/unpause/$', views.queue_unpause, name='queue_unpause'),
    url('^walkin/$', views.walkin, name='walkin'),
    url('^call/$', views.callform, name='callform'),
    url('^faq/$', views.faq, name='faq'),
    url(r'^reports/(?P<report>\w+)/$', views.reports, name='dashboardreports'),
    url(r'^reports/(?P<report>\w+)/$', views.reports, name='adminreports'),
    url(r'^reports/(?P<report>\w+)/(?P<casetype>\w+)/$', views.reports,
        name='dashboardreports'),
    url(r'^reports/(?P<report>\w+)/(?P<casetype>\w+)/$', views.reports,
        name='adminreports'),
    url(r'^charts/(?P<report>\w+)/$', views.report_charts,
        name='report_charts'),
    url(r'^charts/(?P<report>\w+)/(?P<casetype>\w+)/$', views.report_charts,
        name='report_charts'),
    url(r'^reports/(?P<report>\w+)/$', views.reports, name='adminreports'),
    url(r'^reports/(?P<report>\w+)/(?P<casetype>\w+)/$', views.reports,
        name='dashboardreports'),
    url(r'^forms/(?P<form_name>\w+)/$', views.my_forms, name='my_forms'),
    url(r'^form/(?P<form_name>\w+)/$', views.case_form, name='case_form'),
    url('^ajax/get_subcategory/(?P<category>.+)/$', views.ajax_get_subcategory,
        name='get_subcategory'),
    url('^ajax/get_sub_subcategory/(?P<category>.+)/$',
        views.ajax_get_sub_subcategory, name='get_sub_subcategory'),
    url('^ajax/call/$', views.save_call_form, name='save_call_form'),
    url('^ajax/dispose/$', views.save_disposition_form,
        name='save_disposition_form'),
    url('^ajax/average/talktime/$', views.average_talk_time,
        name='average_talk_time'),
    url('^ajax/average/holdtime/$', views.average_talk_time,
        name='average_hold_time'),
    url(r'^ajax/report/factory/(?P<report>\w+)/$', views.ajax_admin_report,
        name='ajax_admin_report'),
    url(r'^ajax/report/factory/(?P<report>\w+)/(?P<casetype>\w+)/$',
        views.ajax_admin_report, name='ajax_admin_report'),
    url('^status/web/presence/$', views.web_presence, name='web_presence'),
    url(r'^selectable/', include('selectable.urls')),
    url('^login/$', login, {'template_name': 'helpline/login.html'},
        name='helpline_login'),
    url('^logout/$', views.logout, name='helpline_logout'),
    url(r'^inbox/notifications/',
        include(notifications.urls, namespace='notifications')),
    url(r'^alert/(?P<auth>\w+)/(?P<dialstatus>\w+)/(?P<case_id>\w+)/$',
        views.asterisk_alert, name='asterisk_alert'),
]

# Realtime Operator functions.

urlpatterns += [
    url('^queues/$', views.queues, name='queues'),
]
