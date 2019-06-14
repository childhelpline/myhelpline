# -*- coding: utf-8 -*-
"""Helpline views """

import os
import calendar

import time
from random import randint
import hashlib
import urllib

import imaplib,smtplib
import email
from django.core.mail import send_mail
import operator

from celery import Celery
from celery.decorators import task

from itertools import tee
import numbers

from datetime import timedelta, datetime, date, time as datetime_time

# from nameparser import HumanName
import requests
from django.db import connection
from collections import namedtuple

from django.shortcuts import render, redirect
from django.http import JsonResponse, Http404
from django.http import (HttpResponse, HttpResponseBadRequest,
                         HttpResponseForbidden, HttpResponseRedirect)
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.template.context_processors import csrf
from django.template.loader import render_to_string
from django.db.models import (Avg,Count)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models import Sum
from django.contrib.auth.views import login as django_login
from django.contrib.auth.views import logout as django_logout
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.db.models.signals import post_save
from django.conf import settings
from django.utils.translation import gettext as _
from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from django.contrib.sessions.models import Session

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from django.db import transaction

from django.core import serializers
# Django 1.10 breaks reverse imports.
try:
    from django.urls import reverse
except Exception as e:
    from django.core.urlresolvers import reverse

from notifications.signals import notify

import django_tables2 as tables

from django_tables2.config import RequestConfig
from django_tables2.export.export import TableExport
from django_tables2.export.views import ExportMixin

from crispy_forms.utils import render_crispy_form
from jsonview.decorators import json_view

from helpdesk.models import Ticket
from dateutil.relativedelta import relativedelta

from onadata.libs.utils.viewer_tools import (
    create_attachments_zipfile, export_def_from_filename, get_form)
from onadata.libs.exceptions import EnketoError
from onadata.libs.utils.viewer_tools import enketo_url, get_form, get_form_url
from onadata.apps.main.models import MetaData, UserProfile

from helpline.models import Report, HelplineUser,\
        Schedule, Case, Postcode,\
        Service, Hotdesk, Category, Clock,\
        MainCDR, Recorder, Address, Contact,\
        Messaging, Emails, SMSCDR, Cases

from helpline.forms import QueueLogForm,\
        ContactForm, DispositionForm, CaseSearchForm, RegisterProfileForm, RegisterUserForm, \
        ReportFilterForm, QueuePauseForm, CaseActionForm, ContactSearchForm

import json
from django.template.defaulttags import register
from onadata.apps.logger.models import Instance, XForm

from onadata.libs.utils.chart_tools import build_chart_data
from onadata.libs.utils.user_auth import (get_xform_and_perms, has_permission,
                                          helper_auth_helper)
from api.serializers import SmsSerializer
from graphos.sources.model import ModelDataSource
from graphos.sources.simple import SimpleDataSource
from graphos.renderers.flot import LineChart

def success(request):
    return render(request, 'helpline/success.html')
    
@login_required
def home(request):
    "Dashboard home"

    template = 'home'

    if not get_dashboard_stats(request):
        message = "Please Configure Service and assign forms"
        return redirect('/ona/%s?message=%s' %(request.user,message))
    else:
        home_statistics = get_dashboard_stats(request)

    status_count = get_status_count()
    case_search_form = CaseSearchForm()
    queue_form = QueueLogForm(request.POST)
    queue_pause_form = QueuePauseForm()
    queues = get_data_queues()

    default_service = Service.objects.all().first()

    if hasattr(default_service,'walkin_xform') and default_service.walkin_xform:
        default_service_xform = default_service.walkin_xform
    else:
        response = redirect('/ona/%s' % request.user.username)
        return response

    default_service_qa = default_service.qa_xform
    default_service_auth_token = default_service_xform.user.auth_token
    current_site = get_current_site(request)

    gtdata = []
    stdata = []
    
    # if default_service != '' and default_service > 0 and default_service_xform.pk  > 0:
    url = 'http://%s/ona/api/v1/charts/%s.json?field_name=_submission_time&limit=14' % (
        current_site,
        default_service_xform.pk
    )

    # Set headers
    headers = {
        'Authorization': 'Token %s' % (default_service_auth_token)
    }

    stat = requests.get(url, headers=headers).json() or {}


    # case priority statistics
    url = 'http://%s/ona/api/v1/charts/%s.json?field_name=case_priority' % (
        current_site,
        default_service_xform.pk
    )
    statex = requests.get(url, headers=headers).json() or {}
    
    forloop = 0
    for dt in get_item(stat, 'data'):
        t = [str(get_item(dt, '_submission_time')), get_item(dt, 'count')]
        gtdata.append(t)
        forloop += 1
        if forloop == 14:
            break

    stype = 'case_action'

    url = 'http://%s/ona/api/v1/charts/%s.json?field_name=reporter_county' \
     %(current_site, default_service_xform.pk)
    color = ['#CD5C5C','#000000','#8A2BE2','#A52A2A','#DEB887','#ADD8E6','#F08080','#90EE90','#F0E68C','#FFB6C1', \
    '#5F9EA0','#7FFF00','#D2691E','#FF7F50','#6495ED','#FFF8DC','#DC143C','#00FFFF','#00008B','#008B8B','#B8860B','#A9A9A9', \
    '#006400','#A9A9A9','#BDB76B','#8B008B','#556B2F','#FF8C00','#9932CC','#8B0000','#E9967A','#8FBC8F','#483D8B','#2F4F4F',\
    '#2F4F4F','#00CED1','#9400D3','#FF1493','#00BFFF','#696969','#696969','#1E90FF','#B22222','#FFFAF0','#228B22','#DCDCDC',\
    '#F8F8FF','#FFD700','#DAA520','#808080','#ADFF2F','#F0FFF0','#FF69B4','#FFE4C4','#4B0082','#FFFFF0','#E6E6FA',\
    '#FFF0F5','#7CFC00','#FFFACD','#FAFAD2','#90EE90','#D3D3D3','#F0F8FF','#FAEBD7','#F0FFFF','#F5F5DC','#7FFFD4','#FFA07A'
    ]
    stype = 'reporter_county'

    #for case status 
    status_data = requests.get(url, headers=headers).json()

    ic = 0
    othercount = 0
    datas = get_item(status_data, 'data')
    for dt in sorted(get_item(status_data, 'data'),reverse=True):#  status_data['data']:
        lbl = dt[str(stype)]
        if isinstance(lbl, list):
            lbl = lbl[0] if len(lbl) > 0 and lbl[0] != 'null' else '' #"Others"
        else:
            lbl = lbl if len(lbl) > 0  and lbl != 'null' else '' # "Others"

        col = color[ic]
        if ic < 9 and lbl != 'Others' and lbl != None:
            stdata.append({"label":str(lbl), "data":str(str(dt['count'])), "color":str(col)})
            ic += 1
        elif lbl != '' and  lbl != None:
            othercount += dt['count']
            ic += 1
        
    col = color[ic]
    stdata.append({"label":'Others', "data":str(othercount), "color":str(col)})

    if request.user.HelplineUser.hl_role == 'Counsellor':
        url_qa = 'http://%s/ona/api/v1/data/%s?query={"case_owner":"%s"}' % (
            current_site,
            default_service_qa.pk,
            request.user.username
        )
    else:
        url_qa = 'http://%s/ona/api/v1/data/%s' % (
            current_site,
            default_service_qa.pk
        )

    qa_stats = requests.get(url_qa, headers=headers).json() or {}
    stat_qa = 0;
    quiz = 0;

    for all_stats in qa_stats:
        if isinstance(all_stats,dict):
            for ev,qa_stat in all_stats.items():
                if ev.encode('utf-8') == 'qa_results/note_results':
                    if not str(qa_stat.encode('utf-8')).lower() == 'nan':
                        stat_qa = stat_qa + float(qa_stat.encode('utf-8')) # '%s || %s || ' %(stat_qa, qa_stat.encode('utf-8'))
            quiz += 1

    if quiz > 0:
        stat_qa = stat_qa/quiz


    high_priority = 0
    if statex.get('data',None) != None:
        for ke_item in statex['data']:
            if str(ke_item['case_priority'][0]) == 'High Priority':
                high_priority = ke_item['count']

    return render(request, 'helpline/%s.html' % template,
                {
                   'att': '',
                   'awt': '',
                   'case_search_form': case_search_form,
                   'status_count': status_count,
                   'gdata': gtdata,
                   'dt': stdata,
                   'priority_stat':high_priority,
                   'qa_stat':stat_qa,
                   'status_data':status_data,
                   'home':home_statistics
                })


@login_required
def leta(request):
    """Return the login duration and ready duration"""
    login_duration = request.user.HelplineUser.get_login_duration()
    ready = request.user.HelplineUser.get_ready_duration()
    return render(request, 'helpline/leta.html',
                  {'ld': login_duration,
                   'ready': ready})
@api_view(['POST'])
def user_api_update(request):
    state = 'False'
    error_message = 'No Success'
    if request.method == 'POST':
        hl_user = HelplineUser.objects.get(hl_key__exact=request.POST.get('agent'))
        hl_user.status = request.POST.get('status')
        hl_user.save()
    sms_list = HelplineUser.objects.all().order_by('-id')

    return JSONResponse({'data':sms_list, 'status':'Eror'})

@api_view(['GET', 'POST'])
def sync_sms(request):
    state = 'False'
    error_message = 'No Success'
    
    if request.method == 'POST':        
        serializer = SmsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return JsonResponse({'status':400,'message':'INVALID REQUEST'})

def sync_emails(request):
    message = {'message':'', 'count':0}
    try:
        mail = imaplib.IMAP4_SSL(settings.EMAIL_HOST)
        mail.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        mail.select('inbox')

        type, data = mail.search(None, 'SEEN')
        mail_ids = data[0]

        id_list = mail_ids.split() 
        mail_count = len(id_list)

        if mail_count > 1:
            first_email_id = int(id_list[0])
            latest_email_id = int(id_list[-1])
        elif mail_count == 1:
            first_email_id = int(id_list[0])
            latest_email_id = int(id_list[0])
        elif mail_count == 0:
            return HttpResponse("No new mails found ")



        for i in range(latest_email_id, first_email_id-1, -1):
            typ, data = mail.fetch(i, '(RFC822)')
            for response_part in data:
                model_mail = Emails()
                if isinstance(response_part, tuple):
                    msg = email.message_from_string(response_part[1])

                    model_mail.email_idkey = i
                    model_mail.email_from = msg['from']
                    model_mail.email_body = str(msg.get_payload())
                    model_mail.email_subject = msg['subject']
                    model_mail.email_date = msg['date']
                    model_mail.save()
                    message['count'] += 1
                    message['message'] = "Fetch complete"

    except Exception, e:
        message['message'] = "Could not complete fetch: %s" %e

    return HttpResponse(message['message'])

@login_required
def check(request):
    """Show login duration. Returns blank template"""
    return render(request, 'helpline/leta.html')


@login_required
def check_call(request):
    """Check if there is a call for request user"""
    my_case = request.user.HelplineUser.case
    if my_case:
        my_case.hl_popup = 'Done'
        my_case.save()
        request.user.HelplineUser.case = None
        request.user.HelplineUser.save()
        report = Report.objects.get(case=my_case)
        telephone = report.telephone
        contact, contact_created = Contact.objects.get_or_create(hl_contact=telephone)
        if contact_created or contact.address == None:
            address = Address(user=request.user)
            contact.address = address
            address.save()
            contact.save()

    else:
        telephone = None
        my_case = None

    response = JsonResponse(
        {
            'my_case': my_case.hl_case if my_case else None,
            'telephone': telephone,
            'name': contact.address.hl_names if my_case else None,
            'type': my_case.hl_data if my_case else 0
        }
    )
    return response


@csrf_exempt
def get_districts(request):
    """Return option field with list of districts from Address table"""
    if request.method == 'POST':
        districts = Postcode.objects.values_list('address3', flat=True).distinct()

    districts = Postcode.objects.values_list('address2', flat=True).distinct()
    return render(request, 'helpline/options.html', {'options':districts})


@login_required
def myaccount(request):
    """View request user account details page"""
    return render(request, 'helpline/profile.html')

@login_required
def manage_users(request,action=None,action_item=None):
    """View user management page"""
    
    message = ""
    data = {}
    # userlist = User.objects.all().filter(is_active=True)
    template = 'users'

    if action != None and action_item != None:
        action_user = User.objects.filter(HelplineUser__hl_key__exact=action_item).first()
        if action == 'delete':
            # del_user = new User()
            action_user.is_active = False;
            action_user.save()
            message = "User successfully deleted"
        elif action == 'profile':
            template = 'profile'
            data['template'] = 'user'
        elif action == 'edit':
            user = User.objects.get(HelplineUser__hl_key__exact=action_item)
            profile = user.HelplineUser

            form = RegisterUserForm(instance=user)
            profile_form = RegisterProfileForm(instance=profile)

            if request.user.is_authenticated() and request.user.id == user.id:
                if request.method == "POST":
                    # form = RegisterProfileForm(request.POST, request.FILES, instance=profile)            
                    form = RegisterUserForm(request.POST or None, request.FILES,instance=action_user)
                    profile_form = RegisterProfileForm(request.POST or None, request.FILES,instance=user_prof)

            data['template'] = 'user'
            template = 'user'
            data['form'] = form
            data['profileform'] = profile_form
            data['messs'] = ''
    
    userlist = User.objects.filter(is_active=True).exclude(HelplineUser=None).select_related('HelplineUser')
    data['systemusers'] = userlist
    return render(request, 'helpline/%s.html' %(template), data)

