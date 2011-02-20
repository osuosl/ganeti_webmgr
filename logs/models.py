# Copyright (C) 2010 Oregon State University et al.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.


from django.db import models

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey
from django.db.utils import DatabaseError
from django.template.loader import get_template
from django.template import Context



class LogActionManager(models.Manager):
    _cache = {}
    _DELAYED = []

    def register(self, key, template):
        try:
            return LogAction.objects._register(key, template)
        except DatabaseError:
            # there was an error, likely due to a missing table.  Delay this
            # registration.
            self._DELAYED.append((key, template))
        
    def _register(self, key, template):
        """
        Registers and caches an LogAction type
        
        @param key : Key identifying log action
        @param template : template associated with key
        """
        try:
            action = self.get_from_cache(key)
            action.template = template
            action.save()
        except LogAction.DoesNotExist:
            action, new = LogAction.objects.get_or_create(name=key, \
            template=template)
            self._cache.setdefault(self.db, {})[key] = action
            action.save()
        
        return action
    
    def _register_delayed(**kwargs):
        """
        Register all permissions that were delayed waiting for database tables to
        be created.
        
        Don't call this from outside code.
        """
        try:
            for args in LogActionManager._DELAYED:
                LogAction.objects._register(*args)
            models.signals.post_syncdb.disconnect(LogActionManager._register_delayed)
        except DatabaseError:
            # still waiting for models in other apps to be created
            pass

    models.signals.post_syncdb.connect(_register_delayed)

    def get_from_cache(self, key):
        """
        Attempts to retrieve the LogAction from cache, if it fails, loads
        the action into the cache.
        
        @param key : key passed to LogAction.objects.get
        """
        try:
            action = self._cache[self.db][key]
        except KeyError:
            action = LogAction.objects.get(name=key)
            self._cache.setdefault(self.db, {})[key]=action
        return action


class LogAction(models.Model):
    """
    Type of action of log entry (for example: addition, deletion)

    @param name           string  verb (for example: add)
    """
    
    name = models.CharField(max_length=128, unique=True, primary_key=True)
    template = models.CharField(max_length=128, unique=True)
    objects = LogActionManager()
    
    def __str__(self):
        return 'LogAction: %s Template: %s \n'%(self.name, self.template)
    

class LogItemManager(models.Manager):
    
    # Cache to avoid re-looking up LogAction objects all over the place
    _cache = {}

    # XXX: it doesn't refresh when any LogAction is changed or removed
    def clear_cache(self):
        """
        Clears out all LogAction cached objects
        """
        self.__class__._cache.clear()

    def log_action(self, key, user, object1, object2=None,  object3=None):
        """
        Creates new log entry

        @param user             Profile
        @param affected_object  any model
        @param key              string (LogAction.name)
        """
        # Want to use unicode?
        # Add this at import section of the file
        #from django.utils.encoding import smart_unicode
        # Uncomment below:
        #key = smart_unicode(key)
        dict = {}
        action = LogAction.objects.get_from_cache(key)
        
        dict['action'] = action
        dict['id'] = None
        dict['timestamp'] = None
        dict['user'] = user
        dict['object1'] = object1
        
        if object2 != None:
            dict['object2'] = object2
        
        if object3 != None:
            dict['object3'] = object3

        m = self.model(**dict)
        m.save()
        return m


class LogItem(models.Model):
    """
    Single entry in log
    """
    action = models.ForeignKey(LogAction)
    #action = models.CharField(max_length=128)
    timestamp = models.DateTimeField(auto_now_add=True, )
    user = models.ForeignKey(User, related_name='log_items')
    
    object_type1 = models.ForeignKey(ContentType, \
    related_name='log_items1', null=True)
    object_id1 = models.PositiveIntegerField(null=True)
    object1 = GenericForeignKey("object_type1", "object_id1")
    
    object_type2 = models.ForeignKey(ContentType, \
    related_name='log_items2', null=True)
    object_id2 = models.PositiveIntegerField(null=True)
    object2 = GenericForeignKey("object_type2", "object_id2")
    
    object_type3 = models.ForeignKey(ContentType, \
    related_name='log_items3', null=True)
    object_id3 = models.PositiveIntegerField(null=True)
    object3 = GenericForeignKey("object_type3", "object_id3")

    #log_message = models.TextField(blank=True, null=True)

    objects = LogItemManager()

    class Meta:
        ordering = ("timestamp", )
    
    def get_template(self):
        """
        retrieves template for this log item
        """
        action = LogAction.objects.get_from_cache(self.action_id)
        return get_template(action.template)
        
    def __repr__(self):
        return 'time: %s user: %s object_type1: %s'%(self.timestamp, self.user, self.object_type1)
    
    def __str__(self):
        """
        Renders single line log entry to a string, 
        containing information like:
        - date and extensive time
        - user who performed an action
        - action itself
        - object affected by the action
        """
        action = LogAction.objects.get_from_cache(self.action_id)
        template = get_template(action.template)
        return template.render(Context({"log_item": self}))


#Most common log types, registered by default for convenience
def create_defaults():
    LogAction.objects.register('EDIT', 'object_log/edit.html')
    LogAction.objects.register('CREATE', 'object_log/add.html')
    LogAction.objects.register('DELETE', 'object_log/delete.html')
