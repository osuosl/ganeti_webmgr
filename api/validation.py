__author__ = 'bojan'

from tastypie.validation import Validation, FormValidation
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
import re
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.http import int_to_base36
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import get_current_site
from django.template import Context, loader
from django import forms


class UserValidation(Validation):
    def is_valid(self, bundle, request=None):
        errors = {}
        if not bundle.data:
                return {'Error':'Empty request'}
        request_type = request.META.get('REQUEST_METHOD')
        if  (request_type == 'POST') :
            if bundle.data.has_key('username'):
                if len(bundle.data.get('username')) > 30:
                    errors['username']=['Username should be 30 characters or fewer.']
                if not re.match('^[\w.@+-]+$', bundle.data.get('username')):
                    errors['username']=['Username should contain only letters, numbers and @/./+/-/_ characters.']
            if not bundle.data.has_key('password'):
                    errors['password'] ='Password must be provided'
        elif (request_type == 'PUT'):
            if bundle.data.has_key('username'):
                if len(bundle.data.get('username')) > 30:
                    errors['username']='Username should be 30 characters or fewer.'
                if not re.match('^[\w.@+-]+$', bundle.data.get('username')):
                    errors['username']='Username should contain only letters, numbers and @/./+/-/_ characters.'
        return errors

    