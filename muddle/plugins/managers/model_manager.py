from django.db.models.base import ModelBase

from muddle.plugins.managers.type_manager import ObjectType, TypeManager
from muddle.plugins.models.wrapper import ModelWrapper
from muddle.plugins.plugin_manager import PluginManager
from muddle.plugins.plugin import Plugin


class ModelManager(Plugin, PluginManager):
    """
    Manager for tracking enabled models
    """
    depends = TypeManager
    description = 'Manages enabled models'
    objects = (ObjectType(ModelBase, ModelWrapper))
    
    def __init__(self, *args, **kwargs):
        Plugin.__init__(self, *args, **kwargs)
        PluginManager.__init__(self)