# Copyright (C) 2010 Oregon State University et al.
# Copyright (C) 2010 Greek Research and Technology Network
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.


from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.forms import CharField, HiddenInput
from django.http import (HttpResponse, HttpResponseRedirect,
                         HttpResponseForbidden, HttpResponseBadRequest,
                         Http404)
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils import simplejson as json
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_http_methods, require_POST
from django.views.generic.edit import DeleteView
from django.views.generic.list import ListView

from object_log.views import list_for_object

from object_permissions import get_users_any
from object_permissions.signals import (view_add_user, view_edit_user,
                                        view_remove_user)
from object_permissions.views.permissions import view_users, view_permissions

from object_log.models import LogItem
log_action = LogItem.objects.log_action

from ganeti_web.backend.queries import vm_qs_for_users
from ganeti_web.caps import has_shutdown_timeout, has_balloonmem
from ganeti_web.forms.virtual_machine import (KvmModifyVirtualMachineForm,
                                              PvmModifyVirtualMachineForm,
                                              HvmModifyVirtualMachineForm,
                                              ModifyConfirmForm, MigrateForm,
                                              RenameForm, ChangeOwnerForm,
                                              ReplaceDisksForm)
from ganeti_web.middleware import Http403
from ganeti_web.models import Cluster, Job, SSHKey, Node, VirtualMachine
from ganeti_web.templatetags.webmgr_tags import render_storage
from ganeti_web.util.client import GanetiApiError
from ganeti_web.utilities import (cluster_os_list, compare, os_prettify,
                                  get_hypervisor)
from ganeti_web.views.generic import (NO_PRIVS, LoginRequiredMixin,
                                      PaginationMixin, SortingMixin,
                                      GWMBaseListView)


#XXX No more need for tastypie dependency for 0.8
class HttpAccepted(HttpResponse):
    """
    Take from tastypie.http

    In 0.9 when we reorganize the RestAPI, change this back
     to an import.
    """
    status_code = 202


def get_vm_and_cluster_or_404(cluster_slug, instance):
    """
    Utility function for querying VirtualMachine and Cluster in a single query
    rather than 2 separate calls to get_object_or_404.
    """
    query = VirtualMachine.objects \
        .filter(cluster__slug=cluster_slug, hostname=instance) \
        .select_related('cluster')
    if len(query):
        return query[0], query[0].cluster
    raise Http404('Virtual Machine does not exist')


class VMListView(LoginRequiredMixin, GWMBaseListView):
    """
    View for displaying a list of VirtualMachines.
    """
    template_name = "ganeti/virtual_machine/list.html"
    default_sort_params = ("hostname", 'asc')

    def get_template_names(self):
        if self.request.is_ajax():
            template = ['ganeti/virtual_machine/table.html']
        else:
            template = ['ganeti/virtual_machine/list.html']
        return template

    def get_queryset(self):
        # queryset takes precedence over model
        self.queryset = vm_qs_for_users(self.request.user)
        qs = super(VMListView, self).get_queryset()
        return qs

    def get_context_data(self, **kwargs):
        context = super(VMListView, self).get_context_data(**kwargs)
        # pass in the Cluster Class to check all clusters
        context["create_vm"] = self.can_create(Cluster)
        context["ajax_url"] = reverse("virtualmachine-list")
        return context

    def can_create(self, cluster):
        """
        Given an instance of a cluster or all clusters returns
        whether or not the logged in user is able to create a VM.
        """
        user = self.request.user
        return (user.is_superuser or user.has_any_perms(cluster,
            ["admin", "create_vm"]))


