#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from datetime import timedelta, datetime, date, time as datetime_time
from helpline.forms import ReportFilterForm
from helpline.models import Messaging
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.template.context_processors import csrf
from django.views.decorators.http import require_POST

import django_tables2 as tables

from jsonview.decorators import json_view
from .forms import MessageForm

import os

from sendsms import api

import time

@login_required
def messaging(request):
    return render(request, 'messaging/dashboard.html', {
        'form': MessageForm(),
    })


@login_required
@require_POST
def send(request):
    try:
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.send()
            for contact in message.contacts:
                messenger = Messaging()
                messenger.hl_service = 'SMSService'
                messenger.hl_contact = contact
                messenger.hl_key = randint(123456789, 987654321)
                messenger.hl_status = 'Sent'
                messenger.hl_type = 'SMS'
                messenger.hl_content = form.cleaned_data.get('message')
                messenger.hl_staff = request.user.hl_users.hl_key
                messenger.hl_time = int(time.time())
                messenger.save()

            if len(message.contacts) == 1:
                return HttpResponse('Your message was sent to 1 recipient.')
            else:
                msg = 'Your message was sent to {0} ' \
                    'recipients.'.format(len(message.connections))
                return HttpResponse(msg)
        else:
            return HttpResponseBadRequest(str(form.errors))
    except:
        return HttpResponse("Unable to send message.", status=500)

@csrf_exempt
@json_view
def sms_actions(request):
    """SMS Actions handles sending of SMS,
    Marking as read and archiving"""

    # Action will be communicated in the request.
    action = request.POST.get('sendSMS')
    message_id = request.POST.get('id')

    if action == 'sendSMS':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = Messaging()
            message.hl_service = 'SMSService'
            message.hl_contact = form.cleaned_data.get('number')
            message.hl_key = randint(123456789,987654321)
            message.hl_status = 'Outbox'
            message.hl_type = 'SMS'
            message.hl_content = form.cleaned_data.get('message')
            message.hl_staff = request.user.hl_users.hl_key
            message.hl_time = int(time.time())
            message.save()

    if message_id:
        message = Messaging.objects.get(id=message_id)
    if request.POST.get('read'):
        message.hl_status = 'Old'
        message.save()
        return {'success':1,
                'message':'Message marked as read.'
               }
    ctx = {}
    ctx.update(csrf(request))

    # Send sms using sms_send api
    api.send_sms(body=form.cleaned_data.get('message'),
                 from_phone=message.hl_service,
                 to=[message.hl_contact])

    return {'success':1,
            'message':'SMS Sent Successfully.'
           }

@login_required
@require_POST
def sms_send(request):
    form = MessageForm(request.POST)
    if form.is_valid():
        message = form.send()
        if len(message) == 1:
            return HttpResponse('Your message was sent to 1 recipient.')
        else:
            msg = 'Your message was sent to {0} ' \
                'recipients.'.format(len(message))
            return HttpResponse(msg)
    else:
        return HttpResponseBadRequest(str(form.errors))

def sms(request):
    sms = Messaging.objects.all()
    form = ReportFilterForm(request.GET, initial={'queueid':'718874580'})
    sms_form = MessageForm()
    table = SMSTable(sms,order_by=(request.GET.get('sort','hl_status'),'-hl_time','id'))
    return render(request,'messaging/sms.html',{'table':table,
                                             'form':form,
                                             'sms_form':sms_form,
                                             'title':'SMS'})
@login_required
def sms_new(request):
    form = MessageForm()
    return render(request,'messaging/sms_new.html',{
                                             'form':form,
                                             'title':'SMS'}
    )

@login_required
def sms_count(request):
    """Return count of SMSs in Inbox"""
    sms_count = Messaging.objects.filter(hl_status__exact='Inbox').count()
    sms_count = sms_count if sms_count else ""
    return HttpResponse(sms_count)

class ReceievedColumn(tables.Column):
    """Return ctime from an epoch time stamp"""
    def render(self, value):
        os.environ['TZ'] = 'Africa/Nairobi'
        time.tzset()
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value))

class SMSTable(tables.Table):

    action = tables.TemplateColumn("{% if record.hl_status == 'Inbox' %}<button class='createR' value='{{ record.id}}'>Read</button><button class='reply' value='{{ record.id}}'>Reply</button>{% elif record.hl_status == 'Old' %}<button class='reply' value='{{ record.id}}'>Reply</button>{% endif %}",orderable=False)
    hl_time = ReceievedColumn()

    class Meta:
        model = Messaging
        attrs = {'class' : 'table table-bordered table-striped dataTable', 'id':'report_table'}
        ##unlocalise = ('holdtime','walkintime','talktime','callstart')
        fields = {'id','hl_contact','hl_status','hl_content','hl_time','action'}
        sequence = ('id','hl_contact','hl_status','hl_content','hl_time','action')

