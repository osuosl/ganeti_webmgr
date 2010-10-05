from django import forms
from django.contrib.auth.models import User

from object_permissions import get_user_perms, get_model_perms, grant, revoke


class ObjectPermissionForm(forms.Form):
    """
    Form used for editing permissions
    """
    permissions = forms.MultipleChoiceField(required=False, \
                                            widget=forms.CheckboxSelectMultiple)
    user = forms.ModelChoiceField(queryset=User.objects.all())

    def __init__(self, object, *args, **kwargs):
        """
        @param object - the object being granted permissions
        """
        super(ObjectPermissionForm, self).__init__(*args, **kwargs)
        self.object = object
        model_perms = get_model_perms(object)
        self.fields['permissions'].choices = zip(model_perms, model_perms)
    
    def update_perms(self):
        """
        updates perms for the user based on values passed in
            * grant all perms selected in the form.  Revoke all
            * other available perms that were not selected.
            
        @return list of perms the user now possesses
        """
        object = self.object
        model_perms = get_model_perms(object)
        perms = self.cleaned_data['permissions']
        user = self.cleaned_data['user']
        for perm in perms:
            grant(user, perm, object)
        for perm in [p for p in model_perms if p not in perms]:
            revoke(user, perm, object)
        return perms


class ObjectPermissionFormNewUsers(ObjectPermissionForm):
    """
    A subclass of permission form that enforces an addtional rule that new users
    must be granted at least one permission.  This is used for objects that
    determine group membership (e.g. listing users with acccess) based on who
    has permissions.
    
    This is different from objects that grant inherent permissions through a
    different membership relationship (e.g. Users in a UserGroup inherit perms)
    """
    
    def clean(self):
        data = self.cleaned_data
        if 'user' in data:
            user = data['user']
            perms = data['permissions']
            
            # if user does not have permissions, then this is a new user:
            #    - permissions must be selected
            if not user.get_perms(self.object) and not perms:
                msg = "You must grant at least 1 permission for new users"
                self._errors["permissions"] = self.error_class([msg])
        else:
            msg = "User is required"
            self._errors["user"] = self.error_class([msg])
        
        return data