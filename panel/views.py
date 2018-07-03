# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render
from django.views.decorators.csrf import requires_csrf_token

from panel.qpanel import upgrader, job, rq_worker
import panel.qpanel.utils as uqpanel

from panel.qpanel.config import QPanelConfig
from panel.qpanel.backend import Backend
if QPanelConfig().has_queuelog_config():
    from panel.qpanel.model import queuelog_data_queue

from jsonview.decorators import json_view

cfg = QPanelConfig()
backend = Backend()


def get_data_queues(queue=None):
    data = backend.get_data_queues()
    if queue is not None:
        try:
            data = data[queue]
        except:
            raise Http404("Queue not found")
    return data


@login_required
def home(request):
    data = get_data_queues()
    template = 'index.html'
    if backend.is_freeswitch():
        template = 'fs/index.html'
    return render(request, template, data)


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


@login_required
@json_view
@requires_csrf_token
def spy(request):
    """ Handle channel spying """
    channel = request.POST.get('channel')
    to_exten = request.POST.get('to_exten')
    r = backend.spy(channel, to_exten)
    return {'data': r}
