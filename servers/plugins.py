from core.plugins.plugins import Plugin
from core.plugins.view import GenericView

from models import Closet, Device, Location, NetworkCard, Rack


class Devices(Plugin):
    description = 'Provides models and views for tracking.'
    objects = (
        Device,
        NetworkCard,
        GenericView(Device)
    )


class Inventory(Plugin):
    description = 'Provides models and views for tracking inventory of a server room.'
    depends = Devices
    objects = (
        Location,
        Rack,
        GenericView(Rack),
        Closet
    )