def increment_case_number():
    case = Cases.objects.all().order_by('case_number').last()

    if not case:
        return 100001
    else:
        return int(case.case_number) + int(1)
def get_case_number(case_source):
    case = Cases()
    caseid = increment_case_number()
    case.case_number = caseid
    case.case_source = case_source
    case.save()
    return caseid

@login_required
def case_number(request, case_source):
    caseid = get_case_number(case_source)
    return HttpResponse(caseid)

@login_required
def new_user(request):
    messages = []
    if request.method == 'POST':
        form = RegisterUserForm(request.POST, request.FILES)
        profile_form = RegisterProfileForm(request.POST, request.FILES)
        if form.is_valid() and profile_form.is_valid():
            user = User()
            try:
                user = form.save()
                user.refresh_from_db()

                user.HelplineUser.hl_names = "%s %s" %(form.cleaned_data.get('first_name'), \
                    form.cleaned_data.get('last_name'))
                user.HelplineUser.hl_nick = form.cleaned_data.get('username')
                user.HelplineUser.hl_calls = 0
                user.HelplineUser.hl_email = "%s" % profile_form.cleaned_data.get('useremail')

                user.HelplineUser.hl_area = ''
                user.HelplineUser.hl_phone = profile_form.cleaned_data.get('phone')
                user.HelplineUser.hl_branch = ''
                user.HelplineUser.hl_case = 0

                user.HelplineUser.hl_status = 'Idle'
                user.HelplineUser.hl_jabber = "" # "%s@%s" % (user.username, settings.BASE_DOMAIN)
                user.HelplineUser.hl_pass = hashlib.md5("1234").hexdigest()

                user.HelplineUser.hl_role = "%s" % profile_form.cleaned_data.get('userrole')
                # user.save()

                uploaded_file_url = ''                
                filename = ''
                if request.FILES['avatar']:
                    myfile = request.FILES['avatar']
                    fs = FileSystemStorage()
                    filename = fs.save(myfile.name, myfile)
                    uploaded_file_url = fs.url(filename)

                user.HelplineUser.hl_avatar = uploaded_file_url
                user.HelplineUser.hl_time = time.time()

                user.HelplineUser.save()

                # share case form
                default_service = Service.objects.all().first()
                default_service_xform = default_service.walkin_xform
                default_service_auth_token = default_service_xform.user.auth_token
                current_site = get_current_site(request)

                if default_service != '' and default_service != 0 and default_service_xform:
                    url = 'http://%s/ona/api/v1/%s/share/' % (
                        current_site,
                        default_service_xform.pk
                    )
                    headers = {
                        'Authorization': 'Token %s' % (default_service_auth_token),
                        'username':user.username,
                        'role':'manager'
                    }
                    requests.post(url, headers=headers)

                messages.append("User saved successfully %s" % user.HelplineUser.hl_email)
                form = RegisterUserForm()
                profile_form = RegisterProfileForm()

            except Exception as e:
                form = RegisterUserForm(request.POST)
                profile_form = RegisterProfileForm(request.POST, request.FILES)
                messages.append('Error saving user: %s' % (e))
        else:
            # messages.error(request, "Error")
            messages.append("Invalid form")
    else:
        form = RegisterUserForm()
        profile_form = RegisterProfileForm()
    return render(request, 'helpline/user.html', {'form':form, 'profileform':profile_form, 'messs':messages})

@login_required
def edit_user(request,userid):

    user = get_object_or_404(User,pk=pk) 
    user = User.objects.get(pk=pk)
    user_profile = User.HelplineUser
    user_form = RegisterUserForm(request.POST or None, instance=user)
    profile_form = RegisterProfileForm(request.POST or None,instance=user_profile)
    messages = []
    if request.method == 'POST':
        form = RegisterUserForm(request.POST, request.FILES)
        profile_form = RegisterProfileForm(request.POST, request.FILES)
        if form.is_valid() and profile_form.is_valid():
            user = User()
            try:
                user = form.save()
                user.refresh_from_db()

                user.HelplineUser.hl_names = "%s %s" %(form.cleaned_data.get('first_name'), \
                    form.cleaned_data.get('first_name'))
                user.HelplineUser.hl_nick = form.cleaned_data.get('username')
                user.HelplineUser.hl_calls = 0
                user.HelplineUser.hl_email = "%s" % profile_form.cleaned_data.get('useremail')

                user.HelplineUser.hl_area = ''
                user.HelplineUser.hl_phone = profile_form.cleaned_data.get('phone')
                user.HelplineUser.hl_branch = ''
                user.HelplineUser.hl_case = 0

                user.HelplineUser.hl_status = 'Idle'
                user.HelplineUser.hl_jabber = "" # "%s@%s" % (user.username, settings.BASE_DOMAIN)
                user.HelplineUser.hl_pass = hashlib.md5("1234").hexdigest()

                user.HelplineUser.hl_role = "%s" % profile_form.cleaned_data.get('userrole')
                # user.save()

                uploaded_file_url = ''                
                filename = ''
                if request.FILES['avatar']:
                    myfile = request.FILES['avatar']
                    fs = FileSystemStorage()
                    filename = fs.save(myfile.name, myfile)
                    uploaded_file_url = fs.url(filename)

                user.HelplineUser.hl_avatar = uploaded_file_url
                user.HelplineUser.hl_time = time.time()

                user.HelplineUser.save()

                # share case form
                default_service = Service.objects.all().first()
                default_service_xform = default_service.walkin_xform
                default_service_auth_token = default_service_xform.user.auth_token
                current_site = get_current_site(request)

                if default_service != '' and default_service != 0 and default_service_xform:
                    url = 'http://%s/ona/api/v1/%s/share/' % (
                        current_site,
                        default_service_xform.pk
                    )
                    headers = {
                        'Authorization': 'Token %s' % (default_service_auth_token),
                        'username':user.username,
                        'role':'dataentry'
                    }
                    requests.post(url, headers=headers)

                messages.append("User saved successfully")
                form = RegisterUserForm()
                profile_form = RegisterProfileForm()

            except Exception as e:
                form = RegisterUserForm(request.POST)
                profile_form = RegisterProfileForm(request.POST, request.FILES)
                messages.append('Error saving user: %s' % (e))
        else:
            # messages.error(request, "Error")
            messages.append("Invalid form")
    else:
        form = RegisterUserForm()
        profile_form = RegisterProfileForm()
    return render(request, 'helpline/user.html', {'form':form, 'profileform':profile_form, 'messs':messages})


@login_required
def user_profile(request, user_id):
    user_edit = User.objects.get(HelplineUser__hl_key__exact=user_id) # get_object_or_404(HelplineUser, user_id)
    user_prof = user_edit.HelplineUser
    message = ''
    form = RegisterUserForm(request.POST or None, request.FILES,instance=user_edit)
    profile_form = RegisterProfileForm(request.POST or None, request.FILES,instance=user_prof)
    if request.method == 'POST':
        form = RegisterUserForm(request.POST, request.FILES,instance=user_edit)
        if form.is_valid():
            user = HelplineUser()
            try:
                user.hl_key = randint(123456789, 999999999)
                user.hl_auth = randint(1234, 9999)
                user.user_id = 2
                user.hl_role = form.cleaned_data['userrole']
                user.hl_names = form.cleaned_data['names']
                user.hl_nick = form.cleaned_data['username']
                user.hl_email = form.cleaned_data['useremail']
                user.hl_phone = form.cleaned_data['phone']

                uploaded_file_url = ''
                filename = ''
                if request.FILES['avatar']:
                    myfile = request.FILES['avatar']
                    fs = FileSystemStorage()
                    filename = fs.save(myfile.name, myfile)
                    uploaded_file_url = fs.url(filename)

                

                user.hl_avatar = uploaded_file_url
                user.hl_time = time.time()
                user.save()
                message = "User saved succeefully"

            except Exception as e:
                message = 'Error saving user: %s' % e
        else:
            messages.error(request, "Error")
            message = "Invalid form"
    else:
        form = RegisterUserForm(instance=user_edit)
        user_form = RegisterProfileForm(instance=user_prof)

    return render(request, 'helpline/user.html', {'form':form,'profileform':profile_form, 'message':message})



@login_required
def queue_logx(request):
    """Join Asterisk queues."""
    services = Service.objects.all()
    if request.method == 'POST':
        queue_form = QueueLogForm(request.POST)
        if queue_form.is_valid():
            extension = queue_form.cleaned_data['softphone']
            try:
                queue_status = True # requests.post('%s/api/v1/call/login?login=%s&exten=%s' %(settings.CALL_API_URL,request.user.HelplineUser.hl_key,extension)).json()
                if queue_status:
                    # Get the hotline object from the extension.
                    hotdesk = Hotdesk.objects.get(extension=extension)

                    hotdesk.jabber = 'helpline@jabber'
                    hotdesk.status = 'Available'
                    hotdesk.agent = request.user.HelplineUser.hl_key
                    hotdesk.user = request.user

                    agent = request.user.HelplineUser
                    agent.hl_status = 'Available'
                    agent.hl_exten = "%s/%s" % (hotdesk.extension_type, hotdesk.extension)
                    agent.save()

                    message = "Successfully joined queue"
                else:
                    message = "Could not successfully join queue, try again!"
            except Exception as e:
                message = e
            return redirect("/helpline/#%s" % message)

@login_required
def queue_log(request):
    """Join Asterisk queues."""
    agent = request.user.HelplineUser
    agent.hl_status = 'Online'
    agent.save()
    # request.session['cdr_key'] = queue_status['data']
    request.session['queuejoin'] = 'join'
    request.session['queuestatus'] = 'queuepause'
    # request.session['extension'] = extension
    response =  HttpResponse({'status':'200'})
    return response


def queue_leave(request):
    """Leave Asterisk queues."""
    queue_status = requests.post('%s/clk/agent/?action=0&agent=%s' %(settings.CALL_API_URL,\
        request.user.HelplineUser.hl_key)).json()
    hl_user = HelplineUser.objects.get(hl_key=request.user.HelplineUser.hl_key)
    hl_user.hl_exten = ''
    hl_user.hl_jabber = ''
    hl_user.hl_status = 'Offline'

    request.session['queuejoin'] = ''
    request.session['queuestatus'] = ''

    hl_user.save()
    message = "The message"
    return redirect("/helpline/#%s" % (message))


@json_view
def queue_remove(request, auth):
    """Remove a user from the Asterisk queue."""
    agent = HelplineUser.objects.get(hl_auth=auth)
    agent.hl_status = 'Idle'
    data = {}

    return redirect("/helpline/status/web/presence/#%s" % (data))


def queue_pause(request):
    """Pause Asterisk Queue member"""
    message = "Nothing to do"
    # form = QueuePauseForm(request.POST)
    # if form.is_valid():
    #     schedules = Schedule.objects.filter(user=request.user)
    #     if not schedules:
    #         message = _("Agent does not have any assigned schedule")
    #     for schedule in schedules:
    #         message = backend.pause_queue_member(
    #             queue='%s' % (schedule.service.queue),
    #             interface='%s' % (request.user.HelplineUser.hl_exten),
    #             paused=True
    #         )
    #         clock = Clock()
    #         clock.user = request.user
    #         clock.hl_clock = form.cleaned_data.get('reason')
    #         clock.service = schedule.service
    #         clock.hl_time = int(time.time())
    #         clock.save()
    #     request.user.HelplineUser.hl_status = 'Pause'
    #     request.user.HelplineUser.save()
    # else:
    #     message = "failed"

    return redirect("/helpline/#%s" % (message))


def queue_unpause(request):
    """Unpause Asterisk Queue member"""
    schedules = Schedule.objects.filter(user=request.user)
    if schedules:
        message = _("Nothing to do")
    else:
        message = _("Agent does not have any assigned schedule")

    request.user.HelplineUser.hl_status = 'Available'
    request.user.HelplineUser.save()

    return redirect("/helpline/#%s" % (message))

def presence(request,presence):
    try:
        request.user.HelplineUser.hl_status = presence
        request.user.HelplineUser.save()
        return True
    except Exception as e:
        return False

def walkin(request):
    """Render CallForm manualy."""
    form = ContactForm()

    return render(request, 'helpline/walkin.html',
                  {'form': form})


def callform(request):
    """Render call form"""
    return render(request, 'helpline/callform.html')


def faq(request):
    """Render FAQ app"""
    return render(request, 'helpline/callform.html')

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, "")

