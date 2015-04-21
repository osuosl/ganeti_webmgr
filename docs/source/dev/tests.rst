:orphan:

.. _testing:

Writing Tests
=============

Ganeti Web Manager has a fairly complete test suite. New code should have matching tests. Before committing code, run the suite for Ganeti Web Manager and `Object Permissions <http://code.osuosl.org/projects/object-permissions>`_

::

    ./ganeti_webmgr/manage.py test ganeti_web
    ./ganeti_webmgr/manage.py test object_permissions


Clean up after yourself
'''''''''''''''''''''''

Remember to tear down any resources you set up in your tests. Don't use "YourModel.objects.all().delete()" to clean up your objects; it could be hiding bugs. Clean up exactly the resources you  created.

Test your setups and teardowns
''''''''''''''''''''''''''''''

To speed up analysis of broken tests, if you have a setUp() or tearDown() in a TestCase, add a   test\_trivial() method which is empty. It will pass if your setUp() and tearDown() work.

Views
'''''

All views should be thoroughly tested for security, checking to ensure that the proper HTTP      codes are returned.

-  Test Anonymous User access
-  Test Permission based access
-  Test Superuser based access

Check for invalid input.

-  missing fields
-  invalid data for field

Templates & Javascript
''''''''''''''''''''''

The test suite does not yet include full selenium tests for verifying Javascript functionality.  Some basic tests can be performed using Django's test suite:

-  Check objects in the context: forms, lists of objects, etc.
-  Check for existence of values in forms.

See :ref:`selenium` for more information on what Selenium can test within GWM.



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
