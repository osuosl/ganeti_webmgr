from copy import copy

from django.forms import Form
from django.forms.util import ErrorDict

class InvalidFieldsException(Exception):
    """
    Fields were invalid.
    """

def merge_dict(dst, src):
    """
    Merge two dictionaries that contain lists.  elements from src are added
    to the same list in dst.
    """
    for k, v in src.items():
        dst[k] = dst[k]+v if k in dst else v


class AggregateForm(Form):

    def __init__(self, *args, **kwargs):
        self.forms = [cls(*args, **kwargs) for cls in self.form_classes]
        super(AggregateForm, self).__init__(*args, **kwargs)

    @classmethod
    def aggregate(cls, forms, options=None):
        """
        Aggregates form classes together to make a new class.
        """
        fields = {'form_classes': forms}

        for form in forms:
            for name, field in form.base_fields.items():
                if name in fields:
                    # If fields are conflicting, their properties must be
                    # merged. The "required" flag merges with a Boolean OR
                    # over all forms; the "initial" attribute merges forward
                    # with most recent value taking precedence.
                    if not fields[name].required:
                        fields[name].required = field.required
                    if field.initial is not None:
                        fields[name].initial = field.initial
                else:
                    # The first field added always retains all of its
                    # properties. Just copy it over.
                    fields[name] = copy(field)

        # Apply options, if any.
        if options:
            for name, properties in options.items():
                if name in fields:
                    for prop, value in properties.items():
                        setattr(fields[name], prop, value)

        return type('AggregateForm', (AggregateForm,), fields)

    def is_valid(self):
        """
        aggregates validation from all child forms.  Will run is_valid on each
        form and then aggregate the errors and or cleaned_data.
        """
        cleaned_data = {}
        errors = ErrorDict()

        for form in self.forms:
            if form.is_valid():
                cleaned_data.update(form.cleaned_data)
            else:
                merge_dict(errors, form.errors)

        if errors:
            # XXX set _errors instead of errors since django doesn't like it
            # when you set errors directly
            self._errors = errors
            return False

        self.cleaned_data = cleaned_data
        return True
