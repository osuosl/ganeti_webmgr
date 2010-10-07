from django import forms
from django.contrib.auth.models import User

from object_permissions import get_user_perms, get_model_perms, grant, revoke
from object_permissions.models import UserGroup


class ObjectPermissionForm(forms.Form):
    """
    Form used for editing permissions
    """
    permissions = forms.MultipleChoiceField(required=False, \
                                            widget=forms.CheckboxSelectMultiple)
    user = forms.ModelChoiceField(queryset=User.objects.all(), required=False)
    group = forms.ModelChoiceField(queryset=UserGroup.objects.all(), \
                                   required=False)
    
    def __init__(self, object, *args, **kwargs):
        """
        @param object - the object being granted permissions
        """
        super(ObjectPermissionForm, self).__init__(*args, **kwargs)
        self.object = object
        model_perms = get_model_perms(object)
        self.fields['permissions'].choices = zip(model_perms, model_perms)

    def clean(self):
        """
        validates:
            * mutual exclusivity of user and group
            * a user or group is always selected and set to 'grantee'
        """
        data = self.cleaned_data
        user = data.get('user')
        group = data.get('group')
        if not (user or group) or (user and group):
            raise forms.ValidationError('Choose a group or user')
        
        # add whichever object was selected
        data['grantee'] = user if user else group
        return data
    
    def update_perms(self):
        """
        updates perms for the user based on values passed in
            * grant all perms selected in the form.  Revoke all
            * other available perms that were not selected.
            
        @return list of perms the user now possesses
        """
        perms = self.cleaned_data['permissions']
        grantee = self.cleaned_data['grantee']
        grantee.set_perms(perms, self.object)
    

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
        data = super(ObjectPermissionFormNewUsers, self).clean()
        
        if 'grantee' in data:
            grantee = data['grantee']
            perms = data['permissions']
            
            # if grantee does not have permissions, then this is a new user:
            #    - permissions must be selected
            if not grantee.get_perms(self.object) and not perms:
                msg = "You must grant at least 1 permission for new users and "
                "groups"
                self._errors["permissions"] = self.error_class([msg])
        
        return data