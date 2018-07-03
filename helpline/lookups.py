from __future__ import unicode_literals

from selectable.base import ModelLookup
from selectable.decorators import login_required
from selectable.registry import registry

from helpline.models import Category,\
        Address, Contact, Partner, Messaging


@login_required
class AddressLookup(ModelLookup):
    model = Address
    search_fields = ('hl_address1__icontains', )

    def get_item_value(self, item):
        return item.hl_address1

    def get_item_label(self, item):
        return u"%s" % (item.hl_address1)


@login_required
class PhoneLookup(ModelLookup):
    model = Contact
    search_fields = ('hl_contact__icontains',)


@login_required
class NameLookup(ModelLookup):
    model = Address
    search_fields = ('hl_names__icontains', )


@login_required
class RecipientLookup(ModelLookup):
    model = Messaging
    search_fields = ('hl_contact__icontains',)

    def get_query(self, request, term):
        qs = super(RecipientLookup, self).get_query(request, term)
        return qs.order_by('hl_contact').distinct()

    def get_item_value(self, item):
        return item.hl_contact

    def get_item_label(self, item):
        return u"%s" % (item.hl_contact)


@login_required
class EmailLookup(ModelLookup):
    model = Address
    search_fields = ('hl_email__icontains', )

    def get_item_value(self, item):
        return item.hl_email

    def get_item_label(self, item):
        return u"%s" % (item.hl_email)


@login_required
class PartnerLookup(ModelLookup):
    model = Partner
    search_fields = ('referralpartner__icontains', )

    def get_item_value(self, item):
        return item.referralpartner

    def get_item_label(self, item):
        return u"%s" % (item.referralpartner)


@login_required
class SubCategoryLookup(ModelLookup):
    model = Category
    search_fields = ('hl_subcategory__icontains', )

    def get_item_value(self, item):
        return item.hl_subcategory

    def get_item_label(self, item):
        return u"%s" % (item.hl_subcategory)


registry.register(AddressLookup)
registry.register(PhoneLookup)
registry.register(NameLookup)
registry.register(RecipientLookup)
registry.register(EmailLookup)
registry.register(PartnerLookup)
registry.register(SubCategoryLookup)
