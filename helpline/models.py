# -*- coding: utf-8 -*-
"""Helpline Models"""

from __future__ import unicode_literals
from datetime import timedelta, datetime, date, time as datetime_time
import time
import os
import re

from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg
from django.utils import timezone
from django.apps import apps
from django.utils.translation import ugettext_lazy

from helpdesk.models import Ticket


class Address(models.Model):
    hl_key = models.IntegerField(unique=True, primary_key=True)
    hl_title = models.CharField(max_length=25, blank=True, null=True)
    hl_type = models.CharField(max_length=9, blank=True, null=True)
    hl_names = models.CharField(max_length=500, blank=True, null=True)
    hl_gender = models.CharField(max_length=7, blank=True, null=True)
    hl_ageclass = models.CharField(max_length=7, blank=True, null=True)
    hl_age = models.IntegerField(blank=True, null=True)
    hl_dob = models.DateField(blank=True, null=True)
    hl_yeardob = models.TextField(blank=True, null=True)
    hl_monthdob = models.SmallIntegerField(blank=True, null=True)
    hl_datedob = models.SmallIntegerField(blank=True, null=True)
    hl_language = models.CharField(max_length=250, blank=True, null=True)
    hl_relation = models.CharField(max_length=100, blank=True, null=True)
    hl_address1 = models.CharField(max_length=250, blank=True, null=True)
    hl_address2 = models.CharField(max_length=250, blank=True, null=True)
    hl_address3 = models.CharField(max_length=100, blank=True, null=True)
    hl_address4 = models.CharField(max_length=100, blank=True, null=True)
    hl_country = models.CharField(max_length=250, blank=True, null=True)
    hl_email = models.CharField(max_length=100, blank=True, null=True)
    hl_householdtype = models.CharField(max_length=13)
    hl_childrenumber = models.IntegerField(blank=True, null=True)
    hl_adultnumber = models.IntegerField(blank=True, null=True)
    hl_headoccupation = models.CharField(max_length=100, blank=True, null=True)
    hl_school = models.CharField(max_length=250, blank=True, null=True)
    hl_company = models.CharField(max_length=250, blank=True, null=True)
    hl_schooltype = models.CharField(max_length=100, blank=True, null=True)
    hl_class = models.CharField(max_length=50, blank=True, null=True)
    hl_attendance = models.CharField(max_length=12, blank=True, null=True)
    hl_attendancereason = models.TextField(blank=True, null=True)
    hl_schaddr = models.CharField(max_length=250, blank=True, null=True)
    hl_homerole = models.CharField(max_length=7, blank=True, null=True)
    hl_latitude = models.FloatField(blank=True, null=True)
    hl_longitude = models.FloatField(blank=True, null=True)
    hl_religion = models.CharField(max_length=100, blank=True, null=True)
    hl_career = models.CharField(max_length=13, blank=True, null=True)
    hl_shl_evel = models.CharField(max_length=11, blank=True, null=True)
    hl_health = models.CharField(max_length=12, blank=True, null=True)
    hl_disabled = models.CharField(max_length=3, blank=True, null=True)
    hl_notes = models.TextField(blank=True, null=True)
    hl_created = models.IntegerField(blank=True, null=True)
    hl_creator = models.IntegerField(blank=True, null=True)
    hl_deletedate = models.IntegerField(blank=True, null=True)
    hl_deleteby = models.IntegerField(blank=True, null=True)
    hl_deleted = models.IntegerField(blank=True, null=True)
    hl_current = models.SmallIntegerField(blank=True, null=True)
    hl_contact = models.IntegerField(blank=True, null=True)
    hl_time = models.IntegerField(blank=True, null=True)
    hl_hiv = models.CharField(max_length=8, blank=True, null=True)

    def __unicode__(self):
        return self.hl_names or u''


