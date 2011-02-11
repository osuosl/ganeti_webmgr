
class FormTestMixin():
    """
    Test mixin for testing forms
    """

    def assert_missing_fields(self, cls, data, fields):
        """
        Tests fields that should raise a required exception
        
        @param cls - form class
        @param data - dict of valid data
        @param fields - list of field names that are required
        """
        
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
        @param fields - list of tuples containing field name and value that is
        invalid for that field
        """
        # check required fields
        for name, value in fields:
            data_ = data.copy()
            data_[name] = value
            form = cls(data_)
            self.assertFalse(form.is_valid())