from django.db import models

class Device(models.Model):
    name = models.CharField(max_length=64)
    

class NetworkCard(models.Model):
    device = models.ForeignKey(Device, related_name='network_cards')
    mac = models.CharField(max_length=64)

class Location(models.Model):
    device = models.OneToOneField(Device, related_name='location')
    pass
    
class Rack(Location):
    row = models.PositiveIntegerField()
    column = models.PositiveIntegerField()

class Closet(Location):
    building = models.CharField(max_length=64)
    floor = models.CharField(max_length=2)
    