from django.contrib.formtools.wizard import FormWizard, FormWizard

__author__ = 'kreneskyp'

from django import forms
from django.contrib.formtools.wizard import FormWizard
from django.test import TestCase

from muddle.workflows import Workflow

DONE = []
PROCESS_STEP = []
RENDER_TEMPLATE = []


def get_template(self, step):
    return 'muddle/workflows/tests/wizard.html'
FormWizard.get_template = get_template

class InstrumentedForm(forms.Form):
    def done(self, request, form):
        DONE.append(self.__class__)

    @classmethod
    def get_template(cls):
        return 'muddle/workflows/tests/%s.html' % cls.__name__

    def process_step(self, request, form, step):
        PROCESS_STEP.append(self.__class__)

    def render_template(self, request, form, previous_fields, steps, context):
        RENDER_TEMPLATE.append(self.__class__)

class Foo(InstrumentedForm):
    foo = forms.IntegerField()

class Bar(forms.Form):
    bar = forms.IntegerField()

class Xoo(InstrumentedForm):
    xoo = forms.IntegerField()


class WorkflowTest(TestCase):
    """
    Tests for the Workflow class
    """
    def setUp(self):
        self.tearDown()
    
    def tearDown(self):
        global DONE, PROCESS_STEP, RENDER_TEMPLATE
        DONE = []
        PROCESS_STEP = []
        RENDER_TEMPLATE = []

    def test_init(self):
        Workflow([Foo])
        Workflow([Foo, Bar])
        Workflow([Foo, Bar, Xoo])

    def test_done(self):
        workflow = Workflow([Foo])
        workflow.done(None, [Foo()])
        self.assertEqual(1, len(DONE))
        self.assertTrue(Foo in DONE)

    def test_done_no_method(self):
        workflow = Workflow([Bar])
        workflow.done(None, [Bar()])
        self.assertEqual(0, len(DONE))

    def test_done_multiple(self):
        workflow = Workflow([Foo, Bar, Xoo])
        workflow.done(None, [Foo(), Bar(), Xoo()])
        self.assertEqual(2, len(DONE))
        self.assertTrue(Foo in DONE)
        self.assertTrue(Xoo in DONE)

    def test_get_template(self):
        """
        Tests retrieving the template for the current step.

        XXX get_template will return the Form class instead of a template name
        since that is easier to check.
        """
        workflow = Workflow([Foo])
        template = workflow.get_template(0)
        self.assertEqual('muddle/workflows/tests/Foo.html', template)

    def test_get_template_no_method(self):
        workflow = Workflow([Bar])
        template = workflow.get_template(0)

    def test_render_template(self):
        workflow = Workflow([Foo])
        workflow.render_template(None, Foo(), None, 0)
        self.assertEqual(1, len(RENDER_TEMPLATE))
        self.assertTrue(Foo in RENDER_TEMPLATE)

    def test_render_template_no_method(self):
        workflow = Workflow([Bar])
        workflow.render_template(None, Bar(), None, 0)
        self.assertEqual(0, len(RENDER_TEMPLATE))

    def test_process_step(self):
        workflow = Workflow([Foo])
        workflow.process_step(None, Foo(), 0)
        self.assertEqual(1, len(PROCESS_STEP))
        self.assertTrue(Foo in PROCESS_STEP)

    def test_process_step_no_method(self):
        workflow = Workflow([Bar])
        workflow.render_template(None, Bar(), None, 0)
        self.assertEqual(0, len(PROCESS_STEP))