from django.forms import Form


def merge_dict(dst, src):
    """
    Merge two dictionaries that contain lists.  elements from src are added
    to the same list in dst.
    """
    for k, v in src.items():
        dst[k] = dst[k]+v if k in dst else v


class AggregateForm(Form):

    @classmethod
    def aggregate(cls, forms, options=None):
        """
        Aggregates form classes together to make a new class.
        """
        fields = {}

        for form in forms:
            for name, field in form.base_fields.items():
                if name in fields:
                    # if fields are conflicting their properties must be merged
                    AggregateForm._merge_field(fields[name], field)
                else:
                    # the first field added always retains all of its properties
                    # just add it.
                    fields[name] = field

        # apply options if any.
        if options:
            for name, properties in options.items():
                if name in fields:
                    field = fields[name]
                    for property, value in properties.items():
                        setattr(field, property, value)
                
        return type('AggregateForm', (AggregateForm,), fields)

    @classmethod
    def _merge_field(cls, dst, src):
        """
        Merge the properties of two form fields together:
           * required must be required if either field is required
        """
        # basic overrides that can be determined based on value, otherwise
        # properties are set on a first come first served basis
        dst.required = dst.required or src.required
        if not src.initial is None:
            dst.initial = src.initial

    def is_valid(self):
        """
        aggregates validation from all child forms.  Will run is_valid on each
        form and then aggregate the errors and or cleaned_data.
        """
        cleaned_data = {}
        errors = {}

        for form in self.forms():
            if form.is_valid():
                cleaned_data.update(form.cleaned_data)
            else:
                merge_dict(errors, form.errors)

        if errors:
            # set using dict as form does something wierd to prevent setting it
            # self.__dict__['errors'] = None if valid else errors
            self.errors = errors
            return False

        self.cleaned_data = cleaned_data
        return True