@register.simple_tag
def setting(setting_item):
    return getattr(settings, setting_item, "")

@register.filter("timestamp")
def timestamp(value):
    return datetime.fromtimestamp(value)

@login_required
def caseview(request, form_name, case_id):
    """View case or submission information"""

    default_service = Service.objects.all().first()
    default_service_xform = default_service.walkin_xform
    default_service_auth_token =  default_service_xform.user.auth_token
    current_site = get_current_site(request)

    url = 'http://%s/ona/api/v1/data/%s/' % (
        current_site,
        default_service_xform.pk
    )

    # Graph data
    headers = {
        'Authorization': 'Token %s' % (default_service_auth_token)
    }

    # Data Request and processing
    # Get default service
    xform_det = default_service.walkin_xform
    request_string = ''

    stat = requests.get(url + case_id + request_string, headers=headers).json()
    history = requests.get(url + case_id + '/history', headers=headers).json()

    statrecords = []
    recordkeys = []
    history_rec = []

    ##brings up data only for existing records
    def get_records(recs):
        return_obj = []
        record = {}

        for key, value in recs.items():
            #if not (key.startswith('_') and key.endswith('_')):# str(key) == "_id":
            key = str(key)
            if key.find('/') != -1:
                k = key.split('/')
                l = len(k)
                kk = str(k[l-1])
            else:
                kk = str(key)
            if isinstance(value, dict) and len(value) >= 1:
                record.update(get_records(value))
            elif isinstance(value, list) and len(value) >= 1:
                if isinstance(value[0], dict):
                    record.update(get_records(value[0]))
            else:
                if not kk in recordkeys and not kk.endswith('ID') and str(value) != 'yes' \
                and str(value) != 'no' and not (kk.startswith('_') and kk != '_id' and kk != '_submission_time'  \
                    and kk != '_last_edited'):
                    recordkeys.append(kk)
                record.update({kk : str(value).capitalize()})
        return record


    if isinstance(stat, dict) and len(stat) > 1:
        statrecords.append(get_records(stat))

    for hist in history:
        if isinstance(hist, dict) and len(hist) > 1:
            history_rec.append(get_records(hist))

    if len(recordkeys) > 0:
        recordkeys.append('Date Created')
    else:
        recordkeys = False

    data = {
        'stat':stat,
        'statrecords':statrecords[0],
        'recordkeys':recordkeys,
        'history':history_rec,
        'xform': default_service_xform,
        'kemcount':0
    }
    htmltemplate = "helpline/instance.html"

    return render(request, htmltemplate, data)

def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]

@login_required
def general_reports(request, report='cases'):
    """Report processing and rendering"""
    default_service = Service.objects.all().first()
    default_service_xform = default_service.walkin_xform
    default_service_auth_token = default_service_xform.user.auth_token
    current_site = get_current_site(request)

    # Graph data
    headers = {
        'Authorization': 'Token %s' % (default_service_auth_token)
    }

    id_string = str(default_service_xform)
    username = request.user.username

    owner = get_object_or_404(User, username__iexact=username)
    xform = get_form({'id_string__iexact': str(default_service.walkin_xform)})

    query = request.GET.get('q', '')
    datetime_range = request.GET.get("datetime_range") or ''
    agent = request.GET.get("agent")
    category = request.GET.get("category", "")
    form = ReportFilterForm(request.GET)
    dashboard_stats = get_dashboard_stats(request.user)
    report_title = {report: _(str(report).capitalize() + " Reports")}

    data = {
        'owner': default_service_xform.user,
        'xform': default_service_xform,
        'title': report_title.get(report),
        'report': report,
        'form': form,
        'datetime_range': datetime_range,
        'dashboard_stats': dashboard_stats,
        'query': query
    }

    request_string = ''
    query_string = ''

    if datetime_range != '':
        start_dates, end_dates = [datetime_range.split(" - ")[0], datetime_range.split(" - ")[1]]
        # start_date = datetime.strptime(start_date, '%Y-%m-%d')
        # end_date = datetime.strptime(end_date, '%Y-%m-%d')

        start_date = datetime.strptime(start_dates, '%m/%d/%Y  %I:%M %p')
        end_date = datetime.strptime(end_dates, '%m/%d/%Y  %I:%M %p')

        d1 = start_date.strftime('%Y-%m-%d %H:%M')
        d2 = end_date.strftime('%Y-%m-%d %H:%M')

        datetime_range = '%s-%s' %(d1,d2)
    else:
        today = datetime.now()
        datetime_range = '%s-%s' %(datetime.strftime(today,'%Y-%m-%d'),datetime.strftime(today,'%Y-%m-%d'))


    htmltemplate = 'helpline/report_cases.html'

    if report.lower() == 'calls':
        """For call reports"""
        htmltemplate = "helpline/report.html"
        if datetime_range == '':
            call_url = "%s/clk/cdr/" %(settings.CALL_API_URL)
        else:
            call_url = "%s/clk/cdr/?chan_ts_f=%s" %(settings.CALL_API_URL, \
            datetime_range)
        


        call_data = requests.post(call_url).json()
        data['report_data'] = call_data
        data['urls'] = call_url

    if report.lower() == 'voicemails':
        """For call reports"""
        htmltemplate = "helpline/report.html"
        call_url = "%s/clk/cdr/?chan_ts_f=%s" %(settings.CALL_API_URL, \
            datetime_range)
        call_data = requests.post(call_url).json()
        data['report_data'] = filter(lambda call_data: call_data['voicemail'], call_data)
    elif report.lower() == 'emails':
        """For call reports"""
        email_data = Emails.objects.all()
        data['report_data'] = email_data
        htmltemplate = "helpline/reports_emails.html"

    elif report.lower() == 'sms':
        """For call reports"""
        sms_data = SMSCDR.objects.all()
        data['report_data'] = sms_data
        htmltemplate = "helpline/reports_sms.html"
    elif report.lower() == 'cases':
        """For case reports"""

        xforms = requests.get('http://%s/ona/api/v1/forms' % (current_site), \
            headers=headers).json()
        xformx = {}

        #split to get xform object
        for xfrm in xforms:
            if str(xfrm['id_string']) == id_string:
                for key, frm in xfrm.items():
                    xformx.update({str(key):str(frm)})

        if request.user.HelplineUser.hl_role == 'Counsellor':
            if query_string == '':
                query_string = '"case_owner":{"$i":"%s"}' %(username)
            else:
                query_string += ',"case_owner":{"$i":"%s"}' %(username)

        ur = 'http://%s/ona/api/v1/data/%s?query={%s}%s&page=1&page_size=50' %(current_site, \
            default_service_xform.pk, query_string, request_string)

        stat = requests.get('http://%s/ona/api/v1/data/%s?query={%s}%s&page=1&page_size=50' %(current_site, \
            default_service_xform.pk, query_string,  request_string), headers=headers).json()
        # + '&sort={"_id":-1}'
        # data['statss'] = "Cheru Data: %s" % stat
        data['ur'] = ur
        statrecords = []
        recordkeys = []

        ##brings up data only for existing records
        def get_records(recs):
            return_obj = []
            record = {}

            for key, value in recs.items():
                #if not (key.startswith('_') and key.endswith('_')):# str(key) == "_id":
                key = str(key)
                if key.find('/') != -1:
                    k = key.split('/')
                    l = len(k)
                    kk = str(k[l-1])
                else:
                    kk = str(key)
                if isinstance(value, dict) and len(value) >= 1:
                    record.update(get_records(value))
                elif isinstance(value, list) and len(value) >= 1:
                    if isinstance(value[0], dict):
                        record.update(get_records(value[0]))
                else:
                    if not kk in recordkeys and not kk.endswith('ID') and str(value) != 'yes' and \
                    str(value) != 'no' and str(kk) != 'case_number'  and str(kk) != 'uuid':
                        recordkeys.append(kk)
                    record.update({kk : str(value).capitalize()})
            return record


        for rec in stat:
            if isinstance(rec, dict) and len(rec) > 1:
                statrecords.append(get_records(rec))

        if len(recordkeys) > 0:
            recordkeys.append('Date Created')
        else:
            recordkeys = False


        data['statrecords'] = statrecords
        data['recordkeys'] = recordkeys

    
    # if report == 'nonanalysed':
    #     data['report_data'] = filter(lambda _call_data: not _call_data['length'] and _call_data['length'] <= 1, call_data)
    #     htmltemplate = "helpline/nonanalysed.html"
    # elif report == 'voicemails':
    #     data['report_data'] = filter(lambda _call_data: _call_data['voicemail'], call_data)
    # elif htmltemplate == '':
    #     htmltemplate = "helpline/report_body.html"

    return render(request, htmltemplate, data)

def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]

@login_required
def reports(request, report, casetype='Call'):
    query = request.GET.get('q', '')
    datetime_range = request.GET.get("datetime_range") or ''
    agent = request.GET.get("agent") or ''
    category = request.GET.get("category", "")
    form = ReportFilterForm(request.GET)
    dashboard_stats = get_dashboard_stats(request.user)
    report_title = {report: _(str(report).capitalize() + " Reports")}

    request_string = ''
    query_string = ''

    home_statistics = get_dashboard_stats(request)

    data = {
            'title': report_title.get(report),
            'report': report,
            'form': form,
            'datetime_range': datetime_range,
            'home': home_statistics,
            'query': query
        }
    case_start = '';
    case_end = ''
    if not datetime_range == '':
        start_dates, end_dates = [datetime_range.split(" - ")[0], datetime_range.split(" - ")[1]]
        
        start_date = datetime.strptime(start_dates, '%m/%d/%Y  %I:%M %p')
        end_date = datetime.strptime(end_dates, '%m/%d/%Y  %I:%M %p')

        d1 = start_date.strftime('%Y-%m-%d %H:%M')
        d2 = end_date.strftime('%Y-%m-%d %H:%M')
        
        datetime_range = '%sto%s' %(d1,d2)

        case_start = start_date.strftime('%Y-%m-%d')
        case_end = end_date.strftime('%Y-%m-%d')

    else:
        nowdate = datetime.now()

        start_date = nowdate.strftime('%Y-%m-%d  00:00')
        end_date = nowdate.strftime('%Y-%m-%d  23:59')

        datetime_range = '%sto%s' %(start_date,end_date)

        case_start = nowdate.strftime('%Y-%m-%d')
        case_end = nowdate.strftime('%Y-%m-%d')

    

    if str(casetype).lower() == 'call':
        """For call reports"""
        callreports = ["missedcalls", "totalcalls",
                       "answeredcalls", "abandonedcalls", "callsummaryreport",
                       "search", "agentsessionreport"]


        if agent != '' or request.user.HelplineUser.hl_role == 'Counsellor':
            if agent == '':
                agent = request.user
            else:
                agent = User.objects.get(pk__exact=agent)
            agent = agent.HelplineUser.hl_key
            
            if request_string == '':
                request_string = '?usr_f=%s' % agent
            else:
                request_string = '%s&usr_f=%s' % (datetime_range,agent)


        calls_url = "%s/clk/cdr?chan_ts_f=%s" %(settings.CALL_API_URL, \
            request_string)
        call_data = requests.post(calls_url).json() 
        
        if report in callreports:
            htmltemplate = "helpline/reports.html"
        elif report == 'voicemails': 
            call_data = filter(lambda call_data: call_data['voicemail'] == 'true' and call_data['recording'] != '', call_data)
            htmltemplate = "helpline/voicemails.html"

        agents = User.objects.filter().only("username", "HelplineUser__hl_key").exclude(HelplineUser=None).select_related('HelplineUser')
        
        agent_list = {}
        agents = map(lambda x: agent_list.update({'%s'%x.HelplineUser.hl_key:str(x.username)}), agents)

        data['agents'] = agent_list
        data['report_data'] = call_data
        data['urls'] = calls_url
    else:
        """Report processing and rendering"""
        default_service = Service.objects.all().first()
        default_service_xform = default_service.walkin_xform
        default_service_auth_token = default_service_xform.user.auth_token
        current_site = get_current_site(request)

        data['owner'] = default_service_xform.user
        data['xform'] = default_service_xform

        # Graph data
        headers = {
            'Authorization': 'Token %s' % (default_service_auth_token)
        }

        id_string = str(default_service_xform)
        username = request.user.username

        owner = get_object_or_404(User, username__iexact=username)
        xform = get_form({'id_string__iexact': str(default_service.walkin_xform)})
        
        if report == 'escalated' or report == 'pending' or report == 'closed':
            rep_status = 'escalate' if report == 'escalated' else report
            if request.user.HelplineUser.hl_role == 'Counsellor':
                query_string = '"case_actions/case_action":{"$i":"%s"}' % rep_status
            elif request.user.HelplineUser.hl_role == 'Caseworker':
                query_string = '"case_actions/case_action":"%s",\
                "case_actions/escalate_caseworker":"%s"' %(rep_status,str(username))
            elif request.user.HelplineUser.hl_role == 'Supervisor':
                query_string = '"case_actions/case_action":"%s",\
                "case_actions/supervisors":"%s"' %(rep_status,str(username))
            else:
                query_string = '"case_actions/case_action":"%s"'  % rep_status

        elif report == 'highpriority':
            query_string = '"case_narratives/case_priority":"high_priority"'
        elif report == 'today' or report == 'totalcases':
            td_date = datetime.today()
            request_string += '&date_created__day=' + td_date.strftime('%d')
            request_string += '&date_created__month=' + td_date.strftime('%m')
            request_string += '&date_created__year=' + td_date.strftime('%Y')

        htmltemplate = ''

        if report == 'disposition':
            dispositions = Cases.objects.all()
            dispx = Cases.objects.all().values('case_source').annotate(case_count=Count('case_number'))
            print("The dispositions: %s " % dispx)
            data['report_data'] = dispositions

            chart = LineChart(MyModelDataSource(queryset=dispositions, fields=['case_source','case_number']))
            data['chart'] = chart
            htmltemplate = 'helpline/dispositions.html'
        elif casetype.lower() == 'qa':
            call_data = requests.post("%s/clk/cdr/?qa=true" %(settings.CALL_API_URL)).json()
        else:
            """For case reports"""

            if request.user.HelplineUser.hl_role == 'Counsellor' and report != 'totalcases':
                if query_string == '':
                    query_string = '"case_owner":{"$i":"%s"}' %(username)
                else:
                    query_string += ',"case_owner":{"$i":"%s"}' %(username)

            ur = 'http://%s/ona/api/v1/data/%s?query={%s}%s' %(current_site, \
                default_service_xform.pk, query_string, request_string)

            print("Reprt: %s, ur: %s" %(report,ur))
        
            stat = requests.get(ur, headers=headers).json()

            data['ur'] = ur
            statrecords = []
            recordkeys = []

            ##brings up data only for existing records
            def get_records(recs):
                return_obj = []
                record = {}

                for key, value in recs.items():
                    key = str(key)
                    if key.find('/') != -1:
                        k = key.split('/')
                        l = len(k)
                        kk = str(k[l-1])
                    else:
                        kk = str(key)
                    if isinstance(value, dict) and len(value) >= 1:
                        record.update(get_records(value))
                    elif isinstance(value, list) and len(value) >= 1:
                        if isinstance(value[0], dict):
                            record.update(get_records(value[0]))
                    else:
                        if not kk in recordkeys and not kk.endswith('ID') and str(value) != 'yes' and \
                        str(value) != 'no' and str(kk) != 'case_number'  and str(kk) != 'uuid':
                            recordkeys.append(kk)
                        record.update({kk : str(value).capitalize()})

                    # format submission date to allow later filter by date
                    if record.get('_submission_time',None) != None:
                        cr_time = record['_submission_time']
                        cr_time = str(cr_time)

                        if 't' in cr_time:
                            cr_time = datetime.strptime(cr_time, '%Y-%m-%dt%H:%M:%S')
                            cr_time = cr_time.strftime('%Y-%m-%d')
                        record['_submission_time'] = cr_time

                return record

            
            for rec in stat:
                if isinstance(rec, dict) and len(rec) > 1:
                    statrecords.append(get_records(rec))

            if len(recordkeys) > 0:
                recordkeys.append('Date Created')
            else:
                recordkeys = False

            # filter by date submitted
            if not case_start == '':
                statrecords = filter(lambda statrecords: statrecords['_submission_time'] >= case_start and statrecords['_submission_time'] <= case_end, statrecords)

            data['statrecords'] = statrecords
            data['recordkeys'] = recordkeys

    
        if report == 'nonanalysed':
            data['report_data'] = filter(lambda call_data: not call_data['length'] and call_data['length'] <= 1, call_data)
            htmltemplate = "helpline/nonanalysed.html"
        elif report == 'voicemails':
            data['report_data'] = filter(lambda call_data: call_data['voicemail'], call_data)
        elif htmltemplate == '':
            htmltemplate = "helpline/report_body.html"
            # data['report_data'] = filter(lambda call_data: not call_data['voicemail'], call_data)

    return render(request, htmltemplate, data)


