from django.db import models

from core.models import Permissable

class Simple(models.Model):
    """
    A simple model with no relationships
    """
    owner = models.ForeignKey(Permissable)
    value = models.CharField(max_length='32')

class Extended(models.Model):
    """
    Class that has been extended
    """
    owner = models.ForeignKey(Permissable)


class ChildA(Extended):
    """
    Class that extends another class
    """
    pass


class ChildA(Extended):
    """
    Class that extends another class
    """
    pass


class Complex(models.Model):
    """
    Model for testing relationships
    """
    owner = models.ForeignKey(Permissable)


class OneToOne(models.Model):
    """
    A one to one extension of a class
    """
    complex = models.OneToOneField(Complex)


class OneToMany(models.Model):
    """
    A one to many extension of a class
    """
    complex = models.ForeignKey(Complex, related_name='one_to_manys')


class ManyToMany(models.Model):
    """
    A many to many extension of a class
    """
    complex = models.ManyToManyField(Complex, related_name='many_to_manys')


class Recursive(models.Model):
    """
    Class that references itself
    """
    parent = models.ForeignKey('self', related_name='children')