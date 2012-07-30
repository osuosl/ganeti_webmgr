import cPickle

from django.db import models


class AppSettingsCategory(models.Model):
    """
    model for storing settings for an app.  This class
    """
    name = models.CharField(max_length=256)


class AppSettingsValue(models.Model):
    """
    An individual app setting value.
    """
    category = models.ForeignKey(AppSettingsCategory, related_name='values')
    key = models.CharField(max_length=64)
    serialized_data = models.CharField(max_length=512)

    @property
    def data(self):
        if self._data:
            self._data = cPickle.loads(self.serialized_data)
        return self._data

    @data.setter
    def data(self, value):
        # clear serialized data, don't know if we'll need to save it
        self.serialized_data = None
        self._data = value

    def save(self, *args, **kwargs):
        if self.serialized_data is None:
            self.serialized_data = cPickle.dumps(self._data)
        super(AppSettingsValue, self).save(*args, **kwargs)