@login_required
def qa(request, report='analysed'):

    default_service = Service.objects.all().first()
    xform = default_service.qa_xform
    username = xform.user.username
    default_service_auth_token = xform.user.auth_token
    current_site = get_current_site(request)

    # service = Service.objects.all().first()
    # xform = service._xform
    # username = xform.user.username
    # default_service_auth_token = xform.user.auth_token
    # current_site = get_current_site(request)


    
    form = ReportFilterForm(request.POST)

    data = {
        'form': form}

    form_url = get_form_url(request, username, settings.ENKETO_PROTOCOL)

    try:
        url = enketo_url(form_url, xform.id_string)
        uri = request.build_absolute_uri()

        # Use https for the iframe parent window uri, always.
        # uri = uri.replace('http://', 'https://')
        # Poor mans iframe url gen
        parent_window_origin = urllib.quote_plus(uri)
        iframe_url = url[:url.find("::")] + "i/" + url[url.find("::"):]+\
          "?&parentWindowOrigin=" + parent_window_origin
        data['iframe_url'] = iframe_url
    except Exception as e:
        data['iframe_url'] = "URL Error: %s" % e

    # Set Query Parameters
    query_string = ''
    if request.method == 'POST':
        category = request.POST.get('contact_id', None)
        datetime_range = request.POST.get('datetime_range', None)
        if datetime_range == '':
            start_date, end_date = [datetime_range.split(" - ")[0], datetime_range.split(" - ")[1]]
            start_date = datetime.strptime(start_date, '%m/%d/%Y %I:%M %p')
            end_date = datetime.strptime(end_date, '%m/%d/%Y %I:%M %p')

    if report == 'results':
        headers = {
            'Authorization': 'Token %s' % (default_service_auth_token)
        }
        url = 'http://%s/ona/api/v1/data/%s?page=1&page_size=50' % (
            current_site,
            xform.pk
        )
        result_data = requests.get(url,headers=headers).json() 

        # process data for preview
        statrecords = []
        recordkeys = []

        ##brings up data only for existing records
        def get_records(recs):
            return_obj = []
            record = {}

            for key, value in recs.items():
                #if not (key.startswith('_') and key.endswith('_')):# str(key) == "_id":
                key = str(key)
                if key.find('/') != -1:
                    k = key.split('/')
                    l = len(k)
                    kk = str(k[l-1])
                else:
                    kk = str(key)
                if isinstance(value, dict) and len(value) >= 1:
                    record.update(get_records(value))
                elif isinstance(value, list) and len(value) >= 1:
                    if isinstance(value[0], dict):
                        record.update(get_records(value[0]))
                else:
                    if not kk in recordkeys and not kk.endswith('ID') and not kk.endswith('ID') and str(value) != 'yes' and \
                    str(value) != 'no' and str(kk) != 'case_number' and 'uuid' not in str(kk):
                        recordkeys.append(kk)
                    record.update({kk : str(value).capitalize()})
            return record


        for rec in result_data:
            if isinstance(rec, dict) and len(rec) > 1:
                statrecords.append(get_records(rec))

        if len(recordkeys) > 0:
            recordkeys.append('Date Created')
        else:
            recordkeys = False


        data['report_data'] = statrecords
        data['recordkeys'] = recordkeys

        htmltemplate = 'helpline/qaresults.html'
    else:
        # Call CDR Data
        result_data = requests.post("%s/clk/cdr/" %(settings.CALL_API_URL) + query_string).json()
        data['report_data'] = result_data
        htmltemplate = "helpline/nonanalysed.html"

    
    data['report'] = report
    # data['users'] = HelplineUser.objects.all()
    
    return render(request, htmltemplate, data)
@login_required
def analysed_qa(request, report='analysed'):
    """
    Process QA result reports for the current service case form
    """
    default_service = Service.objects.all().first()
    default_service_xform = default_service.qa_xform
    default_service_auth_token = default_service_xform.user.auth_token
    current_site = get_current_site(request)


    url = 'http://%s/ona/api/v1/data/%s' % (
        current_site,
        default_service_xform.pk
    )

    # Graph data
    headers = {
        'Authorization': 'Token %s' % (default_service_auth_token)
    }

    id_string = str(default_service_xform)
    username = request.user.username

    owner = get_object_or_404(User, username__iexact=username)
    xform = get_form({'id_string__iexact': str(id_string)})


    request_string = ''

    # if datetime_range == '':
    #    start_date, end_date = [datetime_range.split(" - ")[0], datetime_range.split(" - ")[1]]
    #    start_date = datetime.strptime(start_date, '%m/%d/%Y %I:%M %p')
    #    end_date = datetime.strptime(end_date, '%m/%d/%Y %I:%M %p')

    td_date = datetime.today()
    request_string = '&date_created__day=' + td_date.strftime('%d')
    request_string += '&date_created__month=' + td_date.strftime('%m')
    request_string += '&date_created__year=' + td_date.strftime('%Y')

    xforms = requests.get('http://%s/ona/api/v1/forms' % (current_site), headers=headers).json();
    xformx = {}

    #split to get xform object, this will allow us to obtain xform fields
    for xfrm in xforms:
        if str(xfrm['id_string']) == id_string:
            for key, frm in xfrm.items():
                xformx.update({str(key):str(frm)})

    if request.user.HelplineUser.hl_role == 'Counsellor':
        request_string += '&case_owner=%s' %(request.user.username)


    stat = requests.get('http://%s/ona/api/v1/data/%s?page=1&page_size=50%s' %(current_site, default_service_xform.pk,\
        request_string), headers=headers).json();
    # + '&sort={"_id":-1}'
    statrecords = []
    recordkeys = []

    ##brings up data only for existing records
    def get_records(recs):
        return_obj = []
        record = {}

        for key, value in recs.items():
            #if not (key.startswith('_') and key.endswith('_')):# str(key) == "_id":
            key = str(key)
            if key.find('/') != -1:
                k = key.split('/')
                l = len(k)
                kk = str(k[l-1])
            else:
                kk = str(key)
            if isinstance(value, dict) and len(value) >= 1:
                record.update(get_records(value))
            elif isinstance(value, list) and len(value) >= 1:
                if isinstance(value[0], dict):
                    record.update(get_records(value[0]))
            else:
                if not kk in recordkeys and not kk.endswith('ID') and str(value) != 'yes' and str(value) != 'no'\
                 and str(kk) != 'case_number'  and str(kk) != 'uuid':
                    recordkeys.append(kk)
                record.update({kk : str(value).capitalize()})
        return record


    for rec in stat:
        if isinstance(rec, dict) and len(rec) > 1:
            statrecords.append(get_records(rec))

    if len(recordkeys) > 0:
        recordkeys.append('Date Created')
    else:
        recordkeys = False

    return render(request, 'helpline/analysed_qa.html', {
        'title': 'Analysed QA Results',
        'report': report,
        'xform':id_string,
        'form': 'Qa Form',
        'dashboard_stats': '',
        'statrecords': statrecords,
        'recordkeys': recordkeys
        })


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


