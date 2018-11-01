# -*- coding: utf-8 -*-
"""Helpline views """

import os
import calendar

import time
from random import randint
import hashlib
import urllib

import imaplib
import email

from itertools import tee

from datetime import timedelta, datetime, date, time as datetime_time

from nameparser import HumanName
import requests

from django.shortcuts import render, redirect
from django.http import JsonResponse, Http404
from django.http import (HttpResponse, HttpResponseBadRequest,
                         HttpResponseForbidden, HttpResponseRedirect)
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.template.context_processors import csrf
from django.template.loader import render_to_string
from django.db.models import Avg
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
        Messaging,Emails,SMSCDR,Cases

from helpline.forms import QueueLogForm,\
        ContactForm, DispositionForm, CaseSearchForm, MyAccountForm,RegisterUserForm, \
        ReportFilterForm, QueuePauseForm, CaseActionForm, ContactSearchForm

from helpline.qpanel.config import QPanelConfig
from helpline.qpanel.backend import Backend
if QPanelConfig().has_queuelog_config():
    from helpline.qpanel.model import queuelog_data_queue
import json
from django.template.defaulttags import register
from onadata.apps.logger.models import Instance, XForm

from onadata.libs.utils.chart_tools import build_chart_data
from onadata.libs.utils.user_auth import (get_xform_and_perms, has_permission,
                                          helper_auth_helper)



cfg = QPanelConfig()
backend = Backend()

def success(request):
    return render(request,'helpline/success.html');
    
@login_required
def home(request):
    "Dashboard home"

    try:
        att = request.user.HelplineUser.get_average_talk_time()
        awt = request.user.HelplineUser.get_average_wait_time()
    except Exception as e:
        new = initialize_myaccount(request.user)
        return redirect("/helpline/#%s/new%s" % (e, new))

    dashboard_stats = get_dashboard_stats(request.user)
    status_count = get_status_count()
    case_search_form = CaseSearchForm()
    queue_form = QueueLogForm(request.POST)
    queue_pause_form = QueuePauseForm()
    queues = get_data_queues()

    default_service = Service.objects.all().first()
    default_service_xform = default_service.walkin_xform
    default_service_auth_token = '7331a310c46884d2643ca9805aaf0d420ebfc831' # default_service_xform.user.auth_token
    current_site = get_current_site(request)
    default_service_xform.pk = 29

    gtdata = []
    stdata = []
    if default_service != '' and default_service != 0 and default_service_xform:
        url = 'https://%s/ona/api/v1/charts/%s.json?field_name=_submission_time' % (
            current_site,
            default_service_xform.pk
        )

        # Graph data
        headers = {
                'Authorization': 'Token %s' % (default_service_auth_token)
        }

        stat = requests.get(url,headers=headers).json()


        for dt in get_item(stat, 'data'):
            t = [str(get_item(dt, '_submission_time')), get_item(dt, 'count')]
            gtdata.append(t)

        stype = 'case_action'

        if request.user.HelplineUser.hl_role == 'Caseworker':
            url = 'https://%s/ona/api/v1/charts/%s.json?field_name=client_state' %(current_site,default_service_xform.pk)
            color = ['#00a65a','#00c0ef','#f39c12','#808000','#C7980A', '#F4651F', '#82D8A7', '#CC3A05', '#575E76', '#156943', '#0BD055', '#ACD338']
            stype = 'client_state'
        else:
            url = 'https://%s/ona/api/v1/charts/%s.json?field_name=case_action' %(current_site,default_service_xform.pk)
            color = ['#00a65a','#00c0ef','#f39c12']

        #for case status 
        status_data = requests.get(url, headers= headers).json();

        ic = 0
        for dt in get_item(status_data,'data'):#  status_data['data']:
            lbl = dt[str(stype)]
            if isinstance(lbl,list):
                lbl = lbl[0].encode('UTF8') if not len(lbl) == 0 else "Others"
            else:
                lbl if not len(lbl) == 0 else "Others"

            col = color[ic]
            ic += 1
            stdata.append({"label":str(lbl),"data":str(str(dt['count'])),"color":str(col)})

    return render(request, 'helpline/home.html',
                  {'dashboard_stats': dashboard_stats,
                   'att': att,
                   'awt': awt,
                   'queues': queues,
                   'case_search_form': case_search_form,
                   'queue_form': queue_form,
                   'queue_pause_form': queue_pause_form,
                   'status_count': status_count,
                   'gdata': gtdata,
                   'dt': stdata
                   })


