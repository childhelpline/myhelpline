# -*- coding: utf-8 -*-
"""Helpline Models"""

from __future__ import unicode_literals
import calendar
from datetime import timedelta, datetime, date, time as datetime_time
import time
import os
import re

from random import randint

from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg
from django.utils import timezone
from django.apps import apps
from django.utils.translation import ugettext_lazy as _

from helpdesk.models import Ticket
from onadata.apps.logger.models.instance import Instance
from onadata.apps.logger.models.xform import XForm

from django.db.models.signals import post_save
from django.dispatch import receiver

from django.contrib.auth.signals import user_logged_in, user_logged_out  

class Address(models.Model):
    """Gives details about parties in a report"""
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
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True, null=True
    )
    # Creator will be deleted in favor of user model
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
 


class Contact(models.Model):
    """Contact information for an address"""
    address = models.ForeignKey(Address, on_delete=models.CASCADE,
                                blank=True, null=True)
    hl_contact = models.CharField(max_length=250)
    hl_parent = models.IntegerField(blank=True, null=True)
    hl_type = models.CharField(max_length=12, blank=True, null=True)
    hl_calls = models.IntegerField(blank=True, null=True)
    hl_status = models.CharField(max_length=10, blank=True, null=True)
    hl_time = models.IntegerField(blank=True, null=True)

    class Meta:
        unique_together = (('address', 'hl_contact'),)

    def __unicode__(self):
        return self.hl_contact

    def get_name(self):
        return self.address.hl_names


class Case(models.Model):
    """Case management model"""
    hl_case = models.AutoField(primary_key=True)
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        blank=True, null=True
    )
    hl_unique = models.CharField(unique=True, max_length=20,
                                 blank=True, null=True)
    hl_disposition = models.CharField(max_length=250, blank=True, null=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True, null=True
    )
    hl_data = models.CharField(max_length=9, blank=True, null=True)
    hl_popup = models.CharField(max_length=6,
                                blank=True, null=True)
    hl_time = models.IntegerField(blank=True, null=True)
    instance = models.ManyToManyField(Instance)
    status = models.CharField(max_length=25, blank=True, null=True)
    priority = models.CharField(max_length=25, blank=True, null=True)

    def __unicode__(self):
        return str(self.hl_case)


