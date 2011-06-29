# Copyright (C) 2010 Oregon State University et al.
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

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, SetPasswordForm
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext,loader
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy


def render_403(request, message):
    """
    Render a 403 response
    """
    template = loader.get_template('403.html')
    context = RequestContext(request, {
        'message': message,
    })
    return HttpResponseForbidden(template.render(context))


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(label=_("Email Address"), max_length=100)


@login_required
def user_list(request, template="user/list.html"):
    user = request.user
    if not user.is_superuser:
        return render_403(request, _('Only a superuser may view all users.'))

    users = User.objects.all()

    return render_to_response(template, {
            'userlist':users
        },
        context_instance=RequestContext(request),
    )


@login_required
def user_add(request, template="user/edit.html"):
    user = request.user
    if not user.is_superuser:
        return render_403(request, _('Only a superuser may add a user.'))

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            new_user = User(username=data['username'])
            new_user.set_password(data['password2'])
            new_user.email=data['email']
            new_user.save()
            return HttpResponseRedirect(new_user.get_absolute_url())

    else:
        form = CustomUserCreationForm()

    return render_to_response(template, {
            'form':form,
        },
        context_instance=RequestContext(request),
    )


@login_required
def user_detail(request, user_id=None, template="user/detail.html"):
    user = request.user
    if not user.is_superuser:
        return render_403(request, _('Only a superuser may view a user.'))

    user = get_object_or_404(User, id=user_id)

    return render_to_response(template, {
            'user_detail':user,
        },
        context_instance=RequestContext(request),
    )


@login_required
def user_edit(request, user_id=None, template="user/edit.html"):
    user = request.user
    if not user.is_superuser:
        return render_403(request, _('Only a superuser may edit a user.'))

    user_edit = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = UserEditForm(data=request.POST, instance=user_edit)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(user_edit.get_absolute_url())

    elif request.method == "DELETE":
        user_edit.delete()
        return HttpResponse('1', mimetype='application/json')

    else:
        form = UserEditForm(instance=user_edit)

    return render_to_response(template, {
            'form':form,
            'user_edit':user_edit,
        },
        context_instance=RequestContext(request),
    )


@login_required
def user_password(request, user_id=None, template="user/password.html"):
    user = request.user
    if not user.is_superuser:
        return render_403(request, _('Only superusers have access to the change \
                                     password form.'))

    user_edit = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = SetPasswordForm(user=user_edit, data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('user-list'))
    else:
        form = SetPasswordForm(user=user_edit)

    return render_to_response(template, {
            'form':form,
            'username':user_edit,
        },
        context_instance=RequestContext(request),
    )


@login_required
def user_profile(request, template='user/profile.html'):
    """
    Form for editing a User's Profile
    """
    form = None
    user = request.user
    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        form.user = user
        if form.is_valid():
            data = form.cleaned_data
            user.email = data['email']
            if data['new_password']:
                user.set_password(data['new_password'])
            user.save()
            user.get_profile().save()
            form = None
            messages.add_message(request, messages.SUCCESS,
                                 _('Saved successfully'))

    if not form:

        form = UserProfileForm(initial={'email':user.email,
                                        'old_password':'',
                                        })

    return render_to_response(template,
    {'form':form},
     context_instance=RequestContext(request))


class UserEditForm(UserChangeForm):
    """
    Form to edit user, based on Auth.UserChangeForm
    """

    new_password1 = forms.CharField(label=ugettext_lazy('New password'),
                                    widget=forms.PasswordInput, required=False)
    new_password2 = forms.CharField(label=ugettext_lazy('Confirm password'),
                                    widget=forms.PasswordInput, required=False)

    class Meta(UserChangeForm.Meta):
        fields = (
            'username',
            #'first_name',
            #'last_name',
            'email',
            'is_active',
            'is_superuser',
        )

    def __init__(self, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)

    def clean_new_password2(self):
        password2 = self.cleaned_data.get('new_password2')
        if self.cleaned_data.get('new_password1') != password2:
            raise forms.ValidationError(_("The two password fields didn't match."))
        return password2

    def save(self, commit=True):
        password1 = self.cleaned_data.get('new_password1')
        if password1 and self.cleaned_data.get('new_password2'):
            self.instance.set_password(password1)
        return super(UserEditForm, self).save(commit)


class UserProfileForm(forms.Form):
    """
    Form for editing a User's Profile
    """
    email = forms.EmailField(label=ugettext_lazy('E-mail'))
    old_password = forms.CharField(label=ugettext_lazy('Old password'), required=False, widget=forms.PasswordInput)
    new_password = forms.CharField(label=ugettext_lazy('New password'), required=False, widget=forms.PasswordInput)
    confirm_password = forms.CharField(label=ugettext_lazy('Confirm password'), required=False, widget=forms.PasswordInput)

    # needed to verify the user's password
    user = None

    def clean(self):
        """
        Overridden to add password change verification
        """
        data = self.cleaned_data
        old = data.get('old_password')
        new = data.get('new_password')
        confirm = data.get('confirm_password')

        if new or confirm:
            if not self.user.check_password(old):
                del data['old_password']
                msg = _('Old Password is incorrect')
                self._errors['old_password'] = self.error_class([msg])

            if not new:
                if 'new_password' in data: del data['new_password']
                msg = _('Enter a new password')
                self._errors['new_password'] = self.error_class([msg])

            if not confirm:
                if 'confirm_password' in data: del data['confirm_password']
                msg = _('Confirm new password')
                self._errors['confirm_password'] = self.error_class([msg])

            if new and confirm and new != confirm:
                del data['new_password']
                del data['confirm_password']
                msg = _('New passwords do not match')
                self._errors['new_password'] = self.error_class([msg])

        return data
