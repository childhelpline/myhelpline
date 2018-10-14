# -*- coding: utf-8 -*-
"""Helpline forms"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.conf import settings

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from selectable.forms import AutoCompleteWidget

from helpline.models import HelplineUser,\
        Category, Address

from helpline.lookups import AddressLookup, NameLookup,\
        PhoneLookup, RecipientLookup,\
        EmailLookup, PartnerLookup, SubCategoryLookup


class QueueLogForm(forms.Form):
    """Queue join form"""
    softphone = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Enter Extention No',
                                      'required': 'true'}))


QUEUE_PAUSE_REASON_CHOICES = (
    ('', '--'),
    ('Toilet Break', 'Toilet Break'),
    ('Tea Break', 'Tea Break'),
    ('System Issue TE', 'System Issue TE'),
    ('System Issue PC', 'System Issue PC'),
    ('Meeting', 'Meeting'),
    ('Lunch', 'Lunch'),
    ('End of Shift', 'End of Shift'),
    ('Consulting', 'Consulting'),
    ('Coaching', 'Coaching'),
    ('Other Break Reason', 'Other Break Reason'),
)

GENDER_CHOICES = (
    ('', '--'),
    ('MALE', 'Male'),
    ('FEMALE', 'Female'),
)


STATUS_CHOICES = (
    ('Close', 'Close'),
    ('Pending', 'Pending'),
    ('Escalate', 'Escalate'),
    ('Transferred', 'Transferred'),
)

REFERRED_FROM_CHOICES = (
    ('--', '--'),
    ('Call Center', 'Call Center'),
    ('Facebook', 'Facebook'),
    ('Newspaper', 'Newspaper'),
    ('Friend', 'Friend'),
    ('Radio', 'Radio'),
    ('Other', 'Other'),
)


CASE_TYPE_CHOICES = (
    ('--', '--'),
    ('Claims', 'Claims'),
    ('Other', 'Other'),
)


INTERVAL_CHOICES = (
    ('', '--'),
    ('hourly', 'Hourly'),
    ('daily', 'Daily'),
    ('weekly', 'Weekly'),
    ('monthly', 'Monthly'),
)

BUSINESS_PORTFOLIO_CHOICES = (
    ('', '--'),
    ('eBancasurance', 'eBancasurance'),
    ('General Insurance', 'General Insurance'),
    ('Healthcare', 'Healthcare'),
    ('Hospitality & Tourism', 'Hospitality & Tourism'),
    ('Human Capital Benefits', 'Human Capital Benefits'),
    ('Investment', 'Investment'),
    ('Pension', 'Pension'),
    ('Reinsurance', 'Reinsurance'),
)

AGE_GROUP_CHOICES = (
    ('', '--'),
    ('15-24', '15-24'),
    ('25-34', '25-34'),
    ('35-44', '35-44'),
    ('45-54', '45-54'),
    ('55-64', '55-64'),
    ('65+', '65+'),
)
 
   

INTERVENTIONS = (
    ('Counselling', 'counselling'),
    ('appropriate_referrals','Appropriate Referrals'),
    ('awareness','Awareness'),
    ('psychological_support', 'Psychological Support'),
    ('educational_support', 'Educational Support'),
    ('directed_to_telecom', 'Support Directed to Telecom Support'),
    ('report_to_olice', 'Report to Police'),
    ('medical_support', 'Medical Support'),
    ('legal_support', 'Legal Support'),
    ('basic_need_support', 'Basic Need Support'),
    ('resettlement', 'Resettlement'),
    ('others', 'Others'),
)

def get_dialects():
    """Return list of languages."""
    return [("", "---------")] \
            + list(Dialect.objects.values_list(
                'hl_dialect', 'hl_dialect'
            ).distinct())


def get_categories():
    """Return list of categories."""
    return [("", "---------")] \
            + list(Category.objects.values_list(
                'hl_category', 'hl_category'
            ).distinct())


def get_sub_categories():
    """Return list of sub-categories."""
    return [("", "---------")] \
            + list(Category.objects.values_list(
                'hl_subcategory', 'hl_subcategory'
            ).distinct())


def get_sub_sub_categories():
    """Return list of sub-sub-categories."""
    return [("", "---------")] \
            + list(Category.objects.values_list(
                'hl_subsubcat', 'hl_subsubcat'
            ).distinct())


class ContactForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = 'contactDet'
        self.helper.form_class = 'contactDet'
        self.helper.form_method = 'post'
        self.helper.form_action = ''

        super(ContactForm, self).__init__(*args, **kwargs)

    case_number = forms.CharField(widget=forms.HiddenInput(), required=False)

    caller_name = forms.CharField(
        label='Contact Name',
        widget=AutoCompleteWidget(NameLookup,
                                  attrs={
                                      'class': 'form-control',
                                  }),
        required=False,
    )


    phone_number = forms.CharField(
        label='Phone Number',
        widget=AutoCompleteWidget(PhoneLookup,
                                  attrs={
                                      'class': 'form-control',
                                  }),
        required=False,
    )



class CaseActionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = 'caseAction'
        self.helper.form_class = 'caseAction'
        self.helper.form_method = 'post'
        self.helper.form_action = ''

        super(CaseActionForm, self).__init__(*args, **kwargs)

    case_number = forms.CharField(widget=forms.HiddenInput(), required=False)

    case_status = forms.ChoiceField(choices=STATUS_CHOICES,
                                    required=False,
                                    widget=forms.Select(
                                        attrs={
                                            'class': 'form-control',
                                        }
                                    ),)

    escalate_to = forms.ModelChoiceField(
        label='Escalate To:',
        queryset=HelplineUser.objects.all().order_by('hl_names'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control pull-right',
                                   'id': 'agent',
                                   'name': 'agent'}))


class DispositionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = 'disposeDet'
        self.helper.form_class = 'disposeDet'
        self.helper.form_method = 'post'
        self.helper.form_action = ''
        super(DispositionForm, self).__init__(*args, **kwargs)

    case_number = forms.CharField(widget=forms.HiddenInput(), required=True)
    disposition = forms.ChoiceField(choices=settings.DISPOSITION_CHOICES,
                                    widget=forms.Select(attrs={
                                        'onchange': "disposeCase(this);",
                                        'class': 'form-control',
                                    }
                                    ))

class CaseSearchForm(forms.Form):
    query = forms.CharField()


class MyAccountForm(ModelForm):
    class Meta:
        model = HelplineUser
        fields = ['hl_names', 'hl_phone', 'hl_phone']

class ReportFilterForm(forms.Form):
    datetime_range = forms.CharField(
        label='Choose Date and time Range:',
        widget=forms.TextInput(attrs={'class': 'form-control pull-right',
                                      'name': 'datetimerange',
                                      'id': 'datetimerange',
                                      'width': '200px'}),
        required=False,
    )
    agent = forms.ModelChoiceField(
        label='Agent:',
        queryset=User.objects.all().order_by('username'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control pull-right',
                                   'id': 'agent',
                                   'name': 'agent'}))

    interval = forms.ChoiceField(choices=INTERVAL_CHOICES,
                              label='Interval:',
                              required=False,
                            widget=forms.Select(
                                attrs={
                                    'class':'form-control pull-right',
                                    'id':'interval',
                                    'name':'interval',
                                }
                            ),
                                      )
    category = forms.ChoiceField(choices=get_categories,
                            label='Category:',
                            required=False,
                            widget=forms.Select(
                                attrs={
                                    'class':'form-control pull-right',
                                    'id':'category',
                                    'name':'category',
                                }
                            ),
                                      )

    queueid = forms.CharField(widget = forms.HiddenInput(), required=True)

    case_status = forms.ChoiceField(choices=STATUS_CHOICES,
                                    required=False,
                                    widget=forms.Select(
                                        attrs={
                                            'class': 'form-control',
                                        }
                                    ),)

    interventions = forms.ChoiceField(choices=INTERVENTIONS,
                                    required=False,
                                    widget=forms.Select(
                                        attrs={
                                            'class': 'form-control',
                                        }
                                    ),)


    '''service = forms.ChoiceField(choices=get_services,
        label='Select Service',
        required=True,
        widget=forms.Select(
            attrs={
                'class':'form-control pull-right',
                'id':'services',
                'name':'services',
            }
            ),
        )'''

class LoginForm(forms.Form):
    username = forms.CharField(label="Username", max_length=30,
                               widget=forms.TextInput(attrs={'class': 'form-control', 'name': 'username'}))
    password = forms.CharField(label="Password", max_length=30,
                               widget=forms.TextInput(attrs={'class': 'form-control', 'name': 'password'}))


class QueuePauseForm(forms.Form):
    """Queue pause form"""
    reason = forms.ChoiceField(
        label='Reason',
        widget=forms.Select(
            attrs={
                'class': 'form-control',
            }
        ),
        choices=QUEUE_PAUSE_REASON_CHOICES,
        required=False
    )

class ContactSearchForm(forms.Form):
    """Contact search form"""
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = 'contact-search-form'
        self.helper.form_class = 'contact-search-form'
        self.helper.form_method = 'post'
        self.helper.form_action = ''

        super(ContactSearchForm, self).__init__(*args, **kwargs)
    telephone = forms.CharField(
        required=False,
        label = 'Telephone',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter Phone Number',
                                      'type': 'tel'
            }
        )
    )
    name = forms.CharField(
        required=False,
        label = 'Name',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Contact Name',
            }
        )
    )