@login_required
def report_charts(request, report, casetype='Call'):
    """Return charts for the last 4 days based on the Call Summary Data"""
    # The ussual filters.
    query = request.GET.get('q', '')
    interval = request.GET.get('interval', 'daily')
    category = request.GET.get('category', '')
    if report == 'categorysummary':
        y_axis = 'category'
    elif report == 'dailysummary':
        y_axis = 'daily'
    else:
        y_axis = request.GET.get('y_axis', '')

    datetime_range = request.GET.get("datetime_range")
    agent = request.GET.get("agent")
    form = ReportFilterForm(request.GET)
    # Update the search url to chart based views.
    search_url = reverse('report_charts', kwargs={'report': report})

    # Convert date range string to datetime object
    if datetime_range:
        try:
            a, b = [datetime_range.split(" - ")[0], datetime_range.split(" - ")[1]]
            from_date = datetime.strptime(a, '%m/%d/%Y %I:%M %p')
            to_date = datetime.strptime(b, '%m/%d/%Y %I:%M %p')

            current = from_date

            delta = to_date - from_date
            date_list = []
            if interval == 'hourly':
                for i in range(int(delta.total_seconds()//3600)):
                    date_list.append(from_date + timedelta(seconds=i*3600))
            elif interval == 'monthly':
                while current <= to_date:
                    current += relativedelta(months=1)
                    date_list.append(current)
            elif interval == 'weekly':
                while current <= to_date:
                    current += relativedelta(weeks=1)
                    date_list.append(current)
            else:
                while current <= to_date:
                    current += relativedelta(days=1)
                    date_list.append(current)

            epoch_list = [date_item.strftime('%m/%d/%Y %I:%M %p')
                          for date_item in date_list]

            # Add filter to ajax query string.
        except Exception as e:
            from_date = None
            to_date = None
    else:
        from_date = None
        to_date = None

        # Start date
        base = datetime.today()
        date_list = [base - timedelta(days=x) for x in range(0, 3)]
        epoch_list = [date_item.strftime('%m/%d/%Y %I:%M %p')
                      for date_item in date_list]
        epoch_list.reverse()
    e = None

    datetime_ranges = pairwise(epoch_list)
    callsummary_data = []
    total_calls = 0
    for datetime_range in datetime_ranges:
        # Date time list returns desending. We want assending.
        datetime_range_string = " - ".join(datetime_range)
        if y_axis == 'category':
            categories = [i[0] for i in Category.objects.values_list('hl_category').distinct()]
            for category in categories:
                report_data = report_factory(report='chartreport',
                                             datetime_range=datetime_range_string,
                                             agent=agent,
                                             query=query,
                                             category=category,
                                             casetype=casetype)

                # Append data to tables list.
                callsummary_data.append(report_data)
                total_calls = total_calls + report_data.get('total_offered').get('count')
        else:
            report_data = report_factory(report='chartreport',
                                         datetime_range=datetime_range_string,
                                         agent=agent,
                                         query=query,
                                         category=category,
                                         casetype=casetype)

            # Append data to tables list.
            callsummary_data.append(report_data)
            total_calls = total_calls + report_data.get('total_offered').get('count')

    # Multibar chart page.
    if y_axis != 'daily':
        summary_table = CallSummaryTable(callsummary_data)
    tooltip_date = "%d %b %Y %H:%M:%S %p"
    extra_serie = {"tooltip": {"y_start": "There are ", "y_end": " calls"},
                   "date_format": tooltip_date}

    if y_axis == 'category':
        categories = [i[0] for i in Category.objects.values_list('hl_category').distinct()]

        chartdata = {
            'x': epoch_list,
        }
        for i in range(len(categories)):
            chartdata['name%s' % str(i+1)] = categories[i]
            category_related = []
            for data in callsummary_data:
                if data.get('category') == categories[i]:
                    category_related.append(data)
            chartdata['y%s' % str(i+1)] = [d.get('total_offered').get('count')
                                           for d in category_related]
            chartdata['extra%s' % str(i+1)] = extra_serie
    elif y_axis == 'daily':
        daysummary_data = []
        month_names = []
        day_names = list(calendar.day_name)
        chartdata = {}
        day_related = {}
        for day_name in day_names:
            day_related[day_name] = []

        for i in range(len(day_names)):
            day_summary = {}
            chartdata['name%s' % str(i+1)] = day_names[i]
            day_total_offered = 0
            month_name = 'None'
            for data in callsummary_data:
                if data.get('day') == day_names[i]:
                    day_related[day_names[i]].append(data)
                    day_total_offered = day_total_offered + data.get('total_offered').get('count')
                    day_related[day_names[i]][-1]['day_total_offered'] = day_total_offered
                    month_name = data.get('month')

            day_summary['month'] = month_name
            month_names.append(month_name)
            day_summary['%s' % (day_names[i].lower())] = day_total_offered
            chartdata['y%s' % str(i+1)] = [d.get('day_total_offered')
                                           for d in day_related[day_names[i]]]
            chartdata['extra%s' % str(i+1)] = extra_serie
            chartdata['x'] = month_names
            daysummary_data.append(day_summary)
    else:

        ydata = [d.get('total_offered').get('count') for d in callsummary_data]
        ydata2 = [d.get('total_answered') for d in callsummary_data]
        ydata3 = [d.get('total_abandoned') for d in callsummary_data]

        chartdata = {
            'x': epoch_list,
            'name1': 'Total Offered', 'y1': ydata, 'extra1': extra_serie,
            'name2': 'Total Answered', 'y2': ydata2, 'extra2': extra_serie,
            'name3': 'Total Abandoned', 'y3': ydata3, 'extra3': extra_serie,
        }

    charttype = "multiBarChart"
    chartcontainer = 'multibarchart_container'  # container name
    if y_axis == 'daily':
        summary_table = DaySummaryTable(daysummary_data)

    export_format = request.GET.get('_export', None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, summary_table)
        return exporter.response('table.{}'.format(export_format))

    data = {
        'title': 'callsummary',
        'form': form,
        'summary_table': summary_table,
        'datetime_ranges_number': len(datetime_ranges),
        'error': e,
        'y_axis': y_axis,
        'search_url': search_url,
        'total_calls': total_calls,
        'charttype': charttype,
        'casetype': casetype,
        'chartdata': chartdata,
        'chartcontainer': chartcontainer,
        'extra': {
            'name': 'Call data',
            'x_is_date': False,
            'x_axis_format': '',
            'tag_script_js': True,
            'jquery_on_ready': True,
        },
    }

    if report == 'ajax':
        return render(request, 'helpline/report_charts_factory.html', data)
    else:
        return render(request, 'helpline/report_charts.html', data)


def autolocation(request):
    """Get districts"""
    districts = request.GET['districts']
    return render(request, 'helpline/locations.html', {
        'districts': districts})


def queue_manager(user, extension, action):
    """queuejoin:queueleave:queuepause:queueunpause:queuetrain"""
    data = {}
    # if action == 'queuejoin':
    #     data = backend.add_to_queue(
    #         agent="SIP/%s" % (extension),
    #         queue='Q718874580',
    #         member_name=user.get_full_name()
    #     )
    # elif action == 'queueleave':
    #     data = backend.remove_from_queue(
    #         agent="SIP/%s" % (extension),
    #         queue='Q718874580',
    #     )
    return data

def home_direct():
    return Redirect('/helpline/')

@login_required
def contact_search(request, search_string=None):
    service = Service.objects.all().first()
    default_service_xform = service.walkin_xform
    default_service_auth_token = default_service_xform.user.auth_token
    current_site = get_current_site(request)

    headers = {
        'Authorization': 'Token %s' % (default_service_auth_token)
    }
    call_data = requests.get("%s" %(request.GET.get('url')),headers=headers).json()

    return JsonResponse(call_data,safe=False)
@login_required
def case_form(request, form_name):
    """Handle Walkin and CallForm POST and GET Requests"""


    service = Service.objects.all().first()

    if hasattr(service,'walkin_xform') and service.walkin_xform:
        default_service_xform = service.walkin_xform
    else:
        response = redirect('/ona/%s' % request.user.username)
        return response

    #default_service_xform = service.walkin_xform
    default_service_auth_token = default_service_xform.user.auth_token
    current_site = get_current_site(request)
    """
    Graph data
    """
    headers = { 
        'Authorization': 'Token %s' %(default_service_auth_token)
    }

    #charts
    url = 'http://%s/ona/api/v1/data/%s' %(current_site, default_service_xform.pk)

    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    uid_list = []

    # Build a list of user ids from that query
    for session in sessions:
        data = session.get_decoded()
        uid_list.append(data.get('_auth_user_id', None))

    trans_users = []
    # Query all logged in users based on id list
    users = User.objects.filter(HelplineUser__hl_status__exact='Available').exclude(username__exact=request.user.username)
    for trans_user in users:
        if HelplineUser.objects.filter(user=trans_user):
                    trans_users.append({'text':str(trans_user.username),'value':str(trans_user.HelplineUser.hl_key)})

    message = ''
    initial = {}
    data = {}
    caseid = ''

    data['users'] = trans_users
    data['enketo_url'] = settings.ENKETO_URL
    data['base_domain'] = settings.BASE_DOMAIN
    data['data_url'] = url
    data['data_token'] = default_service_auth_token

    if form_name == 'walkin':
        xform = service.walkin_xform
        data['form_name'] = 'walkin'
    elif form_name == 'call':
        xform = service.call_xform
        data['form_name'] = 'call'
        data['caller'] = request.GET.get('phone')
        data['cdr'] = request.GET.get('callcase')
        data['api_url'] = settings.CALL_API_URL + '/api/v1'
    elif form_name == 'qa':
        xform = service.qa_xform
        data['form_name'] = 'qa'
        sourceid = request.GET.get('sourceid')
        data['sourceid'] = sourceid
    elif form_name == 'webonline':
        xform = service.web_online_xform
        data['form_name'] = 'webonline'
    else:
        xform = service.walkin_xform
        data['form_name'] = form_name
        caseid = get_case_number(form_name)
        sourceid = request.GET.get('sourceid')

        if form_name == 'email':
            email = get_object_or_404(Emails, pk__exact=sourceid, email_case__gt=0);
            email.email_case = caseid
            caseid_str = '&d[/Case_Form/reporter_details/email_adress]=%s' % (email.email_from) + \
            '&d[/Case_Form/case_narratives/case_narrative]=%s' %(email.email_body)
            email.save()

        if form_name == 'sms':
            sms = SMSCDR(pk=sourceid) # get_object_or_404(SMSCDR, pk__exact=sourceid, sms_case__gt=0);
            sms.sms_case = caseid
            caseid_str = '&d[/Case_Form/reporter_details/reporter_phone]=%s' % (sms.contact) + \
            '&d[/Case_Form/case_narratives/case_narrative]=%s' %(sms.msg)
            sms.save()

    # If no XForm is associated with the above cases
    if not xform:
            data['message'] = {
                'type': 'alert-error',
                'text': _(u"No form found for the service %s" % (service.name))
            }
            return render(
                request, "helpline/case_form.html", data
            )

    if request.method == 'GET':
        case_number = request.GET.get('case')
        username = xform.user.username
        data['disposition_form'] = DispositionForm()
        data['contact_form'] = ContactForm()
        data['contact_search_form'] = ContactSearchForm()


        form_url = get_form_url(request, username, settings.ENKETO_PROTOCOL)

        try:
            url = enketo_url(form_url, xform.id_string)
            uri = request.build_absolute_uri()

            # Use https for the iframe parent window uri, always.
            # uri = uri.replace('http://', 'https://')

            caseid_str = '&d[case_owner]=%s' % (request.user.username)

            caseid_str = caseid_str + '&d[case_number]=%s'% (caseid) if caseid else ''
            # Poor mans iframe url gen
            parent_window_origin = urllib.quote_plus(uri)
            iframe_url = url[:url.find("::")] + "i/" + url[url.find("::"):]+\
              "?&parentWindowOrigin=" + parent_window_origin + caseid_str
            data['iframe_url'] = iframe_url
            data['xform_id_string'] = xform.id_string

            if not url:
                return HttpResponseRedirect(
                    reverse(
                        'form-show',
                        kwargs={'username': username,
                                'id_string': xform.id_string}))
            # return HttpResponseRedirect(iframe_url)
        except EnketoError as e:
            data = {}
            owner = User.objects.get(username__iexact=username)
            data['profile'], __ = UserProfile.objects.get_or_create(user=owner)
            data['xform'] = xform
            data['content_user'] = owner
            data['form_view'] = True
            data['message'] = {
                'type': 'alert-error',
                'text': u"Enketo error, reason: %s" % e
            }
            messages.add_message(
                request,
                messages.WARNING,
                _("Enketo error: enketo replied %s") % e,
                fail_silently=True)


        return render(request, "helpline/case_form.html", data)

    elif request.method == 'POST':
        contact, address = (None, None)
        # Process forms differently.

        if form_name == 'call':
            contact_form = ContactForm(request.POST)
        elif form_name == 'walkin':
            contact_form = ContactForm(request.POST)

        if form.is_valid():
            case_number = form.cleaned_data.get('case_number')
            if case_number:
                my_case = Case.objects.get(hl_case=case_number)
                report, contact, address = get_case_info(case_number)
                case_history = Report.objects.filter(
                    telephone=contact.hl_contact).order_by('-case')
                case_history_table = CaseHistoryTable(case_history)

                # Initial case data
                data['case'] = my_case
                data['report'] = report
                data['contact'] = contact
                data['address'] = address
                data['case_history_table'] = case_history_table

                try:
                    case_history_table.paginate(page=request.GET.get('page', 1), per_page=10)
                except Exception as e:
                    # Do not paginate if there is an error
                    pass

            # If no case number is given we create a new case
            else:
                my_case = Case()
                my_case.hl_data = form_name
                my_case.user = request.user
                my_case.popup = 'Done'
                my_case.hl_time = int(time.time())
                my_case.hl_status = form.cleaned_data.get('case_status')
                my_case.hl_acategory = form.cleaned_data.get('category')
                my_case.hl_notes = form.cleaned_data.get('notes')
                my_case.hl_type = form.cleaned_data.get('case_type')

                my_case.priority = 'Non-Critical'
                my_case.hl_creator = request.user.HelplineUser.hl_key
                my_case.save()

                report, contact, address = get_case_info(case_number)

                now = timezone.now()
                callstart = "%s:%s:%s" % (now.hour, now.minute, now.second)
                notime = "00:00:00"
                report = Report(case_id=my_case.hl_case,
                                callstart=callstart,
                                callend=callstart,
                                talktime=notime,
                                holdtime=notime,
                                walkintime=callstart,
                                hl_time=int(time.time()),
                                calldate=time.strftime('%d-%b-%y'))
                case_number = my_case.hl_case
                case_history = Report.objects.filter(telephone=contact.hl_contact).order_by('-case_id')
                case_history_table = CaseHistoryTable(case_history)
                try:
                    case_history_table.paginate(
                        page=request.GET.get('page', 1), per_page=10)
                except Exception as e:
                    # Bad idea.
                    # Ignore pagination errors when a new contact with no case history is input.
                    pass

            address.hl_names = form.cleaned_data.get('caller_name')
            report.counsellorname = request.user.username
            report.user = request.user
            report.casetype = form_name

            my_case.save()
            address.save()
            contact.save()
            report.save()
            message = 'Success'
            disposition_form = DispositionForm(
                initial={'case_number': case_number})
        else:
            case_number = form.cleaned_data.get('case_number')
            disposition_form = DispositionForm()

            if case_number:
                report, contact, address = get_case_info(case_number)
                case_history = Report.objects.filter(
                    telephone=contact.hl_contact).order_by('-case_id')
                case_history_table = CaseHistoryTable(case_history)
            else:
                report, contact, address = (None, None, None)
                case_history = Report.objects.all().order_by('-case_id')
                case_history_table = CaseHistoryTable(case_history)

    request.user.HelplineUser.hl_case = 0
    request.user.HelplineUser.save()

    return render(
        request, 'helpline/case_form.html', {
            'contact': contact if contact else None,
            'initial': initial,
            'disposition_form': disposition_form,
            'case_history_table': case_history_table,
            'form_name': form_name,
            'message': message,
            'contact_form': contact_form
        }
    )

def case_edit(request, form_name, case_id):
    default_service = Service.objects.all().first()
    default_service_xform = default_service.walkin_xform
    default_service_auth_token = default_service_xform.user.auth_token
    current_site = get_current_site(request)

    """
    Graph data
    """
    headers = {
        'Authorization': 'Token %s' %(default_service_auth_token)
    }

    url = 'http://%s/ona/api/v1/data/%s/%s/enketo?return_url=http://%s/helpline/success/&format=json' \
    % (current_site, default_service_xform.pk, case_id, current_site)
    req = requests.get(url, headers=headers).json()
    return render(request,'helpline/case_form_edit.html', {'case':case_id, 'iframe_url':get_item(req, 'url')})

class DashboardTable(tables.Table):
    """Where most of the dashboard reporting happens"""
    casetype = tables.TemplateColumn("<b>{{ record.get_call_type }}</b>",
                                     verbose_name="Call Type")
    case_id = tables.TemplateColumn(
        '{% if record.case %}<a href="{{ record.get_absolute_url }}">{{record.case }}</a>{% else %}-{% endif %}')
    callernames = tables.TemplateColumn("{{ record.case.contact.address.hl_names }}")
    telephone = tables.TemplateColumn(
        '<a href="sip:{{record.telephone}}">{{record.telephone}}</a>')
    user_id = tables.TemplateColumn("{{ record.user }}", verbose_name="Agent")
    service_id = tables.TemplateColumn("{{ record.service }}",
                                       verbose_name="Service")
    qaaction = tables.TemplateColumn('<a href="{{ record.get_qa_url }}"><i class="fa fa-volume-up"></i> Analyse</a>', verbose_name="Action")

    export_formats = ['csv', 'xls']

    class Meta:
        model = Report
        attrs = {'class': 'table table-bordered table-striped dataTable',
                 'id': 'report_table example1'}
        unlocalise = ('holdtime', 'walkintime', 'talktime', 'callstart')
        fields = {'casetype', 'case_id', 'telephone', 'calldate',
                  'service_id', 'callernames', 'user_id', 'escalatename',
                  'calldate', 'callstart', 'callend', 'talktime', 'holdtime',
                  'calltype', 'disposition', 'casestatus'}

        sequence = ('casetype', 'case_id', 'calldate', 'callstart',
                    'callend', 'user_id', 'telephone', 'escalatename',
                    'service_id', 'talktime', 'holdtime', 'calltype',
                    'disposition', 'casestatus')


class WebPresenceTable(tables.Table):
    """Web presence table"""
    class Meta:
        model = HelplineUser
        attrs = {'class': 'table table-bordered table-striped dataTable'}

class ContactTable(tables.Table):
    """Contact list table"""
    address = tables.Column(verbose_name='Name')
    hl_contact = tables.Column(verbose_name='Phone')
    action = tables.TemplateColumn('<a onClick="createCase({{ record.id }});"><i class="fa fa-plus">\
        </i>Create Case</a>', verbose_name="Action")
    class Meta:
        model = Contact
        fields = {'address', 'hl_contact'}
        attrs = {'class': 'table table-bordered table-striped dataTable'}


class CaseHistoryTable(tables.Table):
    """Show related Case form contact"""
    case = tables.TemplateColumn('{% if record.case %}<a href="{{ record.get_absolute_url }}">{{record.case }}</a>\
        {% else %}-{% endif %}')
    class Meta:
        model = Report
        attrs = {'class': 'table table-bordered table-striped dataTable'}
        fields = {'case', 'user', 'calldate', 'calltype'}
        sequence = ('case', 'user', 'calldate', 'calltype')

        unlocalise = ('holdtime', 'walkintime', 'talktime', 'callstart')


class TimeSinceColumn(tables.Column):
    """Return time since formated as "00:00:00" """
    def render(self, value):
        time_since = float(time.time()) - float(value)
        idle_time = str(timedelta(seconds=time_since)) if value else "NA"
        return idle_time


class ConnectedAgentsTable(tables.Table):
    """Show connection information for agents"""
    login_duration = tables.TemplateColumn('''{% with login_duration=record.get_login_duration %}
                                            {{ login_duration.hours }}:{{ login_duration.min }}:{{ login_duration.seconds }}
                                            {% endwith %}''', orderable=False)
    hl_time = TimeSinceColumn(verbose_name='Idle Time')
    att = tables.TemplateColumn('''{% with att=record.get_average_talk_time %}
                                {{ att.hours }}:{{ att.min }}:{{ att.seconds }}
                                {% endwith %}
                               ''', orderable=False, verbose_name='Avg. Talk Time')

    aht = tables.TemplateColumn('''{% with aht=record.get_average_wait_time %}
                                {{ aht.hours }}:{{ aht.min }}:{{ aht.seconds }}
                                {% endwith %}
                               ''', orderable=False, verbose_name='Avg. Hold Time')
    ready = tables.TemplateColumn('''{% with rd=record.get_ready_duration %}
                                {{ rd.hours }}:{{ rd.min }}:{{ rd.seconds }}
                                {% endwith %}
                               ''', orderable=False, verbose_name='Ready')
    action = tables.TemplateColumn('''
                                   {% ifequal record.hl_status 'Available' %}
                                   <a href="{% url 'queue_remove' record.hl_auth %}">Remove from Queue</a>
                                   {% endifequal %}
                               ''', orderable=False, verbose_name='Action')
    class Meta:
        model = HelplineUser
        attrs = {'class' : 'table table-bordered table-striped', 'id':'report_table'}
        fields = {'hl_auth', 'hl_exten', 'hl_calls', 'hl_status', 'hl_names', 'hl_time'}
        sequence = ('hl_auth', 'hl_names', 'hl_calls', 'hl_exten', 'hl_time', 'hl_status')


class ReceievedColumn(tables.Column):
    """Return ctime from an epoch time stamp"""
    def render(self, value):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value))