class VMDeleteView(LoginRequiredMixin, DeleteView):
    """
    Delete a VM.
    """

    template_name = "ganeti/virtual_machine/delete.html"

    def get_context_data(self, **kwargs):
        kwargs["vm"] = self.vm
        kwargs["cluster"] = self.cluster
        return super(VMDeleteView, self).get_context_data(**kwargs)

    def get_object(self):
        user = self.request.user
        vm, cluster = get_vm_and_cluster_or_404(self.kwargs["cluster_slug"],
                                                self.kwargs["instance"])
        if not (
            user.is_superuser or
            user.has_any_perms(vm, ["remove", "admin"]) or
                user.has_perm("admin", cluster)):
            raise Http403(NO_PRIVS)

        self.vm = vm
        self.cluster = cluster
        return vm

    def get_success_url(self):
        return reverse('instance-detail', args=[self.kwargs["cluster_slug"],
                                                self.vm.hostname])

    def delete(self, *args, **kwargs):
        vm = self.get_object()
        self._destroy(vm)
        return HttpResponseRedirect(self.get_success_url())

    def _destroy(self, instance):
        """
        Actually destroy a VM.

        Well, kind of. We won't destroy it immediately if it still exists in
        Ganeti; in that case, we'll only mark it for later removal and start
        the Ganeti job to destroy it.
        """

        # Check that the VM still exists in Ganeti. If it doesn't, then just
        # delete it.
        try:
            instance._refresh()
        except GanetiApiError, e:
            if e.code == 404:
                instance.delete()
                return
            raise

        # Clear any old jobs for this VM.
        ct = ContentType.objects.get_for_model(VirtualMachine)
        Job.objects.filter(content_type=ct, object_id=instance.id).delete()

        # Create the deletion job.
        job_id = instance.rapi.DeleteInstance(instance.hostname)
        job = Job.objects.create(job_id=job_id, obj=instance,
                                 cluster_id=instance.cluster_id)

        # Mark the VM as pending deletion. Also disable its cache.
        instance.last_job = job
        instance.ignore_cache = True
        instance.pending_delete = True
        instance.save()


@require_http_methods(["GET", "POST"])
@login_required
def reinstall(request, cluster_slug, instance):
    """
    Reinstall a VM.
    """

    user = request.user
    instance, cluster = get_vm_and_cluster_or_404(cluster_slug, instance)

    # Check permissions.
    # XXX Reinstalling is somewhat similar to
    # deleting in that you destroy data,
    # so use that for now.
    if not (
        user.is_superuser or
        user.has_any_perms(instance, ["remove", "admin"]) or
            user.has_perm("admin", cluster)):
        raise Http403(NO_PRIVS)

    if request.method == 'GET':
        return render_to_response(
            "ganeti/virtual_machine/reinstall.html",
            {'vm': instance, 'oschoices': cluster_os_list(cluster),
             'current_os': instance.operating_system,
             'cluster': cluster},
            context_instance=RequestContext(request),
        )

    elif request.method == 'POST':
        # Reinstall instance
        if "os" in request.POST:
            os = request.POST["os"]
        else:
            os = instance.operating_system

        # XXX no_startup=True prevents quota circumventions.
        # possible future solution would be a checkbox
        # asking whether they want to start up, and check
        # quota here if they do (would also involve
        # checking whether this VM is already running and subtracting that)

        job_id = instance.rapi \
            .ReinstallInstance(instance.hostname, os=os, no_startup=True)
        job = Job.objects.create(job_id=job_id, obj=instance, cluster=cluster)
        VirtualMachine.objects \
            .filter(id=instance.id).update(last_job=job, ignore_cache=True)

        # log information
        log_action('VM_REINSTALL', user, instance, job)

        return HttpResponseRedirect(
            reverse('instance-detail', args=[cluster.slug, instance.hostname]))


@login_required
def novnc(request,
          cluster_slug,
          instance,
          template="ganeti/virtual_machine/novnc.html"):
    vm = get_object_or_404(VirtualMachine, hostname=instance,
                           cluster__slug=cluster_slug)
    user = request.user
    if not (user.is_superuser
            or user.has_any_perms(vm, ['admin', 'power'])
            or user.has_perm('admin', vm.cluster)):
        return HttpResponseForbidden(_('You do not have permission '
                                       'to vnc on this'))

    return render_to_response(template,
                              {'cluster_slug': cluster_slug,
                               'instance': vm,
                               },
                              context_instance=RequestContext(request), )