@login_required
def leta(request):
    """Return the login duration and ready duration"""
    login_duration = request.user.HelplineUser.get_login_duration()
    ready = request.user.HelplineUser.get_ready_duration()
    return render(request, 'helpline/leta.html',
                  {'ld': login_duration,
                   'ready': ready})

def sync_sms(request):
    if request.method == 'POST':
        sms = SMSCDR()
        sms.contact = request.POST.get('phone')
        sms.msg     = request.POST.get('msg')
        sms.time    = request.POST.get('time')
        sms.type    = 'INBOX'
        sms.save()
    else:
        sms_list = SMSCDR.objects.all().order_by('sms_time')
        return HttpResponse(serializers.serialize('json', sms_list), content_type="application/json")

def sync_emails(request):
    FROM_EMAIL  = "support@" + settings.BASE_DOMAIN
    SMTP_PORT   = 993

    message = {'message':'','count':0}
    try:
        mail = imaplib.IMAP4_SSL(settings.SMTP_SERVER)
        mail.login(FROM_EMAIL,settings.SUPPORT_PASS)
        mail.select('inbox')

        type, data = mail.search(None, 'UNSEEN')
        mail_ids = data[0]

        id_list = mail_ids.split() 
        mail_count = len(id_list)

        if(mail_count > 1):
            first_email_id = int(id_list[0])
            latest_email_id = int(id_list[-1])
        elif mail_count == 1:
            first_email_id = int(id_list[0])
            latest_email_id = int(id_list[0])
        elif mail_count == 0:
            return HttpResponse("No new mails found ")



        for i in range(latest_email_id,first_email_id-1, -1):
            typ, data = mail.fetch(i, '(RFC822)' )
            for response_part in data:
                model_mail = Emails()
                if isinstance(response_part, tuple):
                    msg = email.message_from_string(response_part[1])
                    model_mail.email_idkey    = i
                    model_mail.email_from     = msg['from']
                    model_mail.email_body     = str(msg.get_payload())
                    model_mail.email_subject  = msg['subject']
                    model_mail.email_date     = msg['date']
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
def manage_users(request):
    """View user management page"""
    userlist  = HelplineUser.objects.all()
    message = ""
    return render(request, 'helpline/users.html',{'systemusers':userlist,'message':message})

def increment_case_number():
    case = Cases.objects.all().last()

    if case:
        case = case.case_number

    if not case:
        return 100001
    else:
        return int(case) + int(1)

@login_required
def case_number(request,case_source):
    case = Cases()
    caseid = increment_case_number()
    case.case_number = caseid
    case.case_source = case_source
    case.save()
    return HttpResponse(caseid)