class Case(models.Model):
    hl_case = models.AutoField(primary_key=True)
    hl_key = models.IntegerField()
    hl_callerkey = models.IntegerField(blank=True, null=True)
    hl_victimkey = models.IntegerField(blank=True, null=True)
    hl_unique = models.CharField(unique=True, max_length=20, blank=True, null=True)
    hl_type = models.CharField(max_length=250, blank=True, null=True)
    hl_subcategory = models.CharField(max_length=250,blank=True,null=True)
    hl_subsubcat = models.CharField(max_length=100, verbose_name='Sub-subcategory', blank=True, null=True)
    hl_victim = models.CharField(max_length=3, blank=True, null=True)
    hl_culprit = models.IntegerField(blank=True,null=True)
    hl_status = models.CharField(max_length=250, blank=True, null=True)
    hl_priority = models.CharField(max_length=250, blank=True, null=True)
    hl_disposition = models.CharField(max_length=250, blank=True, null=True)
    hl_creator = models.IntegerField(blank=True, null=True)
    hl_counsellor = models.IntegerField(blank=True, null=True)
    hl_supervisor = models.IntegerField(blank=True, null=True)
    hl_escalateto = models.CharField(max_length=10, blank=True, null=True)
    hl_caseworker = models.IntegerField(blank=True,null=True)
    hl_justice = models.CharField(max_length=13,blank=True,null=True)
    hl_victimassessment = models.CharField(max_length=13,blank=True,null=True)
    hl_data = models.CharField(max_length=9, blank=True, null=True)
    hl_notes = models.CharField(max_length=50, blank=True,null=True)
    hl_abused = models.CharField(max_length=5,blank=True,null=True)
    hl_anotes = models.TextField(blank=True,null=True)
    hl_acategory = models.CharField(max_length=50,blank=True,null=True)
    hl_hiv = models.CharField(max_length=7,blank=True,null=True)
    isrefferedfrom = models.CharField(max_length=250,blank=True,null=True)
    hl_details = models.TextField(blank=True,null=True)
    hl_popup = models.CharField(max_length=6,blank=True,null=True)
    hl_registry = models.IntegerField(blank=True,null=True)
    hl_time = models.IntegerField(blank=True, null=True)


class CaseTrail(models.Model):
    hl_case = models.ForeignKey(Case, on_delete=models.CASCADE)
    hl_status = models.CharField(max_length=8)
    hl_to = models.CharField(max_length=10)
    hl_userkey = models.IntegerField()
    hl_service = models.CharField(max_length=11)
    hl_subcategory = models.CharField(max_length=250)
    hl_servicedesc = models.TextField()
    hl_details = models.TextField()
    hl_editby = models.IntegerField()
    hl_time = models.CharField(max_length=11)


class Category(models.Model):
    hl_core = models.IntegerField(verbose_name='Core ID', default=1)
    hl_category = models.CharField(max_length=100, verbose_name='Category')
    hl_subcategory = models.CharField(max_length=100, verbose_name='Subcategory')
    hl_subsubcat = models.CharField(max_length=100, verbose_name='Sub-subcategory', blank=True, null=True)

    def get_subcategory(self):
        return Category.objects.filter(hl_category=self.hl_category)

    def get_sub_subcategory(self):
        return Category.objects.filter(hl_category=self.hl_subsubcat)

    def __unicode__(self):
        return self.hl_category


class Clock(models.Model):
    hl_key = models.IntegerField(verbose_name='Agent')
    hl_clock = models.CharField(verbose_name='Action',  max_length=50)
    hl_service = models.IntegerField(verbose_name='Service')
    hl_time = models.IntegerField(verbose_name='Time')

    def __unicode__(self):
        return self.hl_clock

class ClockBit(models.Model):
    hl_key = models.IntegerField()
    hl_clock = models.CharField(max_length=11)
    hl_service = models.IntegerField()
    hl_time = models.IntegerField()


