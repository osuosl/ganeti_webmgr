from django.conf import settings
from django.db import models

# Models for testing
if settings.TESTING:
    class TestModel(models.Model):
        value = models.IntegerField(null=True)
        value2 = models.IntegerField(null=True)
    class TestModelChild(models.Model):
        value = models.IntegerField(null=True)
        value2 = models.IntegerField(null=True)
        parent = models.ForeignKey(TestModel, null=True)
    class TestModelChildChild(models.Model):
        value = models.IntegerField(null=True)
        value2 = models.IntegerField(null=True)
        parent = models.ForeignKey(TestModelChild, null=True)