class ServiceColumn(tables.Column):
    """Show service, customized template"""
    def render(self, value):
        return Service.objects.get(hl_key=value).hl_service


class AgentSessionTable(tables.Table):
    """Show agent activity"""
    hl_time = ReceievedColumn()

    class Meta:
        model = Clock
        unlocalize = ('hl_time')
        attrs = {'class': 'table table-bordered table-striped dataTable',
                 'id': 'report_table'}


class CallSummaryTable(tables.Table):
    """Main call summary table"""
    service = tables.Column(orderable=False)
    category = tables.Column(orderable=False, verbose_name=_('Category'))
    total_calls = tables.TemplateColumn(
        "<a href='{% url 'dashboardreports' 'totalcalls' record.total_offered.casetype %}?{{ record.total_offered.filter_query }}'>{{ record.total_offered.count }}</a>",
        orderable=False)
    total_answered = tables.TemplateColumn("<a href='{% url 'dashboardreports' 'answeredcalls' %}?{{ record.total_offered.filter_query }}'>{{ record.total_answered }}</a>",
                                           orderable=False)
    total_abandoned = tables.TemplateColumn("<a href='{% url 'dashboardreports' 'abandonedcalls' %}?{{ record.total_offered.filter_query }}'>{{ record.total_abandoned }}</a>",
                                            orderable=False)
    total_talktime = tables.Column(orderable=False)
    att = tables.Column(orderable=False, verbose_name=_('Average Talk Time'))
    aht = tables.Column(orderable=False, verbose_name=_('Average Hold Time'))
    answered_percentage = tables.Column(orderable=False,
                                        verbose_name=_('Answered Percentage'))
    abandoned_percentage = tables.Column(
        orderable=False,
        verbose_name=_('Abandoned Percentage'))
    export_formats = ['csv', 'xls']

    class Meta:
        attrs = {'class': 'table table-bordered table-striped dataTable',
                 'id': 'report_table'}


class DaySummaryTable(tables.Table):
    """Table to show call summary by day aggregate"""
    month = tables.Column(orderable=False, verbose_name='Month')
    monday = tables.Column(orderable=False, verbose_name='Monday')
    tuesday = tables.Column(orderable=False, verbose_name='Tuesday')
    wednesday = tables.Column(orderable=False, verbose_name='Wednesday')
    thursday = tables.Column(orderable=False, verbose_name='Thursday')
    friday = tables.Column(orderable=False, verbose_name='Friday')
    saturday = tables.Column(orderable=False, verbose_name='Saturday')
    sunday = tables.Column(orderable=False, verbose_name='Sunday')
    class Meta:
        attrs = {'class': 'table table-bordered table-striped dataTable',
                 'id': 'report_table'}


def get_case_info(case_number):
    """ Get related case information from a case number"""
    report = get_object_or_404(Report, case_id=case_number)
    contact, contact_created = Contact.objects.get_or_create(
        hl_contact=report.telephone
    )
    # Create a new address entry if new contact
    if contact_created:
        address = Address(user=report.user)
        address.save()
        contact.address = address
        contact.save()
    elif contact.address is None:
        address = Address(user=report.user)
        address.save()
        contact.address = address
        contact.save()
    else:
        address = contact.address

    return report, contact, address


@json_view
def save_contact_form(request):
    """Save contact/address form returns json status"""
    contact_form = ContactForm(request.POST or None)
    if contact_form.is_valid():
        case_number = contact_form.cleaned_data.get('case_number')
        report, contact, address = get_case_info(case_number)
        contact.address.hl_names = contact_form.cleaned_data.get('caller_name')
        contact.address.save()
        return {'success': True}

    ctx = {}
    ctx.update(csrf(request))
    form_html = render_crispy_form(form, context=ctx)
    return {'success': False, 'form_html':form_html}


@json_view
def contact_search_form(request):
    """Search contact/address and returns html contact list"""

    form = ContactSearchForm(request.POST or None)
    if form.is_valid():
        telephone = form.cleaned_data.get('telephone')
        name = form.cleaned_data.get('name')
        contacts = Contact.objects.filter(
            Q(address__hl_names__icontains=name) |
            Q(hl_contact=telephone)
        )
        table = ContactTable(contacts)
        table_html = render_to_string(
            'helpline/contacts.html',
            {
                'table': table
            }, request
        )
        return {'success': True, 'table_html': table_html}

    ctx = {}
    ctx.update(csrf(request))
    form_html = render_crispy_form(form, context=ctx)
    return {'success': False, 'form_html':form_html}


@json_view
def save_case_action(request):
    """Save case action returns json status"""
    form = CaseActionForm(request.POST or None)
    if form.is_valid():
        case_number = form.cleaned_data.get('case_number')
        report = Report.objects.get(case=case_number)
        case_status = form.cleaned_data.get('case_status')
        escalate_to = form.cleaned_data.get('escalate_to')
        hl_user = request.user.HelplineUser
        hl_user.hl_status = "Available"
        hl_user.save()
        report.user = request.user
        report.casestatus = case_status
        report.escalatename = escalate_to.user.username if escalate_to else None
        report.hl_time = calendar.timegm(time.gmtime())
        report.save()

        return {'success': True}

    ctx = {}
    ctx.update(csrf(request))
    form_html = render_crispy_form(form, context=ctx)
    return {'success': False, 'form_html':form_html}


@json_view
def save_disposition_form(request):
    """Save disposition, uses AJAX and returns json status"""
    status_message = ''
    status = False
    try:
        form = DispositionForm(request.POST or None)
        case_num = request.POST.get('case_number') or '0'
        if form.is_valid():
            if case_num != '0':
                case = Cases.objects.get(case_number=form.cleaned_data['case_number'])
                ctx = {}
                ctx.update(csrf(request))
                form_html = render_crispy_form(form, context=ctx)
            else:
                case = Cases()
                status_message = 'Complete Case'
            case.case_disposition = form.cleaned_data['disposition']
            case.save()
            request.user.HelplineUser.hl_status = 'Available'
            request.user.HelplineUser.save()
            status = True
        else:
            status = False
            status_message = 'Error: Invalid form'
    except Exception as e:
        status = False
        status_message = e

    
    return {'success': status, 'form_html': status_message}


