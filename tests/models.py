from django.db import models

from core.models import Permissable

class Simple(models.Model):
    """
    A simple model with no relationships
    """
    owner = models.ForeignKey(Permissable, null=True)
    value = models.CharField(max_length='32')
    
    integer = models.IntegerField()
    char = models.CharField(max_length='2')
    text = models.TextField()
    datetime = models.DateTimeField()
    date = models.DateField()
    time = models.TimeField()

class Extended(models.Model):
    """
    Class that has been extended
    """
    owner = models.ForeignKey(Permissable)
    a = models.IntegerField()


class ChildA(Extended):
    """
    Class that extends another class
    """
    b = models.IntegerField()


class ChildA(Extended):
    """
    Class that extends another class
    """
    pass


class Complex(models.Model):
    """
    Model for testing relationships
    """
    owner = models.ForeignKey(Permissable, null=True)


class OneToOne(models.Model):
    """
    A one to one extension of a class
    """
    complex = models.OneToOneField(Complex, null=True)


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
    
    
class MultipleParentsParentA(models.Model):
    """
    Class for testing parent child paths
    """
    pass
    

class MultipleParentsParentB(models.Model):
    """
    Class for testing parent child paths
    """
    pass


class MultipleParentsChild(models.Model):
    """
    a class with multiple parents for testing different relationship paths
    """
    parent_a = models.ForeignKey(MultipleParentsParentA, null=True, related_name='children')
    parent_b = models.ForeignKey(MultipleParentsParentB, null=True, related_name='children')


class DepthTestRoot(models.Model):
    """
    model for testing indirect ownership
    """
    owner = models.ForeignKey(Permissable, null=True, related_name='depth_tests')


class DepthTestLevel1(models.Model):
    """
    model for testing indirect ownership
    """
    parent = models.ForeignKey(DepthTestRoot, null=True, related_name='child')


class DepthTestLevel2(models.Model):
    """
    model for testing indirect ownership
    """
    parent = models.ForeignKey(DepthTestLevel1, null=True, related_name='child')