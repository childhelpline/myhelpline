# -*- coding: utf-8 -*-
"""Helpline views """

import os
import calendar

import time
from random import randint
import hashlib
import urllib
from itertools import tee

from datetime import timedelta, datetime, date, time as datetime_time

from nameparser import HumanName
import requests

from django.shortcuts import render, redirect
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.template.context_processors import csrf
from django.db.models import Avg
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models import Sum
from django.contrib.auth.views import login as django_login
from django.contrib.auth.views import logout as django_logout
from django.db.models.signals import post_save
from django.conf import settings
from django.utils.translation import gettext as _

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

from helpline.models import Report, HelplineUser,\
        Schedule, Case, Postcode,\
        Service, Hotdesk, Category, Clock,\
        MainCDR, Recorder, Address, Contact,\
        Messaging

from helpline.forms import QueueLogForm,\
        CallForm, DispositionForm, CaseSearchForm, MyAccountForm, \
        ReportFilterForm, QueuePauseForm

from helpline.qpanel.config import QPanelConfig
from helpline.qpanel.backend import Backend
if QPanelConfig().has_queuelog_config():
    from helpline.qpanel.model import queuelog_data_queue


cfg = QPanelConfig()
backend = Backend()


@login_required
def home(request):
    "Dashboard home"

    try:
        att = request.user.HelplineUser.get_average_talk_time()
        awt = request.user.HelplineUser.get_average_wait_time()
    except Exception as e:
        new = initialize_myaccount(request.user)
        return redirect("/helpline/#%s" % (e))

    dashboard_stats = get_dashboard_stats(request.user)
    status_count = get_status_count()
    case_search_form = CaseSearchForm()
    queue_form = QueueLogForm(request.POST)
    queue_pause_form = QueuePauseForm()

    return render(request, 'helpline/home.html',
                  {'dashboard_stats': dashboard_stats,
                   'att': att,
                   'awt': awt,
                   'case_search_form': case_search_form,
                   'queue_form': queue_form,
                   'queue_pause_form': queue_pause_form,
                   'status_count': status_count})


@login_required
def leta(request):
    """Return the login duration and ready duration"""
    login_duration = request.user.HelplineUser.get_login_duration()
    ready = request.user.HelplineUser.get_ready_duration()
    return render(request, 'helpline/leta.html',
                  {'ld': login_duration,
                   'ready': ready})


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

    else:
        telephone = None
        my_case = None

    response = JsonResponse({'my_case': my_case,
                             'telephone': telephone,
                             'type': my_case.hl_data if my_case else 0})
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
    return render(request, 'helpline/myaccount.html')


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
        queue_manager(agent.hl_key, request.session.get('extension'), 'queueleave')
        agent.save()

    except Exception as e:
        message = e

    return redirect("web_presence")


def queue_pause(request):
    """Pause Asterisk Queue member"""
    form = QueuePauseForm(request.POST)
    if form.is_valid():
        clock = Clock()
        clock.hl_key = request.user.HelplineUser.hl_key
        clock.hl_clock = form.cleaned_data.get('reason')
        # Hardcoded for tests
        # We should loop through all agent services in schedule
        clock.hl_service = 718874580
        clock.hl_time = int(time.time())
        clock.save()
        message = backend.pause_queue_member(
            queue='Q718874580',
            interface='%s' % (request.user.HelplineUser.hl_exten),
            paused=True
        )
        request.user.HelplineUser.hl_status = 'Pause'
        request.user.HelplineUser.save()
    else:
        message = "failed"

    return redirect("/helpline/#%s" % (message))


def queue_unpause(request):
    """Unpause Asterisk Queue member"""
    clock = Clock()
    clock.hl_key = request.user.HelplineUser.hl_key
    clock.hl_clock = "Unpause"
    clock.hl_service = 718874580
    clock.hl_time = int(time.time())
    clock.save()
    request.user.HelplineUser.hl_status = 'Available'
    request.user.HelplineUser.save()

    message = backend.pause_queue_member(
        queue='Q718874580',
        interface='SIP/8007',
        paused=False
    )
    return redirect("/helpline/#%s" % (message))


def walkin(request):
    """Render CallForm manualy."""
    form = CallForm()

    return render(request, 'helpline/walkin.html',
                  {'form': form})


def callform(request):
    """Render call form"""
    return render(request, 'helpline/callform.html')


def faq(request):
    """Render FAQ app"""
    return render(request, 'helpline/callform.html')


