# Copyright (c) 2012 Oregon State University

# Generic class-based view mixins and helpers.

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured
from django.utils.decorators import method_decorator
from django.utils.http import urlencode
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


class PaginationMixin(object):
    """
    Helper which automatically applies uniform pagination options to any
    paginated ListView.
    """

    paginate_by = settings.ITEMS_PER_PAGE

    def get_paginate_by(self, queryset):
        """
        Return the number of items to paginate by.

        I like the wording on the other docstring: "An integer specifying how
        many objects should be displayed per page."
        """

        return self.request.GET.get("count", self.paginate_by)


class SortingMixin(object):
    """
    A mixin which provides sorting for a ListView
    """

    default_sort_params = None

    def get_context_data(self, **kwargs):
        context = super(SortingMixin, self).get_context_data(**kwargs)
        sort_by, order = self.get_sort_params()
        params = {'sort_by': sort_by, 'order': order}
        # Store the sort querystring for the current page for easy reuse in
        # templates
        sort_query = urlencode(params)
        params.update({'sort_query': sort_query})
        context.update(params)
        return context

    def get_default_sort_params(self):
        if self.default_sort_params is None:
            raise ImproperlyConfigured(
                "'SortMixin' requires the 'default_sort_params' "
                "attribute to be set."
            )
        return self.default_sort_params

    def get_sort_params(self):
        default_sort_by, default_order = self.get_default_sort_params()
        sort_by = self.request.GET.get('sort_by', default_sort_by)
        order = self.request.GET.get('order', default_order)
        return (sort_by, order)

    def get_queryset(self):
        return self.sort_queryset(
            super(SortingMixin, self).get_queryset(),
            *self.get_sort_params())

    def sort_queryset(self, qs, sort_by, order):
        """
        This method is how to specify sorting in your view. By default it
        implements a very basic sorting which will use 'sort_by' as the field
        to sort, and 'order' as the sorting order.

        This is the main function to override and modify for sorting. Any sort
        params passed in the url will be passed into this method for use.
        """
        qs = qs.order_by(sort_by)
        if order == 'desc':
            qs = qs.reverse()
        return qs

class GWMBaseListView(PaginationMixin, SortingMixin, ListView):
    """
    A base view which will filter querysets by cluster, primary node, or
    secondary node. It will also saves these to context data.

    This base already includes our standard mixins and if a more custom view is
    necessary, the methods can be overloaded.
    """
    def get_queryset(self):
        qs = super(GWMBaseListView, self).get_queryset()
        # Filter by cluster if applicable
        cluster_slug = self.kwargs.get("cluster_slug", None)
        if cluster_slug:
            qs = qs.filter(cluster__slug=cluster_slug)

        # filter the vms by primary node if applicable
        pnode = self.kwargs.get("primary_node", None)
        if pnode:
            qs = qs.filter(primary_node=pnode)

        # filter the vms by the secondary node if applicable
        snode = self.kwargs.get("secondary_node", None)
        if snode:
            qs = qs.filter(secondary_node=snode)

        return qs

    def get_context_data(self, **kwargs):
        context = super(GWMBaseListView, self).get_context_data(**kwargs)
        cluster_slug = kwargs.get("cluster_slug", None)
        if cluster_slug:
            context['cluster_slug'] = cluster_slug

        return context
