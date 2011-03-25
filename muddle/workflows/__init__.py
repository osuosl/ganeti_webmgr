from muddle.core.apps.plugins import load_app_plugin

from muddle.workflows.registration import Workflow

__author__ = 'kreneskyp'

WORKFLOWS = {}


def initialize():
    """
    Initialize muddled workflows by search all INSTALLED_APPS for a workflow
    module.  Apps should define their workflows within this module.
    """
    load_app_plugin('workflow')


def create(key, klass):
    """
    Create a workflow, adding the supplied Form classes to the workflow in the
    order in which they are given

    @param key: name for workflow.  This should be as unique as possible to
    avoid conflicts.
    @param klass: a workflow must have at least one step.  This should be a
    single Form class, or list of classes
    """
    pass

def add_step(key, klass, optional):
    """
    Add a step to an existing Workflow.  This will fail silently if the
    requested workflow does not exist.

    @param key: name of workflow
    @param klass: Form class to add
    """