@login_required
def reports(request, report, casetype='Call'):
    """Handle report rendering"""
    query = request.GET.get('q', '')
    datetime_range = request.GET.get("datetime_range")
    agent = request.GET.get("agent")
    category = request.GET.get("category", "")
    form = ReportFilterForm(request.GET)
    dashboard_stats = get_dashboard_stats(request.user)

    sort = request.GET.get('sort')
    report_title = {
        'performance': _('Performance Reports'),
        'counsellor': _('Counsellor Reports'),
        'case': _('Case Reports'),
        'call': _('Call Reports'),
        'service': _('Service Reports')
    }

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

    return render(request, 'helpline/reports.html', { #dashboardreports
        'title': report_title.get(report),
        'report': report,
        'form': form,
        'datetime_range': datetime_range,
        'dashboard_stats': dashboard_stats,
        'table': table,
        'query': query})


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
    data = backend.add_to_queue(
        agent="SIP/%s" % (extension),
        queue='Q718874580',
        member_name=user.get_full_name()
    )
    return data


@login_required
def my_forms(request, form_name):
    """Handle Walkin and CallForm POST and GET Requests"""
    message = ''

    if(form_name == 'walkin'):
        loaded_form = {'url':'https://enketo.bitz-itc.com/i/::4n1oArZH',
                        'name':'walkin'}
    elif(form_name == 'qa'):
        loaded_form = {'url':'https://enketo.bitz-itc.com/i/::Bkyb35PE',
                        'name':'qa'}


    initial = {}
    if request.method == 'GET':
        case_number = request.GET.get('case')
        #return redirect('/ona/' + request.user.username + '/forms/Case_Form/enter-data')#"Cheru: %s",form_name)
        # Check if we're looking for a case.
        if case_number:
            my_case = Case.objects.get(hl_case=case_number)
            report, contact, address = get_case_info(case_number)
            initial = {
                'case_number': case_number,
                'phone_number': contact.hl_contact if contact else '',
                'calls': contact.hl_calls if contact else '',
                'caller_name': address.hl_names if address else '',
                'company': address.hl_company if address else '',
                'gender': address.hl_gender if address else '',
                'region': address.hl_address3 if address else '',
                'language': address.hl_language if address else '',
                'district': address.hl_address2 if address else '',
                'address': address.hl_address1 if address else '',
                'current': address.hl_current if address else '',
                'occupation': address.hl_headoccupation if address else '',
                'age_group': address.hl_ageclass if address else '',
                'email': address.hl_email if address else '',
                'data': my_case.hl_data if my_case else '',
                'comment': my_case.hl_details if my_case else '',
                'notes': my_case.hl_notes if my_case else '',
                'partner': my_case.hl_registry if my_case else '',
                'category': my_case.hl_acategory if my_case else '',
                'referred_from': my_case.isrefferedfrom if my_case else '',
                'sub_category': my_case.hl_subcategory if my_case else '',
                'sub_sub_category': my_case.hl_subsubcat if my_case else '',
                'case_status': report.casestatus if report else '',
                'case_type': my_case.hl_type if my_case else '',
                'escalate_to': my_case.hl_escalateto if my_case else '',
                'date_of_birth': address.hl_dob if address else '',
                'national_registration_card': address.hl_adultnumber if address else '',
                'physical_address': address.hl_address4 if address else '',

            }
            case_history = Report.objects.filter(telephone=contact.hl_contact).order_by('-case')
            case_history_table = CaseHistoryTable(case_history)
            try:
                case_history_table.paginate(page=request.GET.get('page', 1), per_page=10)
            except Exception as e:
                # Ignore pagination error.
                pass
        else:
            initial = {}
            my_case = None

            # Case history table will display all records when initialized.
            case_history = Report.objects.all().order_by('-case_id')
            report, contact, address = (None, None, None)
            case_history_table = CaseHistoryTable(case_history)
            case_history_table.paginate(page=request.GET.get('page', 1), per_page=10)

        initial_disposition = {'case_number': case_number,
                               'disposition': my_case.hl_disposition
                               if my_case else ''}
        disposition_form = DispositionForm(initial=(initial_disposition))

        form = CallForm(initial=initial)

    elif request.method == 'POST':
        contact, address = (None, None)
        # Process forms differently.

        if form_name == 'call':
            form = CallForm(request.POST)
        elif form_name == 'walkin':
            form = CallForm(request.POST)

        if form.is_valid():
            case_number = form.cleaned_data.get('case_number')
            if case_number:
                my_case = Case.objects.get(hl_case=case_number)
                report, contact, address = get_case_info(case_number)
                case_history = Report.objects.filter(
                    telephone=contact.hl_contact).order_by('-case')
                case_history_table = CaseHistoryTable(case_history)
                try:
                    case_history_table.paginate(page=request.GET.get('page', 1), per_page=10)
                except Exception as e:
                    # Do not paginate if there is an error
                    pass
            else:
                my_case = Case()
                my_case.hl_data = form_name
                my_case.hl_counsellor = request.user.HelplineUser.hl_key
                my_case.popup = 'Done'
                my_case.hl_time = int(time.time())
                my_case.hl_status = form.cleaned_data.get('case_status')
                my_case.hl_acategory = form.cleaned_data.get('category')
                my_case.hl_notes = form.cleaned_data.get('notes')
                my_case.hl_type = form.cleaned_data.get('case_type')
                my_case.hl_subcategory = form.cleaned_data.get('sub_category')
                my_case.hl_subsubcat = form.cleaned_data.get('sub_sub_category')
                my_case.isrefferedfrom = form.cleaned_data.get('referred_from')
                my_case.hl_details = form.cleaned_data.get('comment')

                my_case.hl_priority = 'Non-Critical'
                my_case.hl_creator = request.user.HelplineUser.hl_key
                my_case.save()
                address, address_created = Address.objects.get_or_create(hl_key=my_case.hl_key)

                contact, contact_created = Contact.objects.get_or_create(hl_key=my_case.hl_key,
                                                                            hl_type='Cell Phone',
                                                                            hl_calls=0,
                                                                            hl_status='Available',
                                                                            hl_time=int(time.time()))
                now = datetime.now()
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

            address.hl_names = form.cleaned_data['caller_name']
            address.hl_gender = form.cleaned_data.get('gender')
            address.hl_address1 = form.cleaned_data.get('address')
            address.hl_email = form.cleaned_data.get('email')
            address.hl_address4 = form.cleaned_data.get('physical_address')
            address.hl_address3 = form.cleaned_data.get('region')
            address.hl_language = form.cleaned_data.get('language')
            address.hl_company = form.cleaned_data.get('company')
            contact.hl_contact = form.cleaned_data['phone_number']
            report.callernames = form.cleaned_data['caller_name']
            report.casearea = form.cleaned_data.get('address')
            report.casearea = form.cleaned_data.get('address')
            report.telephone = form.cleaned_data['phone_number']
            report.counsellorname = request.user.username
            report.casetype = form_name

            report.casestatus = form.cleaned_data['case_status']
            report.escalatename = form.cleaned_data.get('escalate_to')
            my_case.hl_status = form.cleaned_data.get('case_status')
            my_case.hl_acategory = form.cleaned_data.get('category')
            my_case.hl_notes = form.cleaned_data.get('notes')
            my_case.hl_details = form.cleaned_data['comment']
            my_case.isrefferedfrom = form.cleaned_data.get('referred_from')
            my_case.hl_type = form.cleaned_data.get('case_type')
            my_case.hl_subcategory = form.cleaned_data.get('sub_category')
            my_case.hl_subsubcat = form.cleaned_data.get('sub_sub_category')
            my_case.hl_escalateto = form.cleaned_data.get('escalate_to')

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
        request, 'helpline/my_form.html', {
            'form': form,
            'contact': contact if contact else None,
            'initial': initial,
            'disposition_form': disposition_form,
            'case_history_table': case_history_table,
            'form_name': form_name,
            'message': message,
            'loaded_form':loaded_form}
    )