@login_required
def new_user(request):
    message = ''
    if request.method == 'POST':
        form = RegisterUserForm(request.POST,request.FILES)
        if form.is_valid():
            user = User()
            try:
                names = str(form.cleaned_data['names']).split(" ");
                user.password = md5("Cheruiyot")
                user.username = form.cleaned_data['username']
                user.first_name = str(names[0]) if names[0] else None
                user.last_name = str(names[1]) if names[1] else None
                user.email = form.cleaned_data['useremail']
                user.is_active = True

                user.save()

                user.HelplineUser.hl_key   = randint(123456789, 999999999)
                user.HelplineUser.hl_auth  = randint(1234, 9999)
                user.HelplineUser.hl_role  = form.cleaned_data['userrole']
                user.HelplineUser.hl_names = form.cleaned_data['names']
                user.HelplineUser.hl_nick  = form.cleaned_data['username']
                user.HelplineUser.hl_email = form.cleaned_data['useremail']
                user.HelplineUser.hl_phone = form.cleaned_data['phone']


                uploaded_file_url = ''
                filename = ''
                if request.FILES['avatar']:
                    myfile = request.FILES['avatar']
                    fs = FileSystemStorage()
                    filename = fs.save(myfile.name, myfile)
                    uploaded_file_url = fs.url(filename)

                

                user.HelplineUser.hl_avatar = uploaded_file_url
                user.HelplineUser.hl_time = time.time()
                user.save()
                message = "User saved succeefully"
                form = RegisterUserForm()

            except Exception as e:
                message = 'Error saving user: %s' % e
        else:
            messages.error(request, "Error")
            message = "Invalid form"
    else:
        form = RegisterUserForm()
        message = 'Not posted'
    return render(request, 'helpline/user.html',{'form':form,'message':message})


@login_required
def user_profile(request,user_id):
    user_edit = get_object_or_404(HelplineUser,user_id)
    message = ''

    if request.method == 'POST':
        form = RegisterUserForm(request.POST,request.FILES,instance=user_edit)
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

    return render(request, 'helpline/user.html',{'form':user_edit,'message':message})


@login_required
def queue_log(request):
    """Join Asterisk queues."""
    services = Service.objects.all()
    if request.method == 'POST':
        queue_form = QueueLogForm(request.POST)
        if queue_form.is_valid():
            extension = queue_form.cleaned_data['softphone']
            try:
                # Get the hotline object from the extension.
                hotdesk = Hotdesk.objects.get(extension=extension)

                hotdesk.jabber = 'helpline@jabber'
                hotdesk.status = 'Available'
                hotdesk.agent = request.user.HelplineUser.hl_key
                hotdesk.user = request.user

                agent = request.user.HelplineUser
                agent.hl_status = 'Available'
                agent.hl_exten = "%s/%s" % (hotdesk.extension_type, hotdesk.extension)

                hotdesk.save()
                agent.save()

                message = backend.add_to_queue(
                    queue='Q718874580',
                    interface=agent.hl_exten,
                    member_name=request.user.get_full_name()
                )

                request.session['queuejoin'] = 'join'
                request.session['queuestatus'] = 'queuepause'
                request.session['extension'] = extension

            except Exception as e:
                message = e

            return redirect("/helpline/#%s" % (message))
    else:
        queue_form = QueueLogForm()

    return redirect("dashboard_home")


def queue_leave(request):
    """Leave Asterisk queues."""
    services = Service.objects.all()
    queue_form = QueueLogForm()
    user_id = request.user.pk
    HelplineUser.objects.filter(user_id=user_id).update(hl_status='Idle')

    try:
        hotdesk = Hotdesk.objects.filter(agent__exact=request.user.HelplineUser.hl_key)
        hl_user = HelplineUser.objects.get(hl_key=request.user.HelplineUser.hl_key)
        hotdesk.update(agent=0)

        request.session['queuejoin'] = 'out'
        request.session['status'] = 'out'
        request.session['jabber'] = ''
        request.session['queuestatus'] = 'queueunpause'
        message = backend.remove_from_queue(
            agent=hl_user.hl_exten,
            queue='Q718874580'
        )
        hl_user.hl_exten = ''
        hl_user.hl_jabber = ''
        hl_user.hl_status = 'Unavailable'
        hl_user.save()

    except Exception as e:
        message = e

    return redirect("/helpline/#%s" % (message))


@json_view
def queue_remove(request, auth):
    """Remove a user from the Asterisk queue."""
    agent = HelplineUser.objects.get(hl_auth=auth)
    agent.hl_status = 'Idle'

    try:
        hotdesk = Hotdesk.objects.filter(agent__exact=agent.hl_key)
        hotdesk.update(agent=0)
        agent.hl_exten = ''
        agent.hl_jabber = ''
        schedules = Schedule.objects.filter(user=agent.user)
        if schedules:
            for schedule in schedules:
                data = backend.remove_from_queue(
                    agent="SIP/%s" % (request.session.get('extension')),
                    queue='%s' % (schedule.service.queue),
                )
        else:
            data = _("Agent does not have any assigned schedule")
        agent.save()

    except Exception as e:
        data = e

    return redirect("/helpline/status/web/presence/#%s" % (data))