# @json_view
# def save_disposition_form(request):
#     """Save disposition, uses AJAX and returns json status"""
#     form = DispositionForm(request.POST or None)
#     if form.is_valid():
#         case = Case.objects.get(hl_case=form.cleaned_data['case_number'])
#         case.hl_disposition = form.cleaned_data['disposition']
#         case.save()
#         request.user.HelplineUser.hl_status = 'Available'
#         request.user.HelplineUser.save()
#         return {'success': True}
#     ctx = {}
#     ctx.update(csrf(request))
#     form_html = render_crispy_form(form, context=ctx)
#     return {'success': False, 'form_html': form_html}


@json_view
def contact_create_case(request):
    """Create a case for a contact and return the case url"""
    contact_id = request.POST.get('contact_id', None)
    default_service = Service.objects.all().first()
    if contact_id:
        contact = Contact.objects.get(id=contact_id)
        case = Case()
        report = Report()
        case.contact = contact
        case.user = request.user
        case.hl_popup = 'No'
        case.save()
        report.case = case
        report.callstart = timezone.now().strftime('%H:%M:%S.%f')
        report.calldate = timezone.now().strftime('%d-%m-%Y')
        report.queuename = default_service.queue
        report.telephone = contact.hl_contact
        report.save()
        hl_user = request.user.HelplineUser
        hl_user.case = case
        hl_user.hl_status = 'Busy'
        hl_user.save()
        return {'success': True}
    ctx = {}
    ctx.update(csrf(request))
    return {'success': False}


@json_view
def average_talk_time(request):
    """Return the average talk time for current user, in json"""
    att = request.user.HelplineUser.get_average_talk_time()
    return att


@json_view
def average_hold_time(request):
    """Return the average hold time for current user, in json"""
    awt = 0 #request.user.HelplineUser.get_average_wait_time()
    return awt


def initialize_myaccount(user):
    """Initialize user account to call helpline"""
    try:
        myaccount = HelplineUser()
        myaccount.user_id = user.pk
        myaccount.hl_names = user.username
        myaccount.hl_nick = user.username
        myaccount.hl_key = randint(123456789, 999999999)
        myaccount.hl_auth = randint(1000, 9999)
        myaccount.hl_exten = 0
        myaccount.hl_calls = 0
        myaccount.hl_email = ''
        myaccount.hl_avatar = ''
        myaccount.hl_area = ''
        myaccount.hl_phone = ''
        myaccount.hl_branch = ''
        myaccount.hl_case = 0
        myaccount.hl_clock = 0
        myaccount.hl_time = 0
        myaccount.hl_status = 'Idle'
        # TODO: Update this so site specific
        myaccount.hl_jabber = "%s@%s" % (user.username, 'im.helpline.co.ke')
        myaccount.hl_pass = hashlib.md5("1234").hexdigest()

        myaccount.hl_role = "Supervisor" if user.is_superuser else "Counsellor"
        # Default Service, which is the first service
        default_service = Service.objects.all().first()
        myschedule = Schedule()
        myschedule.user = user
        myschedule.service = default_service

        myschedule.hl_status = 'Offline'

        myschedule.save()
        myaccount.save()
        return True
    except Exception as e:
        return e


def edit_myaccount(request):
    """Edit profile"""
    user_profile = HelplineUser.objects.get(pk=request.user.HelplineUser.pk)
    form = MyAccountForm(request.POST or None, instance=user_profile)
    message = ''
    if request.method == 'POST' and form.is_valid():
        message = user_profile
        form.save()

    return render(request, 'helpline/profile.html',
                  {'form': form,
                   'message': message})


def get_status_count():
    """ Get available, idle and busy agents stats"""
    available = HelplineUser.objects.filter(hl_status__exact='Available').count()
    idle = HelplineUser.objects.filter(hl_status__exact='Idle').count()
    busy_on_call = HelplineUser.objects.filter(hl_status__exact='OnCall').count()
    total = available + idle + busy_on_call
    status_count = {'available': available,
                    'idle': idle,
                    'total': total,
                    'busy_on_call': busy_on_call}
    return status_count

def get_dashboard_stats(request, interval=None):
    default_service = Service.objects.all().first()

    if hasattr(default_service,'walkin_xform') and default_service.walkin_xform:
        default_service_xform = default_service.walkin_xform
    else:
        response = redirect('/ona/%s' % request.user.username)
        return response

    default_service_qa = default_service.qa_xform

    default_service_auth_token = ''
    
    if hasattr(default_service_xform,'user'):
        default_service_auth_token = default_service_xform.user.auth_token
    else:
        message = "Please Configure Service and assign forms"
        return False #redirect('/ona/%s?message=%s' %(request.user,message))

    current_site = get_current_site(request)

    # Set headers
    headers = {
        'Authorization': 'Token %s' % (default_service_auth_token)
    }

    # date time
    midnight_datetime = datetime.combine(
            date.today(), datetime_time.min)
    midnight = calendar.timegm(midnight_datetime.timetuple())

    midnight_string = datetime.combine(
        date.today(), datetime_time.min).strftime('%m/%d/%Y %I:%M %p')
    now_string = timezone.now().strftime('%m/%d/%Y %I:%M %p')

    call_statistics = requests.post('%s/clk/stats/' %(settings.CALL_API_URL)).json()



    home_statistics = {'escalate':0,'closed':0,'pending':0,'total':0,'call_stat':call_statistics,\
    'midnight': midnight,'midnight_string': midnight_string,'now_string': now_string,}
    # SMS stats
    home_statistics['sms'] = SMSCDR.objects.filter(sms_time__date=datetime.today()).count()
    # Email stats
    home_statistics['email'] = Emails.objects.filter(email_time__date=datetime.today()).count()
    # case status statistics
    url_status = 'http://%s/ona/api/v1/charts/%s.json?field_name=case_action' \
    %(current_site, default_service_xform.pk)

    status_stat = requests.get(url_status, headers= headers).json()

    status_text = {'escalate':0,'closed':0,'pending':0,'total':0}
    rrr = [] 

    if status_stat.get('data',None) != None:
        for st_action in status_stat.get('data',{}):
            for sts in status_text:
                r_str = str(st_action['case_action'][0]).lower()
                if sts == r_str:
                    home_statistics[sts] =  st_action['count']
            home_statistics['total'] += st_action['count']

    return home_statistics



def get_dashboard_statsx(user, interval=None):
    """Stats which are displayed on the dashboard, returns a dict
    Get stats from last midnight
    """
    # Get the epoch time of the last midnight
    if interval == 'weekly':
        midnight_datetime = datetime.combine(
            date.today() - timedelta(days=date.today().weekday()),
            datetime_time.min)
        midnight = calendar.timegm(midnight_datetime.timetuple())
    else:
        midnight_datetime = datetime.combine(
            date.today(), datetime_time.min)
        midnight = calendar.timegm(midnight_datetime.timetuple())

    midnight_string = datetime.combine(
        date.today(), datetime_time.min).strftime('%m/%d/%Y %I:%M %p')
    now_string = timezone.now().strftime('%m/%d/%Y %I:%M %p')
    # Get the average seconds of hold time from last midnight.

    total_calls = Report.objects.filter(
        hl_time__gt=midnight).filter(casetype__exact='Call')
    answered_calls = Report.objects.filter(
        hl_time__gt=midnight).filter(calltype__exact='Answered')
    abandoned_calls = Report.objects.filter(
        hl_time__gt=midnight).filter(calltype__exact='Abandoned')
    missed_calls = Clock.objects.filter(
        hl_time__gt=midnight).filter(hl_clock="Missed Call")
    voice_mails = Recorder.objects.filter(
        hl_time__gt=midnight).filter(hl_type__exact='Voicemail')

    total_cases = Report.objects.filter(
        hl_time__gt=midnight).filter(casestatus__gt='')
    closed_cases = Report.objects.filter(
        hl_time__gt=midnight, casestatus__exact='Close')
    open_cases = Report.objects.filter(
        hl_time__gt=midnight, casestatus__exact='Pending')
    referred_cases = Report.objects.filter(
        hl_time__gt=midnight, casestatus__exact='Escalate')

    total_sms = Messaging.objects.filter(hl_time__gt=midnight)

    # Filter out stats for non supervisor user.
    if user.HelplineUser.hl_role != 'Supervisor':
        total_calls = total_calls.filter(user=user)
        missed_calls = missed_calls.filter(user=user)
        answered_calls = answered_calls.filter(user=user)
        total_cases = total_cases.filter(user=user)
        closed_cases = closed_cases.filter(user=user)
        open_cases = open_cases.filter(user=user)
        referred_cases = referred_cases.filter(user=user)

    number_tickets = Ticket.objects.all().count()

    # open & reopened tickets, assigned to current user
    tickets = Ticket.objects.select_related('queue').filter(
        assigned_to=user,
    ).exclude(
        status__in=[Ticket.CLOSED_STATUS, Ticket.RESOLVED_STATUS],
    )

    # att = user.HelplineUser.get_average_talk_time()
    # awt = user.HelplineUser.get_average_wait_time()

    # get QA score

    dashboard_stats = {'midnight': midnight,
                       'midnight_string': midnight_string,
                       'now_string': now_string,
                       # 'att': att,
                       # 'awt': awt,
                       'total_calls': total_calls.count(),
                       'answered_calls': answered_calls.count(),
                       'abandoned_calls': abandoned_calls.count(),
                       'missed_calls': missed_calls.count(),
                       'voice_mails': voice_mails.count(),
                       'total_cases': total_cases.count(),
                       'closed_cases': closed_cases.count(),
                       'open_cases': open_cases.count(),
                       'total_sms': total_sms.count(),
                       'number_tickets': number_tickets,
                       'tickets': tickets,
                       'referred_cases': referred_cases.count()}

    return dashboard_stats

def web_presence(request):
    """Show presence information of agents"""

    user_list = User.objects.filter(is_active__exact=True,HelplineUser__hl_role='Counsellor')

    return render(request,'helpline/presence.html',{'users':user_list})
    # available = HelplineUser.objects.filter(hl_status__exact='Available')
    # busy_on_call = HelplineUser.objects.filter(hl_status__exact='OnCall')
    # idle = HelplineUser.objects.filter(hl_status__exact='Idle')
    # offline = HelplineUser.objects.filter(hl_status__exact='Offline')
    # status_count = get_status_count()

    # Display all agents in the Connected Agents Table
    # Exclude Unavailable agents.
    # agents = HelplineUser.objects.exclude(hl_status='Unavailable')
    # connected_agents_table = ConnectedAgentsTable(agents,
    #                                               order_by=(
    #                                                   request.GET.get('sort',
    #                                                                   'userid')))

    # return render(request,
    #               'helpline/presence.html',
    #               {'connected_agents_table': connected_agents_table})