@require_POST
@login_required
def vnc_proxy(request, cluster_slug, instance):
    vm = get_object_or_404(VirtualMachine, hostname=instance,
                           cluster__slug=cluster_slug)
    user = request.user
    if not (user.is_superuser
            or user.has_any_perms(vm, ['admin', 'power'])
            or user.has_perm('admin', vm.cluster)):
        return HttpResponseForbidden(_('You do not have permission '
                                       'to vnc on this'))

    use_tls = bool(request.POST.get("tls"))
    result = json.dumps(vm.setup_vnc_forwarding(tls=use_tls))

    return HttpResponse(result, mimetype="application/json")


@require_POST
@login_required
def shutdown(request, cluster_slug, instance):
    vm = get_object_or_404(VirtualMachine, hostname=instance,
                           cluster__slug=cluster_slug)
    user = request.user

    if not (user.is_superuser or user.has_any_perms(vm, ['admin', 'power']) or
            user.has_perm('admin', vm.cluster)):
        msg = _('You do not have permission to shut down this virtual machine')
        raise Http403(msg)

    try:
        job = vm.shutdown()
        job.refresh()
        msg = job.info

        # log information about stopping the machine
        log_action('VM_STOP', user, vm, job)
    except GanetiApiError, e:
        msg = {'__all__': [str(e)]}

    return HttpResponse(json.dumps(msg), mimetype='application/json')


@require_POST
@login_required
def shutdown_now(request, cluster_slug, instance):
    vm = get_object_or_404(VirtualMachine, hostname=instance,
                           cluster__slug=cluster_slug)
    user = request.user

    if not (user.is_superuser or user.has_any_perms(vm, ['admin', 'power']) or
            user.has_perm('admin', vm.cluster)):
        msg = _('You do not have permission to shut down this virtual machine')
        raise Http403(msg)

    try:
        job = vm.shutdown(timeout=0)
        job.refresh()
        msg = job.info

        # log information about stopping the machine
        log_action('VM_STOP', user, vm, job)
    except GanetiApiError, e:
        msg = {'__all__': [str(e)]}

    return HttpResponse(json.dumps(msg), mimetype='application/json')


@require_POST
@login_required
def startup(request, cluster_slug, instance, rest=False):
    vm = get_object_or_404(VirtualMachine, hostname=instance,
                           cluster__slug=cluster_slug)
    user = request.user
    if not (user.is_superuser or user.has_any_perms(vm, ['admin', 'power']) or
            user.has_perm('admin', vm.cluster)):
        msg = _('You do not have permission to start up this virtual machine')
        if rest:
            return {"msg": msg, "code": 403}
        else:
            raise Http403(msg)

    # superusers bypass quota checks
    if not user.is_superuser and vm.owner:
        # check quota
        quota = vm.cluster.get_quota(vm.owner)
        if any(quota.values()):
            used = vm.owner.used_resources(vm.cluster, only_running=True)

            if quota['ram'] is not None \
                    and (used['ram'] + vm.ram) > quota['ram']:
                msg = _('Owner does not have enough RAM remaining on '
                        'this cluster to start the virtual machine.')
                if rest:
                    return {"msg": msg, "code": 500}
                else:
                    return HttpResponse(json.dumps([0, msg]),
                                        mimetype='application/json')

            if quota['virtual_cpus'] and \
                    (used['virtual_cpus'] + vm.virtual_cpus) \
                    > quota['virtual_cpus']:
                msg = _('Owner does not have enough Virtual CPUs remaining '
                        'on this cluster to start the virtual machine.')
                if rest:
                    return {"msg": msg, "code": 500}
                else:
                    return HttpResponse(json.dumps([0, msg]),
                                        mimetype='application/json')

    try:
        job = vm.startup()
        job.refresh()
        msg = job.info

        # log information about starting up the machine
        log_action('VM_START', user, vm, job)
    except GanetiApiError, e:
        msg = {'__all__': [str(e)]}
    if rest:
        return {"msg": msg, "code": 200}
    else:
        return HttpResponse(json.dumps(msg), mimetype='application/json')


