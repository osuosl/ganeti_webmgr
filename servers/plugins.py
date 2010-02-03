from core.plugins.plugin import Plugin
from core.plugins.model_support import ModelView, ModelListView

from models import *


class Devices(Plugin):
    description = 'Provides models and views for tracking.'
    objects = (
        Device,
        NetworkCard,
        ModelView(Device),
        ModelListView(Device)
    )


class Inventory(Plugin):
    description = 'Provides models and views for tracking inventory of a server room.'
    depends = Devices
    objects = (
        Location,
        Rack,
        RackU,
        ModelView(Rack),
        Closet,
        ClosetLocation
    )