from django.contrib.auth.models import User, Group
from django.db import models


# Patch User model to add url lookup
@models.permalink
def get_absolute_url(self):
    return 'user-detail', (), {'user_id':self.pk}
User.get_absolute_url = get_absolute_url


# Patch Group model to add URL lookup
@models.permalink
def get_absolute_url(self):
    return 'group-detail', (), {'id':self.pk}
Group.get_absolute_url = get_absolute_url