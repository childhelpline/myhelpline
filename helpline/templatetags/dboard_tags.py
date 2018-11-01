"""Tamplate tags that assist our application"""
from datetime import datetime
from helpline.models import Cases

from django.template.defaulttags import register

@register.filter(name='timestamp')
def timestamp(value):
    """Return datetime object from epoch value"""
    try:
        return datetime.fromtimestamp(value)
    except AttributeError, e:
        return e

def increment_case_number():
    last_case_number = Cases.objects.all().last().case_number
    if not last_case_number:
        return 1000001
    else:
        return int(last_case_number) + 1

@register.assignment_tag
def case_id(case_source):
    case = Cases()
    case.case_number = increment_case_number()
    case.case_source = case_source
    case.save()
    return case.case_number
