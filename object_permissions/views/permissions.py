from django import forms
from django.contrib.auth.models import User


class ObjectPermissionForm(forms.Form):
    """
    Form used for editing permissions
    """
    permissions = forms.MultipleChoiceField(required=False, \
                                            widget=forms.CheckboxSelectMultiple)
    user_id = None

    def __init__(self, user_id, choices=[], *args, **kwargs):
        super(ObjectPermissionForm, self).__init__(*args, **kwargs)
        self.user_id = user_id
        self.fields['permissions'].choices = choices
    
    def clean(self):
        try:
            user = User.objects.get(id=self.user_id)
            self.cleaned_data['user'] = user
            return self.cleaned_data
        except User.DoesNotExist:
            raise forms.ValidationError("Invalid User")