class CaseTrail(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
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
    hl_subcategory = models.CharField(max_length=100,
                                      verbose_name='Subcategory')
    hl_subsubcat = models.CharField(max_length=100,
                                    verbose_name='Sub-subcategory',
                                    blank=True, null=True)

    def get_subcategory(self):
        return Category.objects.filter(hl_category=self.hl_category)

    def get_sub_subcategory(self):
        return Category.objects.filter(hl_category=self.hl_subsubcat)

    def __unicode__(self):
        return self.hl_category


class ClockBit(models.Model):
    hl_key = models.IntegerField()
    hl_clock = models.CharField(max_length=11)
    hl_service = models.IntegerField()
    hl_time = models.IntegerField()


class Country(models.Model):
    """
    Gives the details and attributes of an object country which can be used at different instances within the system
    """
    hl_category = models.CharField(max_length=100)
    hl_code = models.CharField(max_length=2)
    hl_country = models.CharField(max_length=250)
    hl_phone = models.IntegerField()


class Dialect(models.Model):
    """
    An object model of the different languages and/or dialects identifiable within a region of the system use. These can be used
    for clients being registered into the system or identify agents 
    """
    hl_category = models.CharField(max_length=100, blank=True, null=True)
    hl_dialect = models.CharField(max_length=100, verbose_name="Language")
    hl_status = models.IntegerField(blank=True, null=True)

    class Meta:
        verbose_name = 'Language'
        verbose_name_plural = 'Languages'

    def __unicode__(self):
        return self.hl_dialect


class Hotdesk(models.Model):
    """A hotdesk references the workstation an agent seats. Normally marked by the SIP configurations on the soft phone
     and mostly set static"""
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
    status = models.CharField(
        max_length=11,
        choices=AVAILABILITY_CHOICES,
        default=UNAVAILABLE
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True, null=True
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
    """Instant Messaging, as it dictates, a set of received or sent short message and/or instant communication channels"""
    hl_index = models.AutoField(primary_key=True)
    hl_chat = models.CharField(max_length=300)
    hl_mandatory = models.CharField(max_length=300)
    hl_path = models.CharField(max_length=300)
    hl_type = models.IntegerField()
    hl_table = models.CharField(max_length=100)


class MainCDR(models.Model):
    """Raw Call details """
    # hl_unique = models.CharField(unique=True, max_length=32)
    # hl_start = models.BigIntegerField()
    # hl_end = models.IntegerField()
    # hl_duration = models.IntegerField()
    # hl_queue = models.IntegerField()
    # hl_agent = models.IntegerField()
    # hl_bridge = models.CharField(max_length=100)
    # hl_holdtime = models.IntegerField()
    # hl_talktime = models.IntegerField()
    # hl_vmail = models.CharField(max_length=7)
    # hl_app = models.CharField(max_length=9)
    # hl_status = models.CharField(max_length=11)
    # hl_time = models.IntegerField()
    hl_phone       = models.CharField(max_length=12,blank=True, null=True)
    hl_start       = models.BigIntegerField(blank=True, null=True)
    hl_answer      = models.IntegerField(blank=True, null=True)
    hl_stop        = models.BigIntegerField(blank=True, null=True)
    hl_queue       = models.IntegerField(blank=True, null=True)
    hl_status      = models.CharField(max_length=11,blank=True, null=True)
    hl_type        = models.IntegerField(blank=True, null=True)
    hl_chan        = models.IntegerField(blank=True, null=True)
    hl_agent       = models.IntegerField(blank=True, null=True)
    hl_transfer    = models.CharField(max_length=11,blank=True, null=True)
    hl_record      = models.CharField(max_length=30,blank=True, null=True)
    hl_case        = models.IntegerField(blank=True, null=True)
    hl_wrapup      = models.CharField(max_length=11,blank=True, null=True)
    hl_bargein     = models.CharField(max_length=11,blank=True, null=True)
    hl_voicemail   = models.CharField(max_length=11,blank=True, null=True)
    hl_disposition = models.CharField(max_length=20,blank=True, null=True)
    hl_pid         = models.IntegerField(blank=True, null=True)


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
    """A list of user menu details based on user authorization"""
    hl_user = models.IntegerField()
    hl_key = models.IntegerField()
    hl_status = models.IntegerField()
    hl_menu = models.CharField(max_length=100)
    hl_path = models.CharField(max_length=100)
    hl_query = models.TextField()
    hl_data = models.TextField()
    hl_time = models.IntegerField()



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
    """Contact and address details of partner organizations and institutions"""
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

class Service(models.Model):
    """Identifies a queue that agents can be assigned"""
    extension = models.CharField(
        unique=True,
        max_length=100,
        help_text=_('Extension callers will dial e.g 116.'),
    )
    name = models.CharField(
        max_length=255,
        help_text=_('Service name')
    )
    queue = models.CharField(
        max_length=255,
        blank=True, null=True,
        help_text=_('Corresponding Asterisk Queue name')
    )
    walkin_xform = models.ForeignKey(
        XForm, on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='walkin_xform',
        help_text=_('Walkin Case Form')
    )
    call_xform = models.ForeignKey(
        XForm, on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='call_xform',
        help_text=_('Call Case Form')
    )
    qa_xform = models.ForeignKey(
        XForm, on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='qa_xform',
        help_text=_('Quality Analysis Form')
    )
    web_online_xform = models.ForeignKey(
        XForm, on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='web_online_xform',
        help_text=_('Quality Analysis Form')
    )

    def __unicode__(self):
        return self.name


class Clock(models.Model):
    """A Clock is an audit trail of agent actions"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True, null=True
    )
    hl_clock = models.CharField(verbose_name='Action', max_length=50)
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE,
        blank=True, null=True
    )
    hl_time = models.IntegerField(verbose_name='Time')

    def __unicode__(self):
        return self.hl_clock


class Report(models.Model):
    """Main report table."""
    address = models.ForeignKey(
        Address,
        on_delete=models.CASCADE,
        blank=True, null=True
    )
    case = models.OneToOneField(
        Case, on_delete=models.CASCADE,
        related_name='Report',
        blank=True, null=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True, null=True
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        blank=True, null=True
    )
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
    talktime = models.DurationField(verbose_name='Talk Time',
                                    blank=True, null=True)
    holdtime = models.DurationField(verbose_name='Hold Time',
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
    hl_unique = models.CharField(unique=True, max_length=20,
                                 blank=True, null=True,
                                 verbose_name='Unique Call-ID')
    qa = models.CharField(max_length=3, verbose_name='QA',
                          blank=True, null=True)

    def __unicode__(self):
        return str(self.case)

    def get_call_type(self):
        """ Get casetype."""
        if self.casetype:
            if self.casetype.lower() == "call":
                return "Inbound"
            elif self.casetype.lower() == "voicemail":
                return "Voicemail"
            else:
                return "Outbound"
        else:
            return "Walkin"

    def get_absolute_url(self):
        """Calculate the canonical URL for Report."""
        # Django 1.10 breaks reverse imports.
        try:
            from django.urls import reverse
        except Exception as e:
            from django.core.urlresolvers import reverse

        return reverse('case_form', args=[self.casetype.lower() if self.casetype else "call"]) + "?case=%s" % str(self.case)

    def get_qa_url(self):
        """Calculate the canonical URL for Report."""
        # Django 1.10 breaks reverse imports.
        try:
            from django.urls import reverse
        except Exception as e:
            from django.core.urlresolvers import reverse

        return reverse('case_form', args=[self.casetype.lower() if self.qa else "qa"]) + "?case=%s" % str(self.case)


class Messaging(models.Model):
    """Inbuilt messaging model"""
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        blank=True, null=True
    )
    hl_service = models.CharField(max_length=100, verbose_name='Service')
    hl_contact = models.CharField(max_length=25, verbose_name='Contact')
    hl_key = models.IntegerField(verbose_name='Key')
    hl_type = models.CharField(max_length=6, verbose_name='Type')
    hl_status = models.CharField(max_length=7, verbose_name='Status')
    hl_staff = models.IntegerField(verbose_name='Staff', blank=True, null=True)
    hl_content = models.TextField(verbose_name='Content')
    hl_time = models.IntegerField(verbose_name='Time')

    def get_formatted_time(self):
        """Get ISO formated time from time stamp"""
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.hl_time))

    def __unicode__(self):
        return str(self.hl_contact)

class Role(models.Model):
    hl_role = models.CharField(max_length=100)
    hl_context = models.CharField(max_length=100)
    hl_status = models.IntegerField()
    hl_count = models.IntegerField()
    hl_time = models.IntegerField()


class Schedule(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True, null=True
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        blank=True, null=True
    )
    hl_status = models.CharField(max_length=7)

    def __unicode__(self):
        return str(self.id)

class Search(models.Model):
    hl_word = models.CharField(unique=True, max_length=100)
    hl_path = models.CharField(max_length=100)
    hl_menu = models.CharField(max_length=100)
    hl_service = models.CharField(max_length=100)


class SMSCDR(models.Model):
    """
    This acts as an SMS log where both received and sent SMS are stored, when a case is created, its number is marked against the sms
    """
    from_phone     = models.CharField(max_length=30)
    msg         = models.CharField(max_length=320, blank=True, null=True)
    sms_status  = models.IntegerField(default=0)
    time        = models.DateTimeField(db_column='Time', blank=True, null=True)
    thread      = models.IntegerField(default=0)
    sms_type    = models.CharField(blank=False,max_length=8,default="INBOX")
    sms_case    = models.IntegerField(blank=True,default=0)
    sms_time    = models.DateTimeField(auto_now_add=True,editable=False)

def get_rand():
    while True:
        numb = randint(123456789,999999999)
        if not HelplineUser.objects.filter(hl_key=numb).exists():
            return numb
        
def get_auth_key():
    while True:
        numb = randint(1000, 9999)
        if not HelplineUser.objects.filter(hl_key=numb).exists():
            return numb

class HelplineUser(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='HelplineUser'
    )
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        blank=True, null=True
    )
    hl_key = models.IntegerField(
        unique=True, primary_key=True,
        verbose_name=_('Key'),
        help_text=_('Autogenerated'),
        default=get_rand
    )
    hl_auth = models.IntegerField(
        verbose_name=_('Auth'),
        help_text=_('Autogenerated Four digit numeric number e.g. 1973.'),
        default=get_auth_key
    )
    hl_pass = models.CharField(
        max_length=500,
        verbose_name=_('PIN'), help_text=_('Four digit numeric PIN')
    )
    hl_exten = models.CharField(
        max_length=55,
        blank=True, null=True,
        verbose_name=_('Exten'), help_text=_('Agent Softphone extension.')
    )
    hl_status = models.CharField(
        max_length=11, blank=True,
        null=True,
        verbose_name=_('Status')
    )
    hl_calls = models.IntegerField(
        blank=True, null=True,
        verbose_name=_('Total Calls')
    )
    hl_email = models.CharField(
        max_length=500, blank=True,
        null=True,
        verbose_name=_('Email')
    )
    hl_names = models.CharField(
        max_length=250,
        blank=True,
        null=True,
        verbose_name=_('Names'))
    hl_nick = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Nick')
    )
    hl_avatar = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Avatar'))
    hl_role = models.CharField(
        max_length=20,
        blank=True, null=True,
        verbose_name=_('Role')
    )
    hl_area = models.CharField(
        max_length=100,
        blank=True, null=True,
        verbose_name=_("Area")
    )
    hl_phone = models.CharField(
        max_length=25,
        blank=True, null=True,
        verbose_name=_('Phone'))
    hl_branch = models.CharField(
        max_length=13,
        blank=True, null=True,
        verbose_name=_('Branch'))
    hl_case = models.IntegerField(
        blank=True, null=True,
        verbose_name=_('Case'))
    hl_clock = models.IntegerField(
        blank=True, null=True,
        verbose_name=_('Clock')
    )
    hl_time = models.IntegerField(
        blank=True, null=True,
        verbose_name=_('Time')
    )

    def get_schedule(self):
        """Returns the users schedule in the helpline"""
        return Schedule.objects.filter(user__exact=self.hl_key)

    def __unicode__(self):
        return self.hl_names if self.hl_names else "No Name"

    def get_average_talk_time(self):
        """Get the average talk time for a user.
        Counted from the last midnight"""
        # Get the epoch time of the last midnight
        midnight_datetime = datetime.combine(date.today(),
                                    datetime_time.min)
        midnight = calendar.timegm(midnight_datetime.timetuple())

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

        td = timedelta(seconds=seconds if seconds else 0)
        att = {'hours': "%02d" % (td.seconds//3600),
               'min': "%02d" % ((td.seconds//60) % 60),
               'seconds': "%02d" % ((td.seconds) % 60)}
        return att

    def get_average_wait_time(self):
        """Get the average hold time for a user.
        Counted from the last midnight"""
        # Get the epoch time of the last midnight
        midnight_datetime = datetime.combine(date.today(),
                                    datetime_time.min)
        midnight = calendar.timegm(midnight_datetime.timetuple())
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
        login_duration = {
            'hours': "%02d" % (ld.seconds//3600),
            'min': "%02d" % ((ld.seconds//60) % 60),
            'seconds': "%02d" % ((ld.seconds) % 60)
        }
        return login_duration

    def get_ready_duration(self):
        """Get how long the agent has been on the queue"""
        clockin = Clock.objects.filter(
            user=self.user,
            hl_clock="Queue Join").order_by('-id').first()
        clockout = Clock.objects.filter(
            user=self.user,
            hl_clock="Queue Leave"
        ).order_by('-id').first()

        if clockin:
            if clockout:
                if clockout.hl_time > clockin.hl_time:
                    return
            seconds = time.time() - clockin.hl_time
            ld = timedelta(seconds=seconds if seconds else 0)
            ready_duration = {
                'hours': "%02d" % (ld.seconds//3600),
                'min': "%02d" % (
                    (ld.seconds//60) % 60),
                'seconds': "%02d" % (
                    (ld.seconds) % 60)
            }
            return ready_duration
        else:
            return

    def get_recent_clocks(self):
        """Get recent actions A.K.A Clocks
        We return only 5 at this time."""
        return Clock.objects.filter(user=self.user).order_by('-id')[:5]

@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
    if created:
        # HelplineUser.hl_key = randint(123456789, 999999999)
        # HelplineUser.hl_auth = randint(1000, 9999)
        HelplineUser.objects.create(user=instance)
        instance.HelplineUser.save()

class Cdr(models.Model):
    """A CDR consists of a unique identifier and several
    fields of information about a call"""
    accountcode = models.IntegerField(blank=True, null=True)
    calldate    = models.DateTimeField(auto_now_add=True, blank=True)
    clid        = models.CharField(max_length=80, blank=True, null=True)
    src         = models.CharField(max_length=80, blank=True, null=True)
    dst         = models.CharField(max_length=80, blank=True, null=True)
    dcontext    = models.CharField(max_length=80, blank=True, null=True)
    channel     = models.CharField(max_length=80, blank=True, null=True)
    dstchannel  = models.CharField(max_length=80, blank=True, null=True)
    lastapp     = models.CharField(max_length=80, blank=True, null=True)

    lastdata    = models.CharField(max_length=80, blank=True, null=True)
    duration    = models.IntegerField(blank=True, null=True)
    billsec     = models.IntegerField(blank=True, null=True)
    disposition = models.CharField(max_length=45, blank=True, null=True)
    amaflags    = models.IntegerField(blank=True, null=True)
    accountcode = models.CharField(max_length=20, blank=True, null=True)
    uniqueid    = models.CharField(max_length=32, blank=True, null=True)
    userfield   = models.CharField(max_length=255, blank=True, null=True)
    peeraccount = models.CharField(max_length=20, blank=True, null=True)
    linkedid    = models.CharField(max_length=20, blank=True, null=True)
    sequence    = models.CharField(max_length=20, blank=True, null=True)

    def __unicode__(self):
        return "%s -> %s" % (self.src, self.dst)

class Emails(models.Model):
    """
    Model for emails synchronized from the public, when a case is created from one, the email_case is filled with the caseid
    """
    email_idkey     = models.CharField(max_length=250)
    email_from      = models.CharField(max_length=100,blank=True, null=True)
    email_status    = models.IntegerField(default=0)
    email_body      = models.TextField(blank=True, null=True)
    email_subject   = models.CharField(max_length=300, blank=True, null=True)
    email_date      = models.CharField(max_length=50,blank=True, null=True)
    email_time      = models.DateTimeField(auto_now_add=True)
    email_case      = models.IntegerField(default=0)


class Cases(models.Model):
    """model for Case Numbers to track case numbers"""
    case_number = models.IntegerField(default=0)
    case_source = models.CharField(max_length = 7, editable=False)
    case_time   = models.DateTimeField(auto_now_add=True)
    case_disposition = models.CharField(max_length = 100,blank=True, null=True)

def login_user(sender, request, user, **kwargs):
    user.HelplineUser.hl_status = 'Available'
    user.HelplineUser.save()

def logout_user(sender, request, user, **kwargs):
    user.HelplineUser.hl_status = 'Unavailable'
    user.HelplineUser.save()
    
user_logged_in.connect(login_user)
user_logged_out.connect(logout_user)

# class calls_detail(models.Model):
#     """model for call records"""
#     dataCreated = models.IntegerField(default=0)
#     dataUpdated = models.IntegerField(default=0)
#     cdrID = models.CharField(max_length = 500,blank=True, null=True) 
#     cdrPhone = models.CharField(max_length = 500,blank=True, null=True)
#     cdrApp = models.CharField(max_length = 500,blank=True, null=True)
#     cdrStart = models.IntegerField(default=0)
#     cdrStop = models.IntegerField(default=0)
#     cdrStatus  = models.CharField(max_length = 500,blank=True, null=True)

    # CALL RECORD MODEL
    # datas['phone'] = _data.get('cdr_phone') datas['app'] = _data.get('cdr_app') \
    # datas['start'] = _data.get('cdr_start') datas['answer'] = _data.get('cdr_answer') \
    # datas['stop'] = _data.get('cdr_stop') datas['queue'] = _data.get('cdr_queue') \
    # datas['status'] = _data.get('cdr_status') datas['type'] = _data.get('cdr_type') \
    # datas['chan'] = _data.get('cdr_chan') datas['agent'] = _data.get('cdr_agent') \
    # datas['transfer'] = _data.get('cdr_transfer') datas['record'] = _data.get('cdr_record') \
    # datas['case'] = _data.get('cdr_case') datas['wrapup'] = _data.get('cdr_wrapup') \
    # datas['bargein'] = _data.get('cdr_bargein') datas['voicemail'] = _data.get('cdr_voicemail') \
    # datas['disposition'] = _data.get('cdr_exit') datas['pid'] = _data.get('cdr_pid')
        
