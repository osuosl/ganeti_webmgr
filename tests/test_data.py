# generates some test data

from core.models import *
from servers.models import *


# get user profiles
up1 = UserProfile.objects.get(id=1)
up2 = UserProfile.objects.get(id=2)

# groups
g1 = Group(name='Group 1')
g1.save()
g2 = Group(name='Group 2')
g2.save()
up1.groups.add(g1)
up2.groups.add(g2)

# racks
r = Rack(row=1, column=2)
r.save()

# closet
c = Closet(building='kelly eng', floor='2')
c.save()


# servers
s1 = Device(name='Server 1', owner=g1)
s1.save()
s2 = Device(name='Server 2', owner=g1)
s2.save()
s3 = Device(name='Switch 1', owner=g2)
s3.save()
s4 = Device(name='Switch 2', owner=g2)
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
n = NetworkCard(mac='00:00:00:00:00:00', device=s1)
n.save()
n = NetworkCard(mac='00:11:00:11:00:11', device=s2)
n.save()
n = NetworkCard(mac='22:11:22:11:00:11', device=s3)
n.save()
n = NetworkCard(mac='AA:11:00:11:00:11', device=s3)
n.save()
n = NetworkCard(mac='BB:BB:00:11:00:11', device=s4)
n.save()
n = NetworkCard(mac='DD:DD:DD:11:00:11', device=s4)
n.save()
n = NetworkCard(mac='55:55:00:55:00:11', device=s4)
n.save()
