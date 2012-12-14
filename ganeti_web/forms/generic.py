from django import forms

class HelpTipsForm(forms.Form):
    # Add has_help_tip CSS class to all form fields with help_text
    def __init__(self, *args, **kwargs):
        super(HelpTipsForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            field = self.fields[field]
            # Make sure the help_text exists, and isn't empty.
            if hasattr(field, 'help_text') and (field.help_text != ''):
                field.widget.attrs['class'] = 'has_help_tip'

