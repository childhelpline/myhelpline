# -*- coding: utf-8 -*-
"""Helpline forms"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm
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
    ('Underwriting', 'Underwriting'),
    ('HealthCare- Case management', 'HealthCare- Case management'),
    ('Lead', 'Lead'),
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


class CallForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = 'caseDet'
        self.helper.form_class = 'caseDet'
        self.helper.form_method = 'post'
        self.helper.form_action = ''

        self.helper.add_input(Submit('submit', 'Save'))
        super(CallForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Address
        fieleds = ['hl_names', 'hl_phone'
                   'hl_address1']

    case_number = forms.CharField(widget=forms.HiddenInput(), required=False)

    caller_name = forms.CharField(
        label='Contact Name',
        widget=AutoCompleteWidget(NameLookup,
                                  attrs={
                                      'class': 'form-control',
                                  }),
        required=False,
    )

    company = forms.CharField(
        label='Company',
        widget=AutoCompleteWidget(AddressLookup,
                                  attrs={
                                      'class': 'form-control',
                                  }),
        required=False,
    )

    email = forms.CharField(
        label='Email',
        widget=AutoCompleteWidget(AddressLookup,
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

    case_type = forms.ChoiceField(
        label='Type',
        widget=forms.Select(
            attrs={
                'class': 'form-control',
            }
        ),
        choices=CASE_TYPE_CHOICES,
        required=False
    )

    category = forms.ChoiceField(
        required=False,
        choices=get_categories,
        widget=forms.Select(
            attrs={
                'class': 'form-control',
            }
        ),
    )

    sub_category = forms.ChoiceField(
        required=False,
        choices=get_sub_categories,
        widget=forms.Select(
            attrs={
                'class': 'form-control',
            }
        ),)

    business_portfolio = forms.ChoiceField(choices=BUSINESS_PORTFOLIO_CHOICES,
                                           required=False,
                                           widget=forms.Select(
                                               attrs={
                                                   'class': 'form-control',
                                               }
                                           ),)

    case_status = forms.ChoiceField(choices=STATUS_CHOICES,
                                    required=False,
                                    widget=forms.Select(
                                        attrs={
                                            'class': 'form-control',
                                        }
                                    ),)

    comment = forms.CharField(
        label='Description',
        widget=forms.Textarea(
            attrs={'col': '30',
                   'rows': '7',
                   'class': 'form-control',
                   'id': 'txtComment'}

        ),
        required=False,
    )

    case_status = forms.ChoiceField(choices=STATUS_CHOICES,
                                    required=False,
                                    widget=forms.Select(
                                        attrs={
                                            'class': 'form-control',
                                        }
                                    ),)

    notes = forms.CharField(required=False,
                            label='Claim Reference Number:',
                            widget=forms.TextInput(
                                attrs={
                                    'class': 'form-control',
                                }
                            ),)

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
        label='Enumerator:',
        queryset=HelplineUser.objects.all().order_by('hl_names'),
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
