from django.template import TemplateDoesNotExist, Template
from django.template.loaders import app_directories

TEST_TEMPLATES = {
    'foo1.html':'',
    'foo2.html':'',
    'foo3.html':'',
    'foo4.html':'',
}

class TestLoader(app_directories.Loader):
    is_usable = True

    def load_template(self, template_name, template_dirs=None):
        try:
            source = TEST_TEMPLATES[template_name]
        except KeyError:
            raise TemplateDoesNotExist()

        return Template(source), template_name