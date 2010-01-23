from core.plugins.plugins import Plugin
from core.plugins.view import GenericView

from models import Closet, Device, Location, NetworkCard, Rack


class Devices(Plugin):
    register = (
        Device,
        NetworkCard,
        GenericView(Device)
    )

class Inventory(Plugin):
    depends = Devices
    register = (
        Location,
        Rack,
        GenericView(Rack),
        Closet
    )