@login_required
def migrate(request, cluster_slug, instance):
    """
    view used for initiating a Node Migrate job
    """
    vm, cluster = get_vm_and_cluster_or_404(cluster_slug, instance)

    user = request.user
    if not (user.is_superuser or
            user.has_any_perms(cluster, ['admin', 'migrate'])):
        raise Http403(NO_PRIVS)

    if request.method == 'POST':
        form = MigrateForm(request.POST)
        if form.is_valid():
            try:
                job = vm.migrate(form.cleaned_data['mode'])
                job.refresh()
                content = json.dumps(job.info)

                # log information
                log_action('VM_MIGRATE', user, vm, job)
            except GanetiApiError, e:
                content = json.dumps({'__all__': [str(e)]})
        else:
            # error in form return ajax response
            content = json.dumps(form.errors)
        return HttpResponse(content, mimetype='application/json')

    else:
        form = MigrateForm()

    return render_to_response('ganeti/virtual_machine/migrate.html',
                              {'form': form, 'vm': vm, 'cluster': cluster},
                              context_instance=RequestContext(request))


@login_required
def replace_disks(request, cluster_slug, instance):
    """
    view used for initiating a Replace Disks job
    """
    vm, cluster = get_vm_and_cluster_or_404(cluster_slug, instance)
    user = request.user
    if not (user.is_superuser or
            user.has_any_perms(cluster, ['admin', 'replace_disks'])):
        raise Http403(NO_PRIVS)

    if request.method == 'POST':
        form = ReplaceDisksForm(vm, request.POST)
        if form.is_valid():
            try:
                job = form.save()
                job.refresh()
                content = json.dumps(job.info)

                # log information
                log_action('VM_REPLACE_DISKS', user, vm, job)
            except GanetiApiError, e:
                content = json.dumps({'__all__': [str(e)]})
        else:
            # error in form return ajax response
            content = json.dumps(form.errors)
        return HttpResponse(content, mimetype='application/json')

    else:
        form = ReplaceDisksForm(vm)

    return render_to_response('ganeti/virtual_machine/replace_disks.html',
                              {'form': form, 'vm': vm, 'cluster': cluster},
                              context_instance=RequestContext(request))


@require_POST
@login_required
def reboot(request, cluster_slug, instance, rest=False):
    vm = get_object_or_404(VirtualMachine, hostname=instance,
                           cluster__slug=cluster_slug)
    user = request.user
    if not (user.is_superuser or
            user.has_any_perms(vm, ['admin', 'power']) or
            user.has_perm('admin', vm.cluster)):

        if rest:
            return HttpResponseForbidden()
        else:
            raise Http403(_('You do not have permission to '
                            'reboot this virtual machine'))

    try:
        job = vm.reboot()
        job.refresh()
        msg = job.info

        # log information about restarting the machine
        log_action('VM_REBOOT', user, vm, job)
    except GanetiApiError, e:
        msg = {'__all__': [str(e)]}
    if rest:
        return HttpAccepted()
    else:
        return HttpResponse(json.dumps(msg), mimetype='application/json')


def ssh_keys(request, cluster_slug, instance, api_key):
    """
    Show all ssh keys which belong to users, who are specified vm's admin
    """
    if settings.WEB_MGR_API_KEY != api_key:
        return HttpResponseForbidden(_("You're not allowed to view keys."))

    vm = get_object_or_404(VirtualMachine, hostname=instance,
                           cluster__slug=cluster_slug)

    users = get_users_any(vm, ["admin", ]).values_list("id", flat=True)
    keys = SSHKey.objects \
        .filter(Q(user__in=users) | Q(user__is_superuser=True)) \
        .values_list('key', 'user__username') \
        .order_by('user__username')

    keys_list = list(keys)
    return HttpResponse(json.dumps(keys_list), mimetype="application/json")


