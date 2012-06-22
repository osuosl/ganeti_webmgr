from django.contrib.formtools.wizard import FormWizard



class Workflow(FormWizard):
    """
    Workflow is an extension of Django FormWizard that enables it to be
    pluggable.  Workflows are registered by a given app, and any other app can
    insert steps into the workflow.

    Workflows work mostly the same as a FormWizard except some methods have been
    extended to be pluggable.  Workflow.done(), Workflow.process_step(),
    Workflow.get_template(), and Workflow.render_template() will attempt to call
    the method of the same name on the Form class for the current step.  This
    allows the Form to encapsulate all logic for the step.

    For example if a Form wants the step to be conditionally modify its
    rendering it may implement render_template.

    These methods are optional and will be skipped if they do not exist.
    """

    def done(self, request, form_list):
        for form in form_list:
            if hasattr(form, 'get_template'):
                form.done(request, form)

    def process_step(self, request, form, step):
        return form.process_step(request, form, step)

    def get_template(self, step):
        klass = self.form_list[step]
        if hasattr(klass, 'get_template'):
            return klass.get_template()
        return super(Workflow, self).get_template(step)

    def render_template(self, request, form, previous_fields, step, context=None):
        if hasattr(form, 'render_template'):
            return form.render_template(request, form, previous_fields, step, context)
    