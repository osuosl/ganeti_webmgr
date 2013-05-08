# Copyright (c) 2012 Oregon State University

# Generic class-based view mixins and helpers.

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured
from django.utils.decorators import method_decorator
from django.utils.http import urlencode
from django.utils.translation import ugettext as _

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

    paginate_by = settings.ITEMS_PER_PAGE  # list view
    table_pagination = {"per_page": settings.ITEMS_PER_PAGE}  # table view

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


class GWMBaseView(object):
    """
    A base view which will filter querysets by cluster, primary node, or
    secondary node. It will also saves these to context data.

    This base already includes our standard mixins and if a more custom view is
    necessary, the methods can be overloaded.
    """
    def get_kwargs(self):
        """
        Get common URL kwargs and assign as object variables.

        This is a useful utility method that should be used if you don't want
        to call super() on you queryset method at the beginning.
        """
        self.cluster_slug = self.kwargs.get("cluster_slug", None)
        self.pnode = self.kwargs.get("primary_node", None)
        self.snode = self.kwargs.get("secondary_node", None)

    def get_queryset(self):
        self.get_kwargs()  # Make sure that we have our values.
        qs = super(GWMBaseView, self).get_queryset()
        # Filter by cluster if applicable
        if self.cluster_slug:
            qs = qs.filter(cluster__slug=self.cluster_slug)

        # filter the vms by primary node if applicable
        if self.pnode:
            qs = qs.filter(primary_node=self.pnode)

        # filter the vms by the secondary node if applicable
        if self.snode:
            qs = qs.filter(secondary_node=self.snode)

        return qs

    def get_context_data(self, **kwargs):
        self.get_kwargs()
        context = super(GWMBaseView, self).get_context_data(**kwargs)
        context['cluster_slug'] = self.cluster_slug

        return context

    def can_create(self, cluster):
        """
        Given an instance of a cluster or all clusters returns
        whether or not the logged in user is able to create a VM.
        """
        user = self.request.user
        return (user.is_superuser or user.has_any_perms(cluster,
                ["admin", "create_vm"]))