@login_required
def detail(request, cluster_slug, instance, rest=False):
    """
    Display details of virtual machine.
    """
    vm, cluster = get_vm_and_cluster_or_404(cluster_slug, instance)

    user = request.user
    cluster_admin = (user.is_superuser or
                     user.has_any_perms(cluster, perms=['admin','create_vm']))

    if not cluster_admin:
        perms = user.get_perms(vm)

    if cluster_admin or 'admin' in perms:
        admin = True
        remove = True
        power = True
        modify = True
        migrate = True
        tags = True
    else:
        admin = False
        remove = 'remove' in perms
        power = 'power' in perms
        modify = 'modify' in perms
        tags = 'tags' in perms
        migrate = 'migrate' in perms

    if not (admin or power or remove or modify or tags):  # TODO REST
        raise Http403(_('You do not have permission to view '
                        'this virtual machines\'s details'))

    context = {
        'cluster': cluster,
        'instance': vm,
        'admin': admin,
        'cluster_admin': cluster_admin,
        'remove': remove,
        'power': power,
        'modify': modify,
        'migrate': migrate,
        "has_immediate_shutdown": has_shutdown_timeout(cluster),
    }

    # check job for pending jobs that should be rendered with a different
    # detail template.  This allows us to reduce the chance that users will do
    # something strange like rebooting a VM that is being deleted or is not
    # fully created yet.
    if vm.pending_delete:
        template = 'ganeti/virtual_machine/delete_status.html'
    elif vm.template:
        template = 'ganeti/virtual_machine/create_status.html'
        if vm.last_job:
            context['job'] = vm.last_job
        else:
            ct = ContentType.objects.get_for_model(vm)
            jobs_loc = Job.objects.order_by('-finished') \
                .filter(content_type=ct, object_id=vm.pk)
            if jobs_loc.count() > 0:
                context['job'] = jobs_loc[0]
            else:
                context['job'] = None
    else:
        template = 'ganeti/virtual_machine/detail.html'

    if rest:
        return context
    else:
        return render_to_response(template, context,
                                  context_instance=RequestContext(request), )


@login_required
def users(request, cluster_slug, instance, rest=False):
    """
    Display all of the Users of a VirtualMachine
    """
    vm, cluster = get_vm_and_cluster_or_404(cluster_slug, instance)

    user = request.user
    if not (user.is_superuser or user.has_perm('admin', vm) or
            user.has_perm('admin', cluster)):
        if rest:
            return {'msg': NO_PRIVS, 'code': 403}
        else:
            raise Http403(NO_PRIVS)

    url = reverse('vm-permissions', args=[cluster.slug, vm.hostname])
    return view_users(request, vm, url, rest=rest)


@login_required
def permissions(request, cluster_slug, instance, user_id=None, group_id=None):
    """
    Update a users permissions.
    """
    vm = get_object_or_404(VirtualMachine, hostname=instance,
                           cluster__slug=cluster_slug)

    user = request.user
    if not (user.is_superuser or user.has_perm('admin', vm) or
            user.has_perm('admin', vm.cluster)):
        raise Http403(NO_PRIVS)

    url = reverse('vm-permissions', args=[cluster_slug, vm.hostname])
    return view_permissions(request, vm, url, user_id, group_id)


@login_required
def object_log(request, cluster_slug, instance, rest=False):
    """
    Display all of the Users of a VirtualMachine
    """
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    vm = get_object_or_404(VirtualMachine, hostname=instance)

    user = request.user
    if not (user.is_superuser or user.has_perm('admin', vm) or
            user.has_perm('admin', cluster)):
        raise Http403(NO_PRIVS)

    if rest:
        return list_for_object(request, vm, True)
    else:
        return list_for_object(request, vm)


