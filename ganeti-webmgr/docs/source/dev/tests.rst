Writing Tests
=============

Any assert statement will take the optional kwarg of 'msg'. This kwarg
will be output instead of an error in the test. It is a very useful
argument for debugging.
::

    self.assertTrue(False, msg="And what else floats? A duck!")

Forms
-----

Here are a few pointers for testing forms.

If there is an error in the test for form.is\_valid() a good way to find
out what form fields are giving trouble is by checking form.errors.
::

    form = MyFormWithErrors()
    self.assertTrue(form.is_valid(), msg=form.errors)

All Django forms generally accept 'initial', 'instance', and 'data'
keyword arguments, but forms will behave differently depending on which
of these arguments you pass in.

**data**

This is probably the easiest of all the form tests to work with, because
it is what you are so used to seeing.
::

    # data is a dictionary
    form = MyForm(data)
    self.assertTrue(form.is_bound)
    self.assertTrue(form.is_valid())
    for field in form.fields:
        self.assertEqual(data[field], form.cleaned_data[field])

**initial**

Initial is a unique case in which I have not found an easy way to check
if the initial values of the form were properly set.
Checking against **form.fields[field].initial** will not work as this is
set to the value of the initial keyword argument originally passed into
the form field.
::

    # initial is a dictionary
    form = MyForm(initial=initial)
    self.assertFalse(form.is_bound)
    self.assertFalse(form.is_valid())
    for field in form.fields:
        self.assertEqual(initial[field], form.fields[field].initial) # This will *NOT* work!

**instance**

Forms that are passed the instance keyword argument will have set the
'instance' property on form.
Thus you can test form.instance against the instance you passed in.
::

    # instance is an instance of a model
    form = MyModelForm(instance=instance)
    self.assertEqual(instance, form.instance)