class Contact(models.Model):
    hl_key = models.IntegerField(primary_key=True)
    hl_contact = models.CharField(max_length=250)
    hl_parent = models.IntegerField(blank=True, null=True)
    hl_type = models.CharField(max_length=12, blank=True, null=True)
    hl_calls = models.IntegerField(blank=True, null=True)
    hl_status = models.CharField(max_length=10, blank=True, null=True)
    hl_time = models.IntegerField(blank=True, null=True)

    class Meta:
        unique_together = (('hl_key', 'hl_contact'),)

    def __unicode__(self):
        return self.hl_contact

    def get_name(self):
        return Address.objects.get(hl_key=self.hl_key).hl_names

class Country(models.Model):
    hl_category = models.CharField(max_length=100)
    hl_code = models.CharField(max_length=2)
    hl_country = models.CharField(max_length=250)
    hl_phone = models.IntegerField()


class Dialect(models.Model):
    hl_category = models.CharField(max_length=100, blank=True, null=True)
    hl_dialect = models.CharField(max_length=100, verbose_name="Language")
    hl_status = models.IntegerField(blank=True, null=True)

    class Meta:
        verbose_name = 'Language'
        verbose_name_plural = 'Languages'

    def __unicode__(self):
        return self.hl_dialect


class Hotdesk(models.Model):
    """A hotdesk references the workstation an agent seats."""
    SIP = 'SIP'
    AVAILABLE = 'Available'
    UNAVAILABLE = 'Unavailable'
    EXTENSION_TYPE_CHOICES = (
        (SIP, 'SIP'),
    )
    AVAILABILITY_CHOICES = (
        (AVAILABLE, 'Available'),
        (UNAVAILABLE, 'Unavailable'),
    )
    extension = models.IntegerField(unique=True, primary_key=True)
    extension_type = models.CharField(
        max_length=6,
        choices=EXTENSION_TYPE_CHOICES,
        default=SIP
    )

    jabber = models.CharField(
        max_length=100,
        blank=True, null=True
    )
    status = models.CharField(
        max_length=11,
        choices=AVAILABILITY_CHOICES,
        default=UNAVAILABLE
    )
    agent = models.IntegerField(
        blank=True, null=True
    )

    def __unicode__(self):
        return str(self.extension)

    def update_hotdesk(self, status, extension):
        """Update extension status on hotdesk"""
        self.status = status
        self.extension = extension
        self.save()

class IMregistry(models.Model):
    hl_index = models.AutoField(primary_key=True)
    hl_chat = models.CharField(max_length=300)
    hl_mandatory = models.CharField(max_length=300)
    hl_path = models.CharField(max_length=300)
    hl_type = models.IntegerField()
    hl_table = models.CharField(max_length=100)


class MainCDR(models.Model):
    hl_unique = models.CharField(unique=True, max_length=32)
    hl_key = models.IntegerField()
    hl_start = models.BigIntegerField()
    hl_end = models.IntegerField()
    hl_duration = models.IntegerField()
    hl_queue = models.IntegerField()
    hl_agent = models.IntegerField()
    hl_bridge = models.CharField(max_length=100)
    hl_holdtime = models.IntegerField()
    hl_talktime = models.IntegerField()
    hl_vmail = models.CharField(max_length=7)
    hl_app = models.CharField(max_length=9)
    hl_status = models.CharField(max_length=11)
    hl_time = models.IntegerField()


class MatrixQA(models.Model):
    hl_type = models.CharField(max_length=5)
    hl_item = models.CharField(max_length=250)
    hl_data = models.TextField()
    hl_cycle = models.IntegerField()
    hl_menu = models.IntegerField()
    hl_score1 = models.CharField(max_length=100)
    hl_score2 = models.CharField(max_length=100)
    hl_score3 = models.CharField(max_length=100)
    hl_score4 = models.CharField(max_length=100)
    hl_mark1 = models.IntegerField()
    hl_mark2 = models.IntegerField()
    hl_mark3 = models.IntegerField()
    hl_mark4 = models.IntegerField()


class MenuLog(models.Model):
    hl_user = models.IntegerField()
    hl_key = models.IntegerField()
    hl_status = models.IntegerField()
    hl_menu = models.CharField(max_length=100)
    hl_path = models.CharField(max_length=100)
    hl_query = models.TextField()
    hl_data = models.TextField()
    hl_time = models.IntegerField()