class DashboardTable(tables.Table):
    """Where most of the dashboard reporting happens"""
    casetype = tables.TemplateColumn("<b>{{ record.get_call_type }}</b>",
                                     verbose_name="Call Type")
    case_id = tables.TemplateColumn(
        '<a href="{{ record.get_absolute_url }}">{{record.case }}</a>')
    telephone = tables.TemplateColumn(
        '<a href="sip:{{record.telephone}}">{{record.telephone}}</a>')
    user_id = tables.TemplateColumn("{{ record.user }}", verbose_name="Agent")
    service_id = tables.TemplateColumn("{{ record.service }}",
                                       verbose_name="Service")

    export_formats = ['csv', 'xls']

    class Meta:
        model = Report
        attrs = {'class': 'table table-bordered table-striped dataTable',
                 'id': 'report_table'}
        unlocalise = ('holdtime', 'walkintime', 'talktime', 'callstart')
        fields = {'casetype', 'case_id', 'telephone', 'calldate',
                  'service_id', 'callernames', 'user_id',
                  'calldate', 'callstart', 'callend', 'talktime', 'holdtime',
                  'calltype', 'disposition', 'casestatus'}

        sequence = ('casetype', 'case_id', 'calldate', 'callstart',
                    'callend', 'user_id', 'telephone',
                    'service_id', 'talktime', 'holdtime', 'calltype',
                    'disposition', 'casestatus')