@login_required
def modify(request, cluster_slug, instance):
    vm, cluster = get_vm_and_cluster_or_404(cluster_slug, instance)

    user = request.user
    if not (user.is_superuser
            or user.has_any_perms(vm, ['admin', 'modify'])
            or user.has_perm('admin', cluster)):
        raise Http403(
            'You do not have permissions to edit this virtual machine')

    hv = get_hypervisor(vm)
    if hv == 'kvm':
        hv_form = KvmModifyVirtualMachineForm
        template = 'ganeti/virtual_machine/edit_kvm.html'
    elif hv == 'xen-pvm':
        hv_form = PvmModifyVirtualMachineForm
        template = 'ganeti/virtual_machine/edit_pvm.html'
    elif hv == 'xen-hvm':
        hv_form = HvmModifyVirtualMachineForm
        template = 'ganeti/virtual_machine/edit_hvm.html'
    else:
        hv_form = None
        template = 'ganeti/virtual_machine/edit_base.html'
        # XXX no matter what, we're gonna call hv_form() and die. Let's do it
        # louder than usual. >:3
        msg = "Hey, guys, implementation error in views/vm.py:modify"
        raise RuntimeError(msg)

    if request.method == 'POST':

        form = hv_form(vm, request.POST)

        form.owner = vm.owner
        form.vm = vm
        form.cluster = cluster
        if form.is_valid():
            data = form.cleaned_data
            request.session['edit_form'] = data
            request.session['edit_vm'] = vm.id
            return HttpResponseRedirect(
                reverse('instance-modify-confirm',
                        args=[cluster.slug,
                        vm.hostname]))

    elif request.method == 'GET':
        if 'edit_form' in request.session \
                and vm.id == request.session['edit_vm']:
            form = hv_form(vm, request.session['edit_form'])
        else:
            form = hv_form(vm)

    return render_to_response(
        template,
        {'cluster': cluster,
         'instance': vm,
         'form': form,
         'balloon': has_balloonmem(cluster)
         },
        context_instance=RequestContext(request),
    )


