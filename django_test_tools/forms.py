
class FormTestMixin():
    """
    Test mixin for testing forms
    """

    def assert_missing_fields(self, cls, data, fields=None):
        """
        Tests fields that should raise a required exception
        
        @param cls - form class
        @param data - dict of valid data
        @param fields - list of field names that are required
        """
        fields = data.keys if fields is None else fields

        # check required fields
        for name in fields:
            data_ = data.copy()
            del data_[name]
            form = cls(data_)
            self.assertFalse(form.is_valid())
    
    def assert_invalid_value(self, cls, data, fields):
        """
        Tests fields that should raise an error for a specific type of invalid
        data.
        
        @param cls - form class
        @param data - dict of valid data
        @param fields - list of dicts containing field name and values that result
        in form errors.
        """
        # check required fields
        for values in fields:
            data_ = data.copy()
            data_.update(values)
            form = cls(data_)
            self.assertFalse(form.is_valid())