class WebPresenceTable(tables.Table):
    """Web presence table"""
    class Meta:
        model = HelplineUser
        attrs = {'class': 'table table-bordered table-striped dataTable'}


class CaseHistoryTable(tables.Table):
    """Show related Case form contact"""
    case = tables.TemplateColumn('<a href="{{ record.get_absolute_url }}">{{record.case }}</a>')
    class Meta:
        model = Report
        attrs = {'class': 'table table-bordered table-striped dataTable'}
        fields = {'case', 'counsellorname', 'calldate', 'calltype'}
        sequence = ('case', 'counsellorname', 'calldate', 'calltype')

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
        os.environ['TZ'] = 'Africa/Nairobi'
        time.tzset()
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value))


class AgentColumn(tables.Column):
    """Return the agent nick from the agent key"""
    def render(self, value):
        # Agent does not have a nickname
        # Or does not extist.
        try:
            return HelplineUser.objects.get(hl_key=value).hl_nick
        except Exception as e:
            return value


class ServiceColumn(tables.Column):
    """Show service, customized template"""
    def render(self, value):
        return Service.objects.get(hl_key=value).hl_service


class AgentSessionTable(tables.Table):
    """Show agent activity"""
    hl_key = AgentColumn()
    hl_time = ReceievedColumn()
    hl_service = ServiceColumn()

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
def save_call_form(request):
    """Save call form returns json status"""
    form = CallForm(request.POST or None)
    if form.is_valid():
        # form.save()
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
    now_string = datetime.now().strftime('%m/%d/%Y %I:%M %p')
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
    closed_cases = Case.objects.filter(
        hl_time__gt=midnight).filter(hl_status__exact='Close')
    open_cases = Case.objects.filter(
        hl_time__gt=midnight).filter(hl_status__exact='Pending')
    referred_cases = Case.objects.filter(
        hl_time__gt=midnight).filter(hl_status__exact='Escalate')

    total_sms = Messaging.objects.filter(hl_time__gt=midnight)

    # Filter out stats for non supervisor user.
    if user.HelplineUser.hl_role != 'Supervisor':
        total_calls = total_calls.filter(user=user)
        missed_calls = missed_calls.filter(hl_key=user.HelplineUser.hl_key)
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
            clock = clock.filter(hl_key__exact=agent)
            filter_query['agent'] = agent
        # Filter actions. Queue Join etc.
        if query:
            clock = clock.filter(hl_clock__exact=query)
            filter_query['q'] = query

        return AgentSessionTable(clock)

    service = settings.DEFAULT_SERVICE
    reports = Report.objects.all()
    cdr = MainCDR.objects.all()
    user = HelplineUser.objects.get(hl_key__exact=agent).user if agent else None

    calltype = {'answeredcalls': 'Answered',
                'abandonedcalls': 'Abandoned',
                'voicemail': 'Voicemail'}

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
            reports = reports.filter(casetype__exact=casetype)

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
            Q(callernames__icontains=query) |
            Q(casestatus__icontains=query) |
            Q(counsellorname__icontains=query)
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

    total_answered = reports.filter(queuename__exact=service,
                                    calltype__exact='Answered').count()
    total_abandoned = reports.filter(queuename__exact=service,
                                     calltype__exact='Abandoned').count()
    total_voicemail = reports.filter(queuename__exact=service,
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
def sources(request,csource = ''):
    """Display statistics for the wall board"""
    #sms_list = get_sms_list(request.user)
   # week_dashboard_stats = get_dashboard_stats(request.user, interval='weekly')
    ln = 'helpline/' + csource + '.html'
    return render(request,ln)#,
                  #{'sls_list': sms_list})


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
@json_view
def queue(request, name=None):
    data = get_data_queues(name)
    return {'data': data}
