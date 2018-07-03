#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django import forms

from selectable.forms import AutoCompleteSelectMultipleField
from sendsms import api

from .lookups import RecipientLookup


class MessageForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea)
    contacts = AutoCompleteSelectMultipleField(
        lookup_class=RecipientLookup)

    def __init__(self, *args, **kwargs):
        super(MessageForm, self).__init__(*args, **kwargs)
        self.fields['contacts'].widget.attrs['placeholder'] = 'Add a Recipient'
        self.fields['message'].widget.attrs['placeholder'] = 'Message'

    def send(self):
        message = self.cleaned_data['message']
        contacts = self.cleaned_data['contacts']
        recipients = [recipient.hl_contact for recipient in contacts]
        api.send_sms(body=message,
                     from_phone='Info',
                     to=recipients)
        return recipients