# XXX mother, did it need to be so long?
@login_required
def modify_confirm(request, cluster_slug, instance):
    vm, cluster = get_vm_and_cluster_or_404(cluster_slug, instance)

    hv = get_hypervisor(vm)
    if hv == 'kvm':
        hv_form = KvmModifyVirtualMachineForm
    elif hv == 'xen-pvm':
        hv_form = PvmModifyVirtualMachineForm
    elif hv == 'xen-hvm':
        hv_form = HvmModifyVirtualMachineForm
    else:
        hv_form = None
        # XXX no matter what, we're gonna call hv_form() and die. Let's do it
        # louder than usual. >:3
        msg = "Hey, guys, implementation error in views/vm.py:modify_confirm"
        raise RuntimeError(msg)

    user = request.user
    power = user.is_superuser or user.has_any_perms(vm, ['admin', 'power'])
    if not (user.is_superuser or user.has_any_perms(vm, ['admin', 'modify'])
            or user.has_perm('admin', cluster)):
        raise Http403(
            _('You do not have permissions to edit this virtual machine'))

    if request.method == "POST":
        if 'edit' in request.POST:
            return HttpResponseRedirect(
                reverse("instance-modify",
                        args=[cluster.slug, vm.hostname]))
        elif 'reboot' in request.POST or 'save' in request.POST:
            form = ModifyConfirmForm(request.POST)
            form.session = request.session
            form.owner = vm.owner
            form.vm = vm
            form.cluster = cluster

            if form.is_valid():
                beparams = {}
                data = form.cleaned_data
                rapi_dict = data['rapi_dict']
                nics = rapi_dict.pop('nics')
                beparams['vcpus'] = rapi_dict.pop('vcpus')
                if has_balloonmem(cluster):
                    beparams['maxmem'] = rapi_dict.pop('maxmem')
                    beparams['minmem'] = rapi_dict.pop('minmem')
                else:
                    beparams['memroy'] = rapi_dict.pop('memory')
                os_name = rapi_dict.pop('os')
                job_id = cluster.rapi.ModifyInstance(
                    instance,
                    nics=nics,
                    os_name=os_name,
                    hvparams=rapi_dict,
                    beparams=beparams)
                # Create job and update message on virtual machine detail page
                job = Job.objects.create(job_id=job_id,
                                         obj=vm,
                                         cluster=cluster)
                VirtualMachine.objects \
                    .filter(id=vm.id).update(last_job=job, ignore_cache=True)
                # log information about modifying this instance
                log_action('EDIT', user, vm)
                if 'reboot' in request.POST and vm.info['status'] == 'running':
                    if power:
                        # Reboot the vm
                        job = vm.reboot()
                        log_action('VM_REBOOT', user, vm, job)
                    else:
                        raise Http403(
                            _("Sorry, but you do not have permission "
                              "to reboot this machine."))

                # Redirect to instance-detail
                return HttpResponseRedirect(
                    reverse("instance-detail",
                            args=[cluster.slug, vm.hostname]))

        elif 'cancel' in request.POST:
            # Remove session variables.
            if 'edit_form' in request.session:
                del request.session['edit_form']
            # Redirect to instance-detail
            return HttpResponseRedirect(
                reverse("instance-detail", args=[cluster.slug, vm.hostname]))

    elif request.method == "GET":
        form = ModifyConfirmForm()

    session = request.session

    if not 'edit_form' in request.session:
        return HttpResponseBadRequest('Incorrect Session Data')

    data = session['edit_form']
    info = vm.info
    hvparams = info['hvparams']

    old_set = dict(
        vcpus=info['beparams']['vcpus'],
        os=info['os'],
    )
    if has_balloonmem(cluster):
        old_set['maxmem'] = info['beparams']['maxmem']
        old_set['minmem'] = info['beparams']['minmem']
    else:
        old_set['memory'] = info['beparams']['memory']
    nic_count = len(info['nic.links'])
    for i in xrange(nic_count):
        old_set['nic_link_%s' % i] = info['nic.links'][i]
        old_set['nic_mac_%s' % i] = info['nic.macs'][i]

    # Add hvparams to the old_set
    old_set.update(hvparams)

    instance_diff = {}
    fields = hv_form(vm, data).fields
    for key in data.keys():
        if key in ['memory', 'maxmem', 'minmem']:
            diff = compare(render_storage(old_set[key]),
                           render_storage(data[key]))
        elif key == 'os':
            oses = os_prettify([old_set[key], data[key]])
            if len(oses) > 1:
                """
                XXX - Special case for a cluster with two different types of
                  optgroups (i.e. Image, Debootstrap).
                  The elements at 00 and 10:
                    The optgroups
                  The elements at 010 and 110:
                    Tuple containing the OS Name and OS value.
                  The elements at 0101 and 1101:
                    String containing the OS Name
                """
                oses[0][1][0] = list(oses[0][1][0])
                oses[1][1][0] = list(oses[1][1][0])
                oses[0][1][0][1] = '%s (%s)' % (oses[0][1][0][1], oses[0][0])
                oses[1][1][0][1] = '%s (%s)' % (oses[1][1][0][1], oses[1][0])
                oses = oses[0][1] + oses[1][1]
                diff = compare(oses[0][1], oses[1][1])
            else:
                oses = oses[0][1]
                diff = compare(oses[0][1], oses[1][1])
            #diff = compare(oses[0][1], oses[1][1])
        if key in ['nic_count', 'nic_count_original']:
            continue
        elif key not in old_set.keys():
            diff = ""
            instance_diff[fields[key].label] = _('Added')
        else:
            diff = compare(old_set[key], data[key])

        if diff != "":
            label = fields[key].label
            instance_diff[label] = diff

    # remove mac if it has not changed
    for i in xrange(nic_count):
        if fields['nic_mac_%s' % i].label not in instance_diff:
            del data['nic_mac_%s' % i]

    # Repopulate form with changed values
    form.fields['rapi_dict'] = CharField(widget=HiddenInput,
                                         initial=json.dumps(data))

    return render_to_response(
        'ganeti/virtual_machine/edit_confirm.html', {
        'cluster': cluster,
        'form': form,
        'instance': vm,
        'instance_diff': instance_diff,
        'power': power,
        },
        context_instance=RequestContext(request),
    )