def queue_pause(request):
    """Pause Asterisk Queue member"""
    form = QueuePauseForm(request.POST)
    if form.is_valid():
        schedules = Schedule.objects.filter(user=request.user)
        if not schedules:
            message = _("Agent does not have any assigned schedule")
        for schedule in schedules:
            message = backend.pause_queue_member(
                queue='%s' % (schedule.service.queue),
                interface='%s' % (request.user.HelplineUser.hl_exten),
                paused=True
            )
            clock = Clock()
            clock.user = request.user
            clock.hl_clock = form.cleaned_data.get('reason')
            clock.service = schedule.service
            clock.hl_time = int(time.time())
            clock.save()
        request.user.HelplineUser.hl_status = 'Pause'
        request.user.HelplineUser.save()
    else:
        message = "failed"

    return redirect("/helpline/#%s" % (message))


def queue_unpause(request):
    """Unpause Asterisk Queue member"""
    schedules = Schedule.objects.filter(user=request.user)
    if schedules:
        for schedule in schedules:
            message = backend.pause_queue_member(
                queue='%s' % (schedule.service.queue),
                interface='%s' % (request.user.HelplineUser.hl_exten),
                paused=False
            )
            clock = Clock()
            clock.hl_clock = "Unpause"
            clock.user = request.user
            clock.service = schedule.service
            clock.hl_time = int(time.time())
            clock.save()
    else:
        message = _("Agent does not have any assigned schedule")

    request.user.HelplineUser.hl_status = 'Available'
    request.user.HelplineUser.save()

    return redirect("/helpline/#%s" % (message))


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
    return dictionary.get(key,"")


