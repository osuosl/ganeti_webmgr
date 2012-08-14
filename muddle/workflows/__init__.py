from django.forms import Form

from muddle.core.apps.plugins import load_app_plugin

from muddle.workflows.registration import Workflow

__author__ = 'kreneskyp'
__all__ = ['initialize', 'create', 'append']

WORKFLOWS = {}
WORKFLOW_CREATION = {}
WORKFLOW_STEPS = {}

def initialize():
    """
    Initialize muddled workflows by search all INSTALLED_APPS for a workflow
    module.  Apps should define their workflows within this module.
    """

    # process all workflows first.  This ensures they are all recorded before we
    # start adding other steps to the workflow.
    def prepare_workflow(initial_step):
        assert(workflow not in WORKFLOW_CREATION, 'A workflow named "%s" already exists' % workflow)
        WORKFLOW_CREATION[initial_step.name]=initial_step
    load_app_plugin('workflows', InitialStep, prepare_workflow)

    # find all 
    def prepare_step(step):
        if not step.optional:
            assert(workflow in WORKFLOW_CREATION, 'A workflow named "%s" does not exist' % workflow)
        workflow_steps = WORKFLOW_STEPS.get(step.workflow, {})
        workflow_steps[step.name] = step
    load_app_plugin('workflows', Step, prepare_step)

    # Workflow builders must now be created from any additional steps that were
    # added.  This requires that steps be sorted into their proper order
    for name, loader in WORKFLOW_CREATION.items():

        steps = [loader.initial_step]
        added = [loader.initial_step.key]

        if name in WORKFLOW_STEPS:
            unsorted_steps = WORKFLOW_STEPS[name].copy()
            sorted_steps = []

            # first add any items with bounds on the initial step
            while added:
                adding = False
                key = added.pop(0).key
                for name, step in unsorted_steps.items():
                    if key in step.after or key in step.before:
                        # A key can be added relative to the step being
                        # processed.  add it to its sorted position
                        adding = True
                        add_sorted(sorted_steps, step)
                        added.append(step)
                        del unsorted_steps[name]
                        
                # if no new step was found then append the first step to the end
                # this meant that none of the steps have references to the steps
                # already in the workflow
                if not adding and unsorted_steps:
                    added.append(unsorted_steps.pop())


def add_sorted(list, step):
    """
    add a step to a sorted list
    """
    lower = None
    after = step.after.copy()
    after.reverse()
    if after:
        for key in after:
            if key in list:
                lower = list.index(key)
                break

    upper = None
    if step.before:
        for key in step.after:
            if key in list:
                upper = list.index(key)
                break

    if lower and upper:
        assert(upper < lower, 'Step "%s" has an impossible order' % step.key)
        list.insert(upper-1, step)

    elif lower:
        list.append(step)

    elif upper:
        list.insert(upper-1, step)


def create(klass, workflow, key=None):
    """
    Create a workflow, adding the supplied Form classes to the workflow in the
    order in which they are given

    @param klass: a workflow must have at least one step.  This should be a
    single Form class, or list of classes
    @param workflow: name for workflow.  This should be as unique as possible to
    avoid conflicts.
    @param key: name for the default step, defaults to name of Form class
    """
    assert(issubclass(klass, (Form,)), 'First argument to create must be a Form class')


    key = key if key else klass.__name__
    return WorkFlowLoader(workflow, klass, key)


def insert(klass, workflow, key=None, after=None, before=None, optional=True):
    """
    Inserts a Form class into an existing workflow.

    Rather than using indices this method uses Before and After to specify a
    a relative location within the list.  This allows position declarations to
    be dynamic and change based on other which apps are installed.
    
    For example a simple store checkout process may have the following steps:
    
    >>> print Checkout.form_list
    [Cart, Payment, Review, Confirmation]
    
    A Shipping step must be after the Cart, but before the customer has Paid.

    >>> insert('checkout', Shipping, after="cart", before="payment")
    >>> print Checkout.form_list
    [Cart, Shipping, Payment, Review, Confirmation]
    
    You may specify a list of steps that come before or after.  This allows an
    app to adjust to other steps as needed.

    >>> insert(Offers, 'checkout', after='cart', before=['shipping','payment'])
    
    You can be less explicit with your definition, specifying only a single
    bound.  In this case an alternative Offer screen is added before Payment.

    >>> insert(Offers, 'checkout', before="payment")

    Note that muddle can only build the workflow order based on the bounds you
    have defined.  It's possible that multiple steps will have the same bounds
    defined but no bounds declaring which order they should exist in.  They will
    be added in order, but the order in which apps are loaded is not guaranteed.

    >>> insert(Shipping, 'checkout', after="cart", before="payment")
    >>> insert(Offers, 'checkout', after="cart", before="payment")
    >>> print Checkout.form_list
    [Cart, Shipping, Offers, Payment, Review, Confirmation]

    If automatic bounds fail, then a project can always modify or replace bounds
    within settings.py

    @param klass: Form class to add
    @param workflow: name of workflow
    @param key: name for the default step, defaults to name of Form class
    @param after: key or list of keys which this step must come after
    @param before: key or list of keys which this step must come before
    @param optional: whether to raise an error if the requested workflow does
    not exist
    """
    assert(issubclass(klass, (Form,)), 'First argument to create must be a Form class')

    key = key if key else klass.__name__
    workflow = WORKFLOW_STEPS.get(workflow, {})
    return Step(klass, key, after, before)


class WorkFlowLoader(object):
    """
    The first step that is added for a workflow.  This step is special in that
    it triggers the creation of the workflow.  All other steps added are
    relative to this base.

    This is not a functional class, it is used merely for marking up classes
    during the workflow initialization process
    """
    
    def __init__(self, name, initial_form, initial_step_key):
        self.name = name
        self.initial = Step(initial_form, initial_step_key)


class Step(object):
    """
    A step

    This is not a functional class, it is used merely for marking up classes
    during the workflow initialization process
    """
    
    def __init__(self, form, key, after=None, before=None):
        self.form = form
        self.key = key
        self.after = after
        self.before = before