class Messaging(models.Model):
    hl_service = models.CharField(max_length=100, verbose_name='Service')
    hl_contact = models.CharField(max_length=25, verbose_name='Contact')
    hl_key = models.IntegerField(verbose_name='Key')
    hl_type = models.CharField(max_length=6, verbose_name='Type')
    hl_status = models.CharField(max_length=7, verbose_name='Status')
    hl_staff = models.IntegerField(verbose_name='Staff', blank=True, null=True)
    hl_content = models.TextField(verbose_name='Content')
    hl_time = models.IntegerField(verbose_name='Time')

    def get_formatted_time(self):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.hl_time))

    def __unicode__(self):
        return str(self.hl_contact)

class Offered(models.Model):
    hl_case = models.IntegerField(unique=True)
    hl_service = models.CharField(max_length=250)
    hl_projectname = models.CharField(max_length=6)
    hl_subcategory = models.CharField(max_length=250)
    hl_victimdev = models.CharField(max_length=13)
    hl_servicespects = models.CharField(max_length=50)
    hl_saction = models.IntegerField()
    hl_expenses = models.IntegerField()
    hl_expensesto = models.CharField(max_length=100)
    hl_remarks = models.TextField()
    hl_assesscomment = models.TextField()
    hl_time = models.IntegerField()


class Partner(models.Model):
    tempid = models.IntegerField(blank=True, null=True)
    keyservices = models.CharField(max_length=100, blank=True, null=True)
    referralpartner = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    town = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    addresslocation = models.CharField(max_length=100, blank=True, null=True)
    contactperson = models.CharField(max_length=100, blank=True, null=True)
    contactpersontitle = models.CharField(max_length=100, blank=True, null=True)
    contactpersonemail = models.CharField(max_length=100, blank=True, null=True)
    contact_personphone = models.CharField(max_length=100, blank=True, null=True)
    contact_personofficephone = models.CharField(max_length=100, blank=True, null=True)
    contactpersonofficeemail = models.CharField(max_length=100, blank=True, null=True)
    contactpersonofficefax = models.CharField(max_length=100, blank=True, null=True)
    website = models.CharField(max_length=100, blank=True, null=True)
    pobox = models.CharField(max_length=100, blank=True, null=True)
    openinghours = models.CharField(max_length=100, blank=True, null=True)
    referralneeded = models.CharField( max_length=100, blank=True, null=True)
    referralpoint = models.CharField(max_length=100, blank=True, null=True)
    counselling = models.CharField(max_length=100, blank=True, null=True)
    shelter = models.CharField(max_length=100, blank=True, null=True)
    afterschool = models.CharField(max_length=100, blank=True, null=True)
    soupkitchen = models.CharField(max_length=100, blank=True, null=True)
    otherservicesinfo = models.CharField(max_length=100, blank=True, null=True)
    counsellornotes = models.TextField(blank=True, null=True, verbose_name='Notes')
    affiliations = models.TextField(blank=True, null=True)


class Postcode(models.Model):
    keyid = models.IntegerField(unique=True,primary_key=True)
    address2 = models.CharField(max_length=100)
    address3 = models.CharField(max_length=100)
    addresstype = models.CharField(max_length=100)

    def __unicode__(self):
        return self.address2

