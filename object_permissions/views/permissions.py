from django import forms
from django.contrib.auth.models import User

from object_permissions import get_model_perms, grant, revoke


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