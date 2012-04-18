# Copyright (c) 2012 Oregon State University

# Generic class-based view mixins and helpers.

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import simplejson as json
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic.list import ListView

# Standard translation messages. We use these everywhere.

NO_PRIVS = _('You do not have sufficient privileges')


class LoginRequiredMixin(object):
    """
    Helper mixin which applies @login_required to all methods on a view.

    Meant to massively simplify the four-line prelude common to many of our
    views.
    """

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)


class PagedListView(ListView):
    """
    Helper which automatically applies uniform pagination options to any
    paginated list.

    This helper should be mixed in *before* ListView or any of its relatives.
    """

    def get_paginate_by(self, queryset):
        """
        Return the number of items to paginate by.

        I like the wording on the other docstring: "An integer specifying how
        many objects should be displayed per page."
        """

        print "Here!"
        return self.request.GET.get("count", settings.ITEMS_PER_PAGE)

    def paginate_queryset(self, queryset, page_size):
        """
        Returns a 4-tuple containing (paginator, page, object_list,
        is_paginated).

        The Django docstring isn't super-helpful. This function is the actual
        workhorse of pagination. Our hook here is meant to order the queryset,
        if needed, prior to pagination since Django won't do it otherwise.
        """

        print "Here too!"
        if "order_by" in self.request.GET:
            queryset = queryset.order_by(self.request.GET["order_by"])
        return super(PagedListView, self).paginate_queryset(queryset,
                                                            page_size)


class JSONOnlyMixin(object):
    """
    Mixin which simplifies the logic of crafting a view which returns JSON.
    """

    def render_to_response(self, context):
        return HttpResponse(json.dumps(context),
                            content_type="application/json")