@login_required
def rename(request, cluster_slug, instance, rest=False, extracted_params=None):
    """
    Rename an existing instance
    """
    vm, cluster = get_vm_and_cluster_or_404(cluster_slug, instance)

    user = request.user
    if not (user.is_superuser or user.has_any_perms(vm, ['admin', 'modify'])
            or user.has_perm('admin', cluster)):
        raise Http403(
            _('You do not have permissions to edit this virtual machine'))

    if request.method == 'POST':
        form = RenameForm(vm, request.POST)
        params_ok = False
        if rest and extracted_params is not None:
            if all(k in extracted_params
                   for k in ("hostname", "ip_check", "name_check")):
                hostname = extracted_params['hostname']
                ip_check = extracted_params['ip_check']
                name_check = extracted_params['name_check']
                params_ok = True
            else:
                return HttpResponseBadRequest()

        if form.is_valid():
            data = form.cleaned_data
            hostname = data['hostname']
            ip_check = data['ip_check']
            name_check = data['name_check']

        if form.is_valid() or params_ok:
            try:
                # In order for rename to work correctly, the vm must first be
                #   shutdown.
                if vm.is_running:
                    job1 = vm.shutdown()
                    log_action('VM_STOP', user, vm, job1)

                job_id = vm.rapi.RenameInstance(vm.hostname, hostname,
                                                ip_check, name_check)
                job = Job.objects.create(job_id=job_id,
                                         obj=vm,
                                         cluster=cluster)
                VirtualMachine.objects.filter(pk=vm.pk) \
                    .update(hostname=hostname, last_job=job, ignore_cache=True)

                # slip the new hostname to the log action
                vm.newname = hostname

                # log information about creating the machine
                log_action('VM_RENAME', user, vm, job)

                if not rest:
                    return HttpResponseRedirect(
                        reverse('instance-detail',
                                args=[cluster.slug, hostname]))
                else:
                    return HttpAccepted()

            except GanetiApiError, e:
                msg = 'Error renaming virtual machine: %s' % e
                form._errors["cluster"] = form.error_class([msg])
                if rest:
                    return HttpResponse(400, content=msg)

    elif request.method == 'GET':
        form = RenameForm(vm)

    return render_to_response(
        'ganeti/virtual_machine/rename.html',
        {'cluster': cluster,
         'vm': vm,
         'form': form
         },
        context_instance=RequestContext(request), )


@login_required
def reparent(request, cluster_slug, instance):
    """
    update a virtual machine to have a new owner
    """
    vm, cluster = get_vm_and_cluster_or_404(cluster_slug, instance)

    user = request.user
    if not (user.is_superuser or user.has_perm('admin', cluster)):
        raise Http403(
            _('You do not have permissions to change the owner '
              'of this virtual machine'))

    if request.method == 'POST':
        form = ChangeOwnerForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            vm.owner = data['owner']
            vm.save(force_update=True)

            # log information about creating the machine
            log_action('VM_MODIFY', user, vm)

            return HttpResponseRedirect(
                reverse('instance-detail', args=[cluster_slug, instance]))

    else:
        form = ChangeOwnerForm()

    return render_to_response(
        'ganeti/virtual_machine/reparent.html', {
        'cluster': cluster,
        'vm': vm,
        'form': form
        },
        context_instance=RequestContext(request),
    )


@login_required
def job_status(request, id, rest=False):
    """
    Return a list of basic info for running jobs.
    """
    ct = ContentType.objects.get_for_model(VirtualMachine)
    jobs = Job.objects.filter(status__in=("error", "running", "waiting"),
                              content_type=ct,
                              object_id=id).order_by('job_id')
    jobs = [j.info for j in jobs]

    if rest:
        return jobs
    else:
        return HttpResponse(json.dumps(jobs), mimetype='application/json')


def recv_user_add(sender, editor, user, obj, **kwargs):
    """
    receiver for object_permissions.signals.view_add_user, Logs action
    """
    log_action('ADD_USER', editor, obj, user)


def recv_user_remove(sender, editor, user, obj, **kwargs):
    """
    receiver for object_permissions.signals.view_remove_user, Logs action
    """
    log_action('REMOVE_USER', editor, obj, user)


def recv_perm_edit(sender, editor, user, obj, **kwargs):
    """
    receiver for object_permissions.signals.view_edit_user, Logs action
    """
    log_action('MODIFY_PERMS', editor, obj, user)


view_add_user.connect(recv_user_add, sender=VirtualMachine)
view_remove_user.connect(recv_user_remove, sender=VirtualMachine)
view_edit_user.connect(recv_perm_edit, sender=VirtualMachine)