@login_required
def caseview(request, form_name, case_id):
    """View case or submission information"""

    default_service = Service.objects.all().first()
    default_service_xform = default_service.call_xform
    default_service_auth_token = default_service_xform.user.auth_token
    current_site = get_current_site(request)

    url = 'https://%s/ona/api/v1/data/%s/' % (
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

        for key,value in recs.items():
            #if not (key.startswith('_') and key.endswith('_')):# str(key) == "_id":
            key = str(key)
            if key.find('/') != -1:
                k = key.split('/')
                l = len(k)
                kk = str(k[l-1])
            else:
                kk = str(key)
            if isinstance(value,dict) and len(value) >= 1:
                record.update(get_records(value))
            elif isinstance(value,list) and len(value) >= 1:
                if isinstance(value[0],dict):
                    record.update(get_records(value[0]))
            else:
                if not kk in recordkeys and not kk.endswith('ID') and str(value) != 'yes' and str(value) != 'no' and not (kk.startswith('_') and kk != '_id' and kk != '_submission_time'  and kk != '_last_edited'):
                    recordkeys.append(kk)
                record.update({kk : str(value).capitalize()})
        return record


    if isinstance(stat,dict) and len(stat) > 1:
        statrecords.append(get_records(stat))

    for hist in history:
        if isinstance(hist,dict) and len(hist) > 1:
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

@login_required
def reports(request, report, casetype='Call'):
    """Report processing and rendering"""
    default_service = Service.objects.all().first()
    default_service_xform = default_service.walkin_xform
    default_service_auth_token = default_service_xform.user.auth_token
    current_site = get_current_site(request)


    url = 'https://%s/ona/api/v1/data/%s' % (
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
    xform = get_form({'id_string__iexact': str(default_service.walkin_xform)})

    query = request.GET.get('q', '')
    datetime_range = request.GET.get("datetime_range")
    agent = request.GET.get("agent")
    category = request.GET.get("category", "")
    form = ReportFilterForm(request.GET)
    dashboard_stats = get_dashboard_stats(request.user)

    request_string = ''

    if datetime_range == '':
        start_date, end_date = [datetime_range.split(" - ")[0], datetime_range.split(" - ")[1]]
        start_date = datetime.strptime(start_date, '%m/%d/%Y %I:%M %p')
        end_date = datetime.strptime(end_date, '%m/%d/%Y %I:%M %p')

    if report == 'pendingcases':
        request_string = '&query={"case_actions/case_action":{"$i":"pending"}}'
    elif report == 'today':
        td_date = datetime.today()
        request_string = '&date_created__day=' + td_date.strftime('%d')
        request_string += '&date_created__month=' + td_date.strftime('%m')
        request_string += '&date_created__year=' + td_date.strftime('%Y')

    xforms = requests.get('https://%s/ona/api/v1/forms' % (current_site), headers= headers).json();
    xformx = {}

    #split to get xform object
    for xfrm in xforms:
        if str(xfrm['id_string']) == id_string:
            for key,frm in xfrm.items():
                xformx.update({str(key):str(frm)})

   #  stat = requests.get('https://%s/ona/api/v1/data/' % (current_site) + xformx['formid'] + '?page=1&page_size=50' + request_string, headers= headers).json();
    if request.user.HelplineUser.hl_role == 'Counsellor':
        request_string += '&submitted_by__username=%s' %(username)


    stat = requests.get('https://%s/ona/api/v1/data/%s?page=1&page_size=50' %(current_site,default_service_xform.pk) + request_string, headers= headers).json();
    # + '&sort={"_id":-1}'
    statrecords = []
    recordkeys = []

    ##brings up data only for existing records
    def get_records(recs):
        return_obj = []
        record = {}

        for key,value in recs.items():
            #if not (key.startswith('_') and key.endswith('_')):# str(key) == "_id":
            key = str(key)
            if key.find('/') != -1:
                k = key.split('/')
                l = len(k)
                kk = str(k[l-1])
            else:
                kk = str(key)
            if isinstance(value,dict) and len(value) >= 1:
                record.update(get_records(value))
            elif isinstance(value,list) and len(value) >= 1:
                if isinstance(value[0],dict):
                    record.update(get_records(value[0]))
            else:
                if not kk in recordkeys and not kk.endswith('ID') and str(value) != 'yes' and str(value) != 'no' and str(kk) != 'case_id'  and str(kk) != 'uuid':
                    recordkeys.append(kk)
                record.update({kk : str(value).capitalize()})
        return record


    for rec in stat:
        if isinstance(rec,dict) and len(rec) > 1:
            statrecords.append(get_records(rec))

    if len(recordkeys) > 0:
        recordkeys.append('Date Created')
    else:
        recordkeys = False

    sort = request.GET.get('sort')
    report_title = {report: _(str(report).capitalize() + " Reports")}
    '''report_title = {
        'performance': _('Performance Reports'),
        'counsellor': _('Counsellor Reports'),
        'case': _('Case Reports'),
        'call': _('Call Reports'),
        'service': _('Service Reports')
    }'''

    table = report_factory(report=report,
                           datetime_range=datetime_range,
                           agent=agent,
                           query=query, sort=sort,
                           category=category,
                           casetype=casetype)

    # Export table to csv
    export_format = request.GET.get('_export', None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response('table.{}'.format(export_format))
    table.paginate(page=request.GET.get('page', 1), per_page=10)

    data = {
        'owner': default_service_xform.user,
        'xform': default_service_xform,
        'title': report_title.get(report),
        'report': report,
        'form': form,
        'datetime_range': datetime_range,
        'dashboard_stats': dashboard_stats,
        'table': table,
        'query': query,
        'statrecords': statrecords,
        'recordkeys': recordkeys
    }

    callreports = ["missedcalls", "voicemails", "totalcalls",
                   "answeredcalls", "abandonedcalls", "callsummaryreport",
                  "search", "agentsessionreport"]

    if report in callreports:
        htmltemplate = "helpline/reports.html"
    elif report == 'nonanalysed':
        htmltemplate = "helpline/nonanalysed.html"
    else:
        htmltemplate = "helpline/report_body.html"

    return render(request, htmltemplate, data)


@login_required
def analysed_qa(request,report='analysed'):
    """
    Process QA result reports for the current service case form
    """
    default_service = Service.objects.all().first()
    default_service_xform = default_service.qa_xform
    default_service_auth_token = default_service_xform.user.auth_token
    current_site =  get_current_site(request)


    url = 'https://%s/ona/api/v1/data/%s' % (
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

    xforms = requests.get('https://%s/ona/api/v1/forms' % (current_site), headers= headers).json();
    xformx = {}

    #split to get xform object, this will allow us to obtain xform fields
    for xfrm in xforms:
        if str(xfrm['id_string']) == id_string:
            for key,frm in xfrm.items():
                xformx.update({str(key):str(frm)})

    #stat = requests.get('https://%s/ona/api/v1/data/' % (current_site) + xformx['formid'] + '?page=1&page_size=50' + request_string, headers= headers).json();
    
    if request.user.HelplineUser.hl_role == 'Counsellor':
        request_string += '&submitted_by__username=%s' %(username)


    stat = requests.get('https://%s/ona/api/v1/data/%s?page=1&page_size=50' %(current_site,default_service_xform.pk), headers= headers).json();
    # + '&sort={"_id":-1}'
    statrecords = []
    recordkeys = []

    ##brings up data only for existing records
    def get_records(recs):
        return_obj = []
        record = {}

        for key,value in recs.items():
            #if not (key.startswith('_') and key.endswith('_')):# str(key) == "_id":
            key = str(key)
            if key.find('/') != -1:
                k = key.split('/')
                l = len(k)
                kk = str(k[l-1])
            else:
                kk = str(key)
            if isinstance(value,dict) and len(value) >= 1:
                record.update(get_records(value))
            elif isinstance(value,list) and len(value) >= 1:
                if isinstance(value[0],dict):
                    record.update(get_records(value[0]))
            else:
                if not kk in recordkeys and not kk.endswith('ID') and str(value) != 'yes' and str(value) != 'no' and str(kk) != 'case_id'  and str(kk) != 'uuid':
                    recordkeys.append(kk)
                record.update({kk : str(value).capitalize()})
        return record


    for rec in stat:
        if isinstance(rec,dict) and len(rec) > 1:
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
    if action == 'queuejoin':
        data = backend.add_to_queue(
            agent="SIP/%s" % (extension),
            queue='Q718874580',
            member_name=user.get_full_name()
        )
    elif action == 'queueleave':
        data = backend.remove_from_queue(
            agent="SIP/%s" % (extension),
            queue='Q718874580',
        )
    return data

def home_direct():
    return Redirect('/helpline/')

@login_required
def case_form(request, form_name):
    """Handle Walkin and CallForm POST and GET Requests"""


    default_service = Service.objects.all().first()
    default_service_xform = default_service.walkin_xform
    default_service_auth_token = default_service_xform.user.auth_token
    current_site = get_current_site(request)
    default_service_xform.pk = 29

    
    """
    Graph data
    """
    headers = { 
            'Authorization': 'Token %s' %(default_service_auth_token)
    }

    #charts
    url = 'https://%s/ona/api/v1/data/%s' %(current_site,default_service_xform.pk)

    message = ''
    initial = {}
    data = {}
    data['enketo_url'] = settings.ENKETO_URL
    data['base_domain'] = settings.BASE_DOMAIN
    data['data_url'] = url
    data['data_token'] = default_service_auth_token

    service = Service.objects.all().first()
    if(form_name == 'walkin'):
        xform = service.walkin_xform
        data['form_name'] = 'walkin'
    elif(form_name == 'call'):
        xform = service.call_xform
        data['form_name'] = 'call'
    elif(form_name == 'qa'):
        xform = service.qa_xform
        data['form_name'] = 'qa'
    elif(form_name == 'webonline'):
        xform = service.web_online_xform
        data['form_name'] = 'webonline'
    else:
        xform = service.call_xform


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


        if case_number:
            try:
                my_case = int(case_number)
            except ValueError:
                raise Http404(_("Case not found"))
            my_case = get_object_or_404(Case, hl_case=case_number)
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
            data['contact_form'] = ContactForm(
                initial={
                    'caller_name': address.hl_names,
                    'phone_number': contact.hl_contact,
                    'case_number': my_case
                }
            )
            data['case_action_form'] = CaseActionForm(
                initial={
                    'case_number': my_case
                }
            )

            try:
                case_history_table.paginate(page=request.GET.get('page', 1), per_page=10)
            except Exception as e:
                # Do not paginate if there is an error
                pass

        form_url = get_form_url(request, username, settings.ENKETO_PROTOCOL)
        # Check if we're looking for a case.
        if case_number:
            my_case = Case.objects.get(hl_case=case_number)
            report, contact, address = get_case_info(case_number)
        try:
            url = enketo_url(form_url, xform.id_string)
            uri = request.build_absolute_uri()

            # Use https for the iframe parent window uri, always.
            uri = uri.replace('http://', 'https://')

            # Poor mans iframe url gen
            parent_window_origin = urllib.quote_plus(uri)
            iframe_url = url[:url.find("::")] + "i/" + url[url.find("::"):]+\
              "?d[/%s/case_id]=%s&parentWindowOrigin=" % (xform.id_string, case_number) + parent_window_origin
            data['iframe_url'] = iframe_url
            if not url:
                return HttpResponseRedirect(
                    reverse(
                        'form-show',
                        kwargs={'username': username,
                                'id_string': xform.id_string}))
#            return HttpResponseRedirect(iframe_url)
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

    url = 'https://%s/ona/api/v1/data/%s/%s/enketo?return_url=https://%s/helpline/success/&format=json' % (current_site,default_service_xform.pk,case_id,current_site)
    req = requests.get(url,headers=headers).json()
    return render(request,'helpline/case_form_edit.html',{'case':case_id,'iframe_url':get_item(req,'url')})

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
    address = tables.Column(verbose_name= 'Name')
    hl_contact = tables.Column(verbose_name= 'Phone')
    action = tables.TemplateColumn('<a onClick="createCase({{ record.id }});"><i class="fa fa-plus"></i>Create Case</a>', verbose_name="Action")
    class Meta:
        model = Contact
        fields = {'address', 'hl_contact'}
        attrs = {'class': 'table table-bordered table-striped dataTable'}


class CaseHistoryTable(tables.Table):
    """Show related Case form contact"""
    case = tables.TemplateColumn('{% if record.case %}<a href="{{ record.get_absolute_url }}">{{record.case }}</a>{% else %}-{% endif %}')
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
                               ''',orderable=False,verbose_name='Avg. Talk Time')

    aht = tables.TemplateColumn('''{% with aht=record.get_average_wait_time %}
                                {{ aht.hours }}:{{ aht.min }}:{{ aht.seconds }}
                                {% endwith %}
                               ''',orderable=False,verbose_name='Avg. Hold Time')
    ready = tables.TemplateColumn('''{% with rd=record.get_ready_duration %}
                                {{ rd.hours }}:{{ rd.min }}:{{ rd.seconds }}
                                {% endwith %}
                               ''',orderable=False,verbose_name='Ready')
    action = tables.TemplateColumn('''
                                   {% ifequal record.hl_status 'Available' %}
                                   <a href="{% url 'queue_remove' record.hl_auth %}">Remove from Queue</a>
                                   {% endifequal %}
                               ''',orderable=False,verbose_name='Action')
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
        report.user =request.user
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
    form = DispositionForm(request.POST or None)
    if form.is_valid():
        case = Case.objects.get(hl_case=form.cleaned_data['case_number'])
        case.hl_disposition = form.cleaned_data['disposition']
        case.save()
        request.user.HelplineUser.hl_status = 'Available'
        request.user.HelplineUser.save()
        return {'success': True}
    ctx = {}
    ctx.update(csrf(request))
    form_html = render_crispy_form(form, context=ctx)
    return {'success': False, 'form_html': form_html}


@json_view
def save_disposition_form(request):
    """Save disposition, uses AJAX and returns json status"""
    form = DispositionForm(request.POST or None)
    if form.is_valid():
        case = Case.objects.get(hl_case=form.cleaned_data['case_number'])
        case.hl_disposition = form.cleaned_data['disposition']
        case.save()
        request.user.HelplineUser.hl_status = 'Available'
        request.user.HelplineUser.save()
        return {'success': True}
    ctx = {}
    ctx.update(csrf(request))
    form_html = render_crispy_form(form, context=ctx)
    return {'success': False, 'form_html': form_html}


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
    awt = request.user.HelplineUser.get_average_wait_time()
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


def get_dashboard_stats(user, interval=None):
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

    att = user.HelplineUser.get_average_talk_time()
    awt = user.HelplineUser.get_average_wait_time()

    # get QA score

    dashboard_stats = {'midnight': midnight,
                       'midnight_string': midnight_string,
                       'now_string': now_string,
                       'att': att,
                       'awt': awt,
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
    available = HelplineUser.objects.filter(hl_status__exact='Available')
    busy_on_call = HelplineUser.objects.filter(hl_status__exact='OnCall')
    idle = HelplineUser.objects.filter(hl_status__exact='Idle')
    offline = HelplineUser.objects.filter(hl_status__exact='Offline')
    status_count = get_status_count()

    # Display all agents in the Connected Agents Table
    # Exclude Unavailable agents.
    agents = HelplineUser.objects.exclude(hl_status='Unavailable')
    connected_agents_table = ConnectedAgentsTable(agents,
                                                  order_by=(
                                                      request.GET.get('sort',
                                                                      'userid')))

    return render(request,
                  'helpline/presence.html',
                  {'connected_agents_table': connected_agents_table})


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
            clock = clock.filter(hl_time__gt=from_date_epoch,hl_time__lt=to_date_epoch)
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
def wall(request):
    """Display statistics for the wall board"""
    dashboard_stats = get_dashboard_stats(request.user)
    week_dashboard_stats = get_dashboard_stats(request.user, interval='weekly')
    return render(request, 'helpline/wall.html',
                  {'dashboard_stats': dashboard_stats,
                   'week_dashboard_stats': week_dashboard_stats})

@login_required
def sources(request, source=None):
    """Display data source"""
    data_messages = ''
    if source == 'email':
        data_messages  = Emails.objects.all()
    if source == 'sms':
        data_messages = SMSCDR.objects.all().order_by('sms_time')

    template = 'helpline/%s.html' % (source)
    return render(request, template,{'data_messages':data_messages})


def get_data_queues(queue=None):
    data = backend.get_data_queues()
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


@login_required
@json_view
def spy(request):
    channel = request.POST.get('channel', '')
    to_exten = request.POST.get('to_exten', '')
    r = backend.spy(channel, to_exten)
    return r


@login_required
@json_view
def whisper(request):
    channel = request.POST.get('channel', '')
    to_exten = request.POST.get('to_exten', '')
    r = backend.whisper(channel, to_exten)
    return r


@login_required
@json_view
def barge(request):
    channel = request.POST.get('channel', '')
    to_exten = request.POST.get('to_exten', '')
    r = backend.barge(channel, to_exten)
    return r


@login_required
@json_view
def hangup_call(request):
    channel = request.POST.get('channel', '')
    r = backend.hangup(channel)
    return r


@login_required
@json_view
def remove_from_queue(request):
    queue = request.POST.get('queue', '')
    agent = request.POST.get('agent', '')
    r = backend.remove_from_queue(agent, queue)
    return r

post_save.connect(report_save_handler, sender=Report)
