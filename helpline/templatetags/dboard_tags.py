"""Tamplate tags that assist our application"""
from datetime import datetime

from django.template.defaulttags import register

@register.filter(name='timestamp')
def timestamp(value):
    """Return datetime object from epoch value"""
    try:
        return datetime.fromtimestamp(value)
    except AttributeError, e:
        return e
