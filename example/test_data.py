# generates some test data

from muddle.models import *
from servers.models import *
from muddle.plugins.registerable import PERM_READ, PERM_WRITE

# delete old data
Group.objects.all().delete()
Device.objects.all().delete()
ClosetLocation.objects.all().delete()
RackU.objects.all().delete()
Rack.objects.all().delete()
Closet.objects.all().delete()
NetworkCard.objects.all().delete()
Permission.objects.all().delete()

# get user profiles
try:
    up1 = UserProfile.objects.get(id=2)
except UserProfile.DoesNotExist:
    up1 = UserProfile()
    up1.id=2
    up1.save()

try:
    up2 = UserProfile.objects.get(id=3)
except UserProfile.DoesNotExist:
    up2 = UserProfile()
    up2.id = 3
    up2.save()

# groups
g1 = Group(name='Group 1')
g1.save()
g2 = Group(name='Group 2')
g2.save()
up1.groups.add(g1)
up2.groups.add(g2)

# permissions - group 1
p = Permission(path='Device.owner.1', mask=PERM_READ|PERM_WRITE, granted_to=g1)
p.save()
p = Permission(path='Device', mask=PERM_READ, granted_to=g1)
p.save()
p = Permission(path='Rack', mask=PERM_READ, granted_to=g1)
p.save()
p = Permission(path='NetworkCard.device.owner.1', mask=PERM_READ|PERM_WRITE, granted_to=g1)
p.save()
p = Permission(path='Location.device.owner.1', mask=PERM_READ|PERM_WRITE, granted_to=g1)
p.save()

# permissions - group 2
p = Permission(path='Device.owner.1', mask=PERM_READ|PERM_WRITE, granted_to=g2)
p.save()
p = Permission(path='Rack', mask=PERM_READ, granted_to=g2)
p.save()
p = Permission(path='NetworkCard.device.owner.1', mask=PERM_READ, granted_to=g2)
p.save()
p = Permission(path='Location.device.owner.1', mask=PERM_READ|PERM_WRITE, granted_to=g2)
p.save()

# racks
r = Rack(id=1, row=1, column=2)
r.save()

# closet
c = Closet(id=1, building='kelly eng', floor='2')
c.save()


# servers
s1 = Device(id=1, name='Server 1', owner=g1)
s1.save()
s2 = Device(id=2, name='Server 2', owner=g1)
s2.save()
s3 = Device(id=3, name='Switch 1', owner=g2)
s3.save()
s4 = Device(id=4, name='Switch 2', owner=g2)
s4.save()


# closet locations
cl1 = ClosetLocation(position='Next to the broom',  device=s3, closet=c)
cl1.save()
cl1 = ClosetLocation(position='on the shelf', device=s4, closet=c)
cl1.save()

# rack location
ru1 = RackU(rack=r, device=s1, u=1)
ru1.save()
ru2 = RackU(rack=r, device=s2, u=3)
ru2.save()

# network cards
n = NetworkCard(id=1, mac='00:00:00:00:00:00', device=s1)
n.save()
n = NetworkCard(id=2, mac='00:11:00:11:00:11', device=s2)
n.save()
n = NetworkCard(id=3, mac='22:11:22:11:00:11', device=s3)
n.save()
n = NetworkCard(id=4, mac='AA:11:00:11:00:11', device=s3)
n.save()
n = NetworkCard(id=5, mac='BB:BB:00:11:00:11', device=s4)
n.save()
n = NetworkCard(id=6, mac='DD:DD:DD:11:00:11', device=s4)
n.save()
n = NetworkCard(id=7, mac='55:55:00:55:00:11', device=s4)
n.save()
