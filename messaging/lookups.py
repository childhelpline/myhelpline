#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from helpline.models import Contact

from selectable.base import ModelLookup
from selectable.registry import registry
from selectable.decorators import login_required


@login_required
class RecipientLookup(ModelLookup):
    model = Contact
    search_fields = ('hl_contact__icontains',)

    def get_query(self, request, term):
        qs = super(RecipientLookup,self).get_query(request,term)
        return qs.order_by('hl_contact').distinct()

    def get_item_value(self,item):
        try:
            name = item.get_name()
        except:
            name = ""
        return u"%s <%s>" % (name, item.hl_contact)

    def get_item_label(self,item):
        try:
            name = item.get_name()
        except:
            name = ""
        return u"%s <%s>" % (name, item.hl_contact)


registry.register(RecipientLookup)