class QALog(models.Model):
    hl_case = models.ForeignKey(Case, on_delete=models.CASCADE)
    hl_key = models.IntegerField()
    hl_case = models.IntegerField()
    hl_supervisor = models.IntegerField()
    hl_counsellor = models.IntegerField()
    hl_total = models.IntegerField()
    hl_grq1 = models.IntegerField()
    hl_lsq1 = models.IntegerField()
    hl_lsq2 = models.IntegerField()
    hl_akq1 = models.IntegerField()
    hl_akq2 = models.IntegerField()
    hl_akq3 = models.IntegerField()
    hl_akq4 = models.IntegerField()
    hl_akq5 = models.IntegerField()
    hl_paq1 = models.IntegerField()
    hl_paq2 = models.IntegerField()
    hl_paq3 = models.IntegerField()
    hl_req1 = models.IntegerField()
    hl_req2 = models.IntegerField()
    hl_req3 = models.IntegerField()
    hl_req4 = models.IntegerField()
    hl_req5 = models.IntegerField()
    hl_req6 = models.IntegerField()
    hl_req7 = models.IntegerField()
    hl_req8 = models.IntegerField()
    hl_req9 = models.IntegerField()
    hl_req10 = models.IntegerField()
    hl_hpq1 = models.IntegerField()
    hl_hpq2 = models.IntegerField()
    hl_usq1 = models.IntegerField()
    hl_csq1 = models.IntegerField()
    hl_csq2 = models.IntegerField()
    hl_feedback = models.TextField()
    hl_time = models.IntegerField()
    hl_what = models.CharField(max_length=6, blank=True, null=True)


class Recorder(models.Model):
    hl_case = models.ForeignKey(Case, on_delete=models.CASCADE)
    hl_key = models.IntegerField(blank=True, null=True)
    hl_type = models.CharField(max_length=9, blank=True, null=True)
    hl_service = models.IntegerField(blank=True, null=True)
    hl_unique = models.CharField(max_length=25, blank=True, null=True)
    hl_status = models.CharField(max_length=7, blank=True, null=True)
    hl_staff = models.IntegerField(blank=True, null=True)
    hl_time = models.IntegerField(blank=True, null=True)


class Registry(models.Model):
    hl_key = models.IntegerField(unique=True)
    hl_names = models.CharField(max_length=255)
    hl_age = models.CharField(max_length=7)
    hl_gender = models.CharField(max_length=7)
    hl_relation = models.CharField(max_length=100)
    hl_address = models.CharField(max_length=500)
    hl_orient = models.CharField(max_length=8)
    hl_cases = models.IntegerField()
    hl_data = models.TextField()
    hl_status = models.CharField(max_length=7)
    hl_healthstatus = models.CharField(max_length=100)
    hl_proffession = models.CharField(max_length=200)
    hl_maritalstatus = models.CharField(max_length=8)
    hl_householdshared = models.CharField(max_length=3)
    hl_time = models.IntegerField()
    hl_hivrelated = models.IntegerField()


