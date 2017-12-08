from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class DataFile(models.Model):
    filename = models.CharField(max_length=250)
    tempCode = models.CharField(max_length=250)
    date = models.DateTimeField('date added')

    def __str__(self):
        return self.filename + "  path: " + self.get_path()

    def get_path(self):
        return "temp/" + str(self.tempCode)

    def get_name(self):
        return self.tempCode


@python_2_unicode_compatible
class Image(models.Model):
    src = models.CharField(max_length=250)
    alt = models.CharField(max_length=250)
    style = models.CharField(max_length=250)
