from django.db import models

from muddle.models import Permissable

class Device(models.Model):
    owner = models.ForeignKey(Permissable, related_name='devices')
    name = models.CharField(max_length=64)


class NetworkCard(models.Model):
    device = models.ForeignKey(Device, related_name='network_cards')
    mac = models.CharField(max_length=64)


class Location(models.Model):
    device = models.OneToOneField(Device, related_name='location')
    pass


class Rack(models.Model):
    row = models.PositiveIntegerField()
    column = models.PositiveIntegerField()


class RackU(Location):
    rack = models.ForeignKey(Rack, related_name='servers')
    u = models.IntegerField()
    

class Closet(models.Model):
    building = models.CharField(max_length=64)
    floor = models.CharField(max_length=2)


class ClosetLocation(Location):
    closet = models.ForeignKey(Closet)
    position = models.CharField(max_length='128')