class Report(models.Model):
    """Main report table."""
    hl_case = models.ForeignKey(Case, on_delete=models.CASCADE)
    caseid = models.IntegerField(unique=True, primary_key=True,
                                 verbose_name='Case ID')
    calldate = models.CharField(max_length=250, verbose_name='Call Date',
                                blank=True, null=True)
    queuename = models.TextField(verbose_name='Queue Name',
                                 blank=True, null=True)
    telephone = models.CharField(max_length=20, verbose_name='Telephone',
                                 blank=True, null=True)
    callernames = models.CharField(max_length=250, verbose_name='Caller Names',
                                   blank=True, null=True)
    casearea = models.CharField(max_length=13, verbose_name='Case Area',
                                blank=True, null=True)
    counsellorname = models.TextField(verbose_name='Agent Name',
                                      blank=True, null=True)
    agentchannel = models.CharField(max_length=100,
                                    verbose_name='Agent Channel',
                                    blank=True, null=True)
    callstart = models.TimeField(verbose_name='Call Start',
                                 blank=True, null=True)
    callend = models.TimeField(verbose_name='Call End',
                               blank=True, null=True)
    talktime = models.TimeField(verbose_name='Talk Time',
                                blank=True, null=True)
    holdtime = models.TimeField(verbose_name='Hold Time',
                                blank=True, null=True)
    walkintime = models.TimeField(verbose_name='Walkin Time',
                                  blank=True, null=True)
    calltype = models.CharField(max_length=11, verbose_name='Call Type',
                                blank=True, null=True)
    casestatus = models.CharField(max_length=16, verbose_name='Call Status',
                                  blank=True, null=True)
    escalatename = models.CharField(max_length=250,
                                    verbose_name='Escalated Name',
                                    blank=True, null=True)
    casetype = models.CharField(max_length=6, verbose_name='Case Type',
                                blank=True, null=True)
    hl_time = models.IntegerField(verbose_name='Time', blank=True, null=True)
    qa = models.CharField(max_length=3, verbose_name='QA',
                          blank=True, null=True)

    def __unicode__(self):
        return str(self.caseid)

    def get_disposition(self):
        return Case.objects.get(hl_case=self.caseid).hl_disposition

    def get_notes(self):
        return Case.objects.get(hl_case=self.caseid).hl_notes

    def get_details(self):
        return Case.objects.get(hl_case=self.caseid).hl_details

    def get_category(self):
        """ Get case type related to a report"""
        return Case.objects.get(hl_case=self.caseid).hl_type

    def get_sub_category(self):
        """ Get case type sub-category related to a report"""
        return Case.objects.get(hl_case=self.caseid).hl_subcategory

    def get_sub_sub_category(self):
        """ Get case type sub sub-category related to a report"""
        return Case.objects.get(hl_case=self.caseid).hl_subsubcat

    def get_referred_from(self):
        """ Get referred from."""
        return Case.objects.get(hl_case=self.caseid).isrefferedfrom

    def get_case_type(self):
        """ Get casetype."""
        return Case.objects.get(hl_case=self.caseid).hl_type

    def get_call_type(self):
        """ Get casetype."""
        if self.casetype.lower() == "call":
            return "Inbound"
        elif self.casetype.lower() == "voicmail":
            return "Voicemail"
        else:
            return "Outbound"

    def get_case_category(self):
        """ Get case category."""
        return Case.objects.get(hl_case=self.caseid).hl_acategory

    def get_case_subcategory(self):
        """ Get case subcategory."""
        return Case.objects.get(hl_case=self.caseid).hl_subcategory

    def get_business_portfolio(self):
        """ Get case subcategory."""
        return Case.objects.get(hl_case=self.caseid).business_portfolio

    def get_case_key(self):
        """ Get case key."""
        return Case.objects.get(hl_case=self.caseid).hl_key

    def get_case_address(self):
        """ Get case Address."""
        return Address.objects.get(hl_key=self.get_case_key())

    def get_case_gender(self):
        """ Get case gender."""
        return Address.objects.get(hl_key=self.get_case_key()).hl_gender

    def get_adultnumber(self):
        """ Get nrc."""
        return str(Address.objects.get(hl_key=self.get_case_key()).hl_adultnumber)

    def get_email_address(self):
        """ Get email address."""
        return Address.objects.get(hl_key=self.get_case_key()).hl_email

    def get_dob(self):
        """ Get date of birth."""
        return Address.objects.get(hl_key=self.get_case_key()).hl_dob

    def get_csat_comment(self):
        """ Get poll results."""
        csat_vote = apps.get_model('polls', 'Vote')
        csat = csat_vote.objects.get(contact=self.get_case_key())
        return csat.comment

    def get_csat(self):
        """ Get poll results."""
        csat_vote = apps.get_model('polls', 'Vote')
        csat = csat_vote.objects.get(contact=self.get_case_key())
        return csat.choice

    def get_ticket(self):
        """ Get date of birth."""
        ticket = Ticket.objects.filter(title__icontains="case %s." % (self.caseid))
        return ticket.order_by("modified")[0] if ticket else None

    def get_absolute_url(self):
        """Calculate the canonical URL for Report."""
        # Django 1.10 breaks reverse imports.
        try:
            from django.urls import reverse
        except Exception as e:
            from django.core.urlresolvers import reverse

        return reverse('my_forms', args=[self.casetype.lower() if self.casetype else "call"]) + "?case=%s" % str(self.caseid)


class Role(models.Model):
    hl_role = models.CharField(max_length=100)
    hl_context = models.CharField(max_length=100)
    hl_status = models.IntegerField()
    hl_count = models.IntegerField()
    hl_time = models.IntegerField()


class Schedule(models.Model):
    hl_key = models.IntegerField()
    hl_service = models.IntegerField()
    hl_queue = models.IntegerField()
    hl_status = models.CharField(max_length=7)

    def __unicode__(self):
        return str(self.hl_key)

class Search(models.Model):
    hl_word = models.CharField(unique=True, max_length=100)
    hl_path = models.CharField(max_length=100)
    hl_menu = models.CharField(max_length=100)
    hl_service = models.CharField(max_length=100)


class Service(models.Model):
    """Identifies a queue that agents can be assigned"""
    extension = models.CharField(unique=True, max_length=100)
    name = models.CharField(max_length=255)
    queue = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):
        return self.name

class SMSCDR(models.Model):
    sender = models.CharField(max_length=30)
    receiver = models.CharField(max_length=30)
    msg = models.CharField(max_length=320, blank=True, null=True)
    time = models.DateTimeField(db_column='Time', blank=True, null=True)
    uniqueid = models.CharField(max_length=50)
    received = models.IntegerField()
    processing = models.IntegerField()
    processing_by = models.IntegerField()
    dateprocessed = models.DateTimeField()
    processed_by = models.IntegerField()
    link_id = models.CharField(max_length=300)


class System(models.Model):
    hl_system = models.CharField(unique=True, max_length=100)
    hl_data = models.CharField(max_length=100)


class HelplineUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='HelplineUser')
    hl_key = models.IntegerField(unique=True, primary_key=True,
                                 verbose_name='Key', help_text='Autogenerated')
    hl_auth = models.IntegerField(verbose_name='Auth',
                                  help_text='Autogenerated Four digit numeric number e.g. 1973.')
    hl_pass = models.CharField(max_length=500,
                               verbose_name='PIN', help_text='Four digit numeric PIN')
    hl_exten = models.CharField(max_length=55,
                                blank=True, null=True, verbose_name='Exten', help_text='Agent Softphone extension.')
    hl_jabber = models.CharField(max_length=500,
                                 blank=True, null=True, verbose_name='Jabber', help_text='IM username.')
    hl_status = models.CharField(max_length=11, blank=True, null=True,verbose_name='Status')
    hl_calls = models.IntegerField(blank=True, null=True,verbose_name='Total Calls')
    hl_email = models.CharField(max_length=500, blank=True, null=True,verbose_name='Email')
    hl_names = models.CharField(max_length=250, blank=True, null=True,verbose_name='Names')
    hl_nick = models.CharField(max_length=100, blank=True, null=True,verbose_name='Nick')
    hl_avatar = models.CharField(max_length=100, blank=True, null=True,verbose_name='Avatar')
    hl_role = models.CharField(max_length=10, blank=True, null=True,verbose_name='Role')
    hl_area = models.CharField(max_length=100, blank=True, null=True, verbose_name="Area")
    hl_phone = models.CharField(max_length=25, blank=True, null=True,verbose_name='Phone')
    hl_branch = models.CharField(max_length=13, blank=True, null=True,verbose_name='Branch')
    hl_case = models.IntegerField(blank=True, null=True,verbose_name='Case')
    hl_clock = models.IntegerField(blank=True, null=True,verbose_name='Clock')
    hl_time = models.IntegerField(blank=True, null=True,verbose_name='Time')

    def get_schedule(self):
        """Returns the users schedule in the helpline"""
        return Schedule.objects.filter(hl_key__exact=self.hl_key)
    def __unicode__(self):
        return self.hl_names if self.hl_names else "No Name"

    def get_average_talk_time(self):
        """Get the average talk time for a user.
        Counted from the last midnight"""
        # Get the epoch time of the last midnight
        midnight = datetime.combine(date.today(),
                                    datetime_time.min).strftime('%s')

        # Get the average seconds of hold time from last midnight.
        # Return global values for supervisors.
        if self.hl_role.lower() != "supervisor":
            seconds = MainCDR.objects.filter(
                hl_time__gt=midnight).filter(
                    hl_agent__exact=self.hl_key).aggregate(
                        Avg('hl_talktime')).get('hl_talktime__avg')
        else:
            seconds = MainCDR.objects.filter(
                hl_time__gt=midnight).aggregate(
                    Avg('hl_talktime')).get('hl_talktime__avg')


        td = timedelta(seconds = seconds if seconds else 0)
        att = {'hours':"%02d" % (td.seconds//3600)
            ,'min':"%02d" % ((td.seconds//60)%60),'seconds': "%02d" % ((td.seconds)%60)}
        return att

    def get_average_wait_time(self):
        """Get the average hold time for a user.
        Counted from the last midnight"""
        # Get the epoch time of the last midnight
        midnight = datetime.combine(date.today(), datetime_time.min).strftime('%s')
        # Get the average seconds of hold time from last midnight.
        # Return global values for supervisors.
        if self.hl_role.lower() != "supervisor":
            seconds = MainCDR.objects.filter(
                hl_time__gt=midnight).filter(
                    hl_agent__exact=self.hl_key).aggregate(
                        Avg('hl_holdtime')).get('hl_holdtime__avg')
        else:
            seconds = MainCDR.objects.filter(
                hl_time__gt=midnight).aggregate(
                        Avg('hl_holdtime')).get('hl_holdtime__avg')

        td = timedelta(seconds = seconds if seconds else 0)
        awt = {'hours':"%02d" % (td.seconds//3600)
            ,'min':"%02d" % ((td.seconds//60)%60),'seconds': "%02d" % ((td.seconds)%60)}
        return awt

    def get_login_duration(self):
        time_now = timezone.now()
        last_login = self.user.last_login
        ld = time_now - last_login
        login_duration = {'hours':"%02d" % (ld.seconds//3600)
            ,'min':"%02d" % ((ld.seconds//60)%60),'seconds': "%02d" % ((ld.seconds)%60)}
        return login_duration

    def get_ready_duration(self):
        """Get how long the agent has been on the queue"""
        clockin = Clock.objects.filter(hl_key=self.hl_key,hl_clock="Queue Join").order_by('-id').first()
        clockout = Clock.objects.filter(hl_key=self.hl_key,hl_clock="Queue Leave").order_by('-id').first()

        if clockin:
            if clockout:
                if clockout.hl_time > clockin.hl_time:
                    return
            seconds = time.time() - clockin.hl_time
            ld = timedelta(seconds=seconds if seconds else 0)
            ready_duration = {'hours': "%02d" % (ld.seconds//3600),
                              'min': "%02d" % (
                                  (ld.seconds//60) % 60), 'seconds': "%02d" % (
                    (ld.seconds) % 60)}
            return ready_duration
        else:
            return

    def get_recent_clocks(self):
        """Get recent actions A.K.A Clocks
        We return only 5 at this time."""
        return Clock.objects.filter(hl_key=self.hl_key).order_by('-id')[:5]


class WorkForce(models.Model):
    hl_key = models.IntegerField()
    clockdate = models.DateField()
    weblogin = models.IntegerField()
    clockbreak = models.IntegerField()
    weblogout = models.IntegerField()
    callsanswered = models.IntegerField()
    missedcalls = models.IntegerField()
    casescreated = models.IntegerField()
    talktime = models.IntegerField()
    occupancy = models.IntegerField()
    queuebreaks = models.IntegerField()
    queuelogin = models.IntegerField()
    queuelogout = models.IntegerField()
    hl_time = models.IntegerField()
    hl_access = models.DateTimeField()


class WorkForce2(models.Model):
    hl_key = models.IntegerField()
    clockdate = models.DateField()
    weblogin = models.IntegerField()
    clockbreak = models.IntegerField()
    weblogout = models.IntegerField()
    callsanswered = models.IntegerField()
    missedcalls = models.IntegerField()
    casescreated = models.IntegerField()
    talktime = models.IntegerField()
    occupancy = models.IntegerField()
    queuebreaks = models.IntegerField()
    queuelogin = models.IntegerField()
    queuelogout = models.IntegerField()
    hl_time = models.IntegerField()
    hl_access = models.DateTimeField()