def report_factory(report='callsummary', datetime_range=None, agent=None,
                   queuename=None, queueid=None, query=None, sort=None,
                   casetype='all', category=None):
    """Create admin reports"""

    # Initialize the filter query dict
    filter_query = {}

    # Convert date range string to datetime object
    if datetime_range:
        try:
            a, b = [datetime_range.split(" - ")[0], datetime_range.split(" - ")[1]]
            from_date = datetime.strptime(a, '%m/%d/%Y %I:%M %p')
            to_date = datetime.strptime(b, '%m/%d/%Y %I:%M %p')

            # Add filter to ajax query string.
            filter_query['datetime_range'] = datetime_range
        except Exception as e:
            from_date = None
            to_date = None
    else:
        from_date = None
        to_date = None

    # Return agent session table for agent session report.
    if report == 'agentsessionreport':
        clock = Clock.objects.filter()
        # Apply filters to queryset.
        if from_date and to_date:
            from_date_epoch = calendar.timegm(from_date.timetuple())
            to_date_epoch = calendar.timegm(to_date.timetuple())
            clock = clock.filter(hl_time__gt=from_date_epoch, hl_time__lt=to_date_epoch)
        if agent:
            clock = clock.filter(user=agent)
            filter_query['agent'] = agent
        # Filter actions. Queue Join etc.
        if query:
            clock = clock.filter(hl_clock__exact=query)
            filter_query['q'] = query

        return AgentSessionTable(clock)

    # The first created service is considered our default service
    # This will change in future to site based or config based views
    default_service = Service.objects.all().first()
    service = default_service

    reports = Report.objects.all()
    cdr = MainCDR.objects.all()
    user = agent

    calltype = {'answeredcalls': 'Answered',
                'missedcalls': 'Abandoned',
                'voicemails': 'Voicemail'}

    casestatus = {'pendingcases': 'Pending',
                  'closedcases': 'Close',
                  'escalatedcases': 'Escalate'}

    if calltype.get(report):
        reports = reports.filter(calltype__exact=calltype.get(report))
    if casestatus.get(report):
        reports = reports.filter(casestatus__exact=casestatus.get(report))
    # Retrun all case types Inbound and outbount for the following reports.
    if report != 'totalcases' and report != 'search':
        if casetype != 'all':
            reports = reports.filter(casetype__iexact=casetype)

    # Apply filters to queryset.
    if from_date and to_date:
        from_date_epoch = calendar.timegm(from_date.timetuple())
        to_date_epoch = calendar.timegm(to_date.timetuple())
        reports = reports.filter(hl_time__gt=from_date_epoch,
            hl_time__lt=to_date_epoch)
        cdr = cdr.filter(hl_time__gt=from_date_epoch,
            hl_time__lt=to_date_epoch)

    if agent:
        reports = reports.filter(user=user)
        cdr = cdr.filter(hl_agent__exact=agent)
        filter_query['agent'] = agent

    if queueid:
        queue = Service.objects.filter(hl_key__exact=queueid)
    if queuename:
        reports = reports.filter(queuename__exact=queuename)

    if category:
        Case = Case.objects.filter(hl_acategory=category)
        filter_query['category'] = category
        reports = reports.filter(case_id__in=cases)

    # Search report data
    if query:
        qset = (
            Q(telephone__icontains=query) |
            Q(case__contact__address__hl_names__icontains=query) |
            Q(casestatus__icontains=query)
        )
        # Check if query is an integer for case id matching.
        # Ask for forgiveness if it's not.
        try:
            val = int(query)
            qset |= (Q(case_id__exact=query))
        except ValueError:
            # Ask for forgiveness.
            pass

        reports = reports.filter(qset)
        filter_query['q'] = query

    # Create a link to the data.
    total_offered = {'count': reports.filter().count(),
                     'filter_query': urllib.urlencode(filter_query),
                     'casetype': casetype}

    # Compute the average talk time from seconds returned.
    seconds = cdr.aggregate(Avg('hl_talktime')).get('hl_talktime__avg')
    att = str(timedelta(seconds=seconds)) if seconds else "00:00:00"

    # Compute the average hold time for seconds returned.
    seconds = cdr.aggregate(Avg('hl_holdtime')).get('hl_holdtime__avg')
    aht = str(timedelta(seconds=seconds)) if seconds else "00:00:00"

    # Compute total talk time from seconds returned in h:m:s format
    seconds = cdr.aggregate(Sum('hl_talktime')).get('hl_talktime__sum')
    total_talktime = str(timedelta(seconds=seconds)) if seconds else "00:00:00"

    # Count Answered, Abandoned and Voicemail calls for a specific queue.
    total_answered = reports.filter(service=service,
                                    calltype__exact='Answered').count()
    total_abandoned = reports.filter(service=service,
                                    calltype__exact='Abandoned').count()
    total_voicemail = reports.filter(service=service,
                                    calltype__exact='Voicemail').count()

    if total_offered.get('count'):
        answered_percentage = "{0:.2f}%".format(
            100.0 * (float(total_answered)/float(total_offered.get('count'))))
        abandoned_percentage = "{0:.2f}%".format(
            100.0 * (float(total_abandoned)/float(total_offered.get('count'))))
    else:
        answered_percentage = "NA"
        abandoned_percentage = "NA"

    # Call summary data.
    callsummary_data = {'service': '%s %s' % (service, datetime_range),
                        'total_offered': total_offered,
                        'total_answered': total_answered,
                        'total_abandoned': total_abandoned,
                        'total_talktime': total_talktime,
                        'answered_percentage': answered_percentage,
                        'abandoned_percentage': abandoned_percentage,
                        'day': from_date.strftime("%A") if from_date else None,
                        'month': from_date.strftime("%B") if from_date else None,
                        'year': from_date.strftime("%Y") if from_date else None,
                        'att': att,
                        'aht': aht,
                        'category': category,
                        'total_voicemail': total_voicemail}

    if report == 'callsummaryreport':
        table = CallSummaryTable([callsummary_data])
    elif report == 'chartreport':
        # Return a dict of the call summary data for chartning.
        return callsummary_data
    else:
        # Check if table is to be sorted.
        table = DashboardTable(reports, order_by=sort) if sort else DashboardTable(reports)

    return table


def ajax_admin_report(request, report, casetype='all'):
    """Returns table of admin reports"""
    form = ReportFilterForm(request.GET)
    datetime_range = request.GET.get("datetime_range")
    agent = request.GET.get("agent")
    query = request.GET.get('q', '')

    table = report_factory(report=report, datetime_range=datetime_range,
                           agent=agent, query=query, casetype=casetype)

    RequestConfig(request).configure(table)
    export_format = request.GET.get('_export', None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response('table.{}'.format(export_format))

    table.paginate(page=request.GET.get('page', 1), per_page=10)

    return render(request, 'helpline/report_factory.html', {
        'table': table,
        'datetime_range': datetime_range,
        'form': form})


def login(request, template_name="helpline/login.html"):
    """Helpline login handler"""
    request.user.HelplineUser.hl_status = "Idle"
    request.user.HelplineUser.save()
    return django_login(request, **{"template_name": template_name})


@login_required
def logout(request, template_name="helpline/loggedout.html"):
    request.user.HelplineUser.hl_status = "Unavailable"
    request.user.HelplineUser.save()

    try:
        hotdesk = Hotdesk.objects.filter(
            agent__exact=request.user.HelplineUser.hl_key)
        hl_user = HelplineUser.objects.get(hl_key=request.user.HelplineUser.hl_key)
        hotdesk.update(agent=0)
        hl_user.hl_exten = ''
        hl_user.hl_jabber = ''
        hl_user.hl_status = 'Unavailable'
        hl_user.save()
        
        queue_manager(hl_user.hl_key,
                      request.session.get('extension'),
                      'queueleave')

    except Exception as e:
        message = e
    return django_logout(request, **{"template_name": template_name})


def helpline_home(request):
    """Helpline home"""
    return redirect("/helpline/")


def report_save_handler(sender, instance, created, **kwargs):
    """Notify relevant users when a report is saved."""

    # Only notify if report is marked as open
    if instance.escalatename != "":
        user = instance.user
        verb = "Escalted case %s. Telephone number: %s Status: %s" % (
            instance.case, instance.telephone, instance.casestatus)
        case = instance.case
        address = instance.address
        names = address.hl_names if address else None


        level = 'info'

        description = """
        Customer Details
        Name: %s
        Phone Number: %s
        """ % (
            names,
            instance.telephone
            )

        escalate_to = User.objects.get(username=instance.escalatename)

        notify.send(user, recipient=escalate_to,
                verb=verb, level=level, description=description)


@json_view
def asterisk_alert(request, auth, dialstatus, case_id):
    """Accept user alerts from Asterisk"""
    agent = HelplineUser.objects.get(hl_auth=auth)
    user = agent.user
    case = Case.objects.get(hl_case=case_id)

    alert = {'CHANUNAVAIL': 'unavailable',
             'NOANSWER': 'missed',
             'BUSY': 'busy'}

    verb = "%s" % (alert[dialstatus])
    description = "Dial status is %s for case %s" % (alert[dialstatus], case_id)
    channel = agent.hl_exten.split('/')[1]
    notify.send(user, recipient=user, verb=verb,
                description=description, level="warning")
    message = 'Notification sent'
    return {'message': message,
            'auth': auth,
            'agent channel': channel}


@json_view
def ajax_get_subcategory(request, category):
    """Accept ajax request for subcategories"""
    results = Category.objects.filter(
        hl_category__iexact=category).values('hl_category', 'hl_subcategory')
    data = {'data': list(results)}
    return data


@json_view
def ajax_get_sub_subcategory(request, category):
    """Accept ajax request for sub-subcategories"""
    results = Category.objects.filter(
        hl_subcategory=category).values('hl_subsubcat', 'hl_subsubcat')
    data = {'data': list(results)}
    return data

@login_required
def pivot(request):
    report = {}
    with connection.cursor() as cursor:
            query = 'SELECT json from logger_xform where id = 1'
            cursor.execute(query)
            report['data'] = namedtuplefetchall(cursor).json
    return render(request, 'helpline/report_pivot.html',report)

@login_required
def wall(request):
    ret = stat(request)
    return HttpResponse(ret)

@login_required
def stat(request):
    """Display statistics for the wall board"""

    # Case statistics

    default_service = Service.objects.all().first()
    default_service_xform = default_service.walkin_xform

    default_service_qa = default_service.qa_xform
    default_service_auth_token = default_service_xform.user.auth_token
    current_site = get_current_site(request)

    # Graph data
    headers = {
        'Authorization': 'Token %s' % (default_service_auth_token)
    }

    url_status = 'http://%s/ona/api/v1/charts/%s.json?field_name=case_action' \
    %(current_site, default_service_xform.pk)

    status_stat = requests.get(url_status, headers= headers).json() or {}

    status_stats = {'escalate':0,'closed':0,'pending':0,'total':0}
    rrr = []
    for st_action in status_stat['data']:
        for sts in status_stats:
            r_str = str(st_action['case_action'][0]).lower()
            if sts == r_str:
                status_stats[sts] =  st_action['count']
        status_stats['total'] += st_action['count']

    # agent status
    url_agents = '%s/clk/agent/' %(settings.CALL_API_URL)

    agent_status = requests.get(url_agents, headers=headers).json()

    # call statistics
    call_statistics = requests.post('%s/clk/stats/' %(settings.CALL_API_URL)).json()

    dashboard_stats = get_dashboard_stats(request.user)
    week_dashboard_stats = get_dashboard_stats(request.user, interval='weekly')

    userlist = User.objects.filter(is_active=True,HelplineUser__hl_role='Counsellor').exclude(HelplineUser__hl_status='Unavailable').exclude(HelplineUser__hl_status='Offline').select_related('HelplineUser')
    
    def get_queue_status(agent_id):
        ret_val = ''
        for ag in agent_status:
            if str(ag['agent']) == str(agent_id):
                ret_val = str(ag['status']) 
        return ret_val   

    agent_status_x = {}

    for user_x in userlist:
        agent_status_x.update({str(user_x.username):get_queue_status(user_x.HelplineUser.hl_key)})

    statistics = {'case': status_stats,'call':call_statistics,'dashboard_stats': dashboard_stats,
                   'week_dashboard_stats': week_dashboard_stats,'users':userlist,'call_agents':agent_status_x}
    return render(request, 'helpline/wall.html',statistics)

@login_required
def sources(request, source=None,itemid=None):
    """Display data source"""
    data_messages = ''
    item = ''
    message = ''

    home_statistics = get_dashboard_stats(request)

    if source == 'email':
        data_messages = Emails.objects.all()
        item = Emails

        if request.method == 'POST':
            email = Emails()

            try:

                # email.email_idkey = 
                email.email_from      = 'kemboicheru@gmail.com'
                email.email_status    = 0
                email.email_body      = request.POST.get('message', None)
                email.email_subject   = ''
                email.email_date      = datetime.now()
                email.save()


                server = smtplib.SMTP('mail.bitz-itc.com')
                server.starttls()
                server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                server.set_debuglevel(2)
                server.sendmail("support@" + settings.BASE_DOMAIN,'kemboicheru@gmail.com',request.POST.get('message', None))
                server.quit()
                message = "Mail sent successfully"
            except Exception as e:
                message = "Error: %s" %e


    if source == 'sms':
        data_messages = SMSCDR.objects.all() #.order_by('-sms_time')
        item = SMSCDR

        # if request.method == 'POST':
        #     email = Emails()
            
        #     email.email_idkey = 
        #     email.email_from      = 
        #     email.email_status    = 0
        #     email.email_body      = 
        #     email.email_subject   = 
        #     email.email_date      = date.now()

    if itemid != None:
        data_messages = item.objects.get(pk=itemid) # (Emails,pk=itemid)
        source = 'read_%s' % (source) 

    template = 'helpline/%s.html' % (source)
    return render(request, template, {'data_messages':data_messages,'message':message,'home':home_statistics})


def get_data_queues(queue=None):
    data = {} # backend.get_data_queues()
    if queue is not None:
        try:
            data = data[queue]
        except:
            raise Http404("Queue not found")
    return data


@login_required
@json_view
def queues(request):
    data = get_data_queues()
    return {'data': data}


@login_required
def queue(request, name=None):
    data = get_data_queues(name)
    return render(request, 'helpline/queue.html',
                  {'data': data,
                   'name': name
                  })


@login_required
@json_view
def queue_json(request, name=None):
    data = get_data_queues(name)
    return {'data': data}

class MyModelDataSource(ModelDataSource):
    def get_data(self):
        data = super(MyModelDataSource, self).get_data()
        # header = data[0]
        data_without_header = data
        # for row in data_without_header:
        #     # Assuming second column contains datetime
        #     row[1] = row[1].year
        # data_without_header.insert(0, header)
        return data_without_header

post_save.connect(report_save_handler, sender=Report)
