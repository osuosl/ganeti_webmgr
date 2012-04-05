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

from datetime import datetime
from decimal import Decimal
import time
import re

from django.core.exceptions import ValidationError
from django.core.validators import (EMPTY_VALUES, MaxValueValidator,
                                    MinValueValidator)
from django.db import models
from django.db.models.fields import DecimalField
from django.forms.fields import CharField, RegexField
from django.utils.translation import ugettext as _

from south.modelsinspector import add_introspection_rules

from django_fields.fields import EncryptedCharField

class PatchedEncryptedCharField(EncryptedCharField):
    """
    django_fields upstream refuses to fix a bug, so we get to do it ourselves.

    Feel free to destroy this class and switch back to upstream if
    https://github.com/svetlyak40wt/django-fields/pull/12 is ever merged into
    a released version of django_fields.
    """

    def get_db_prep_value(self, value, connection=None, prepared=False):
        if value is None:
            return None

        return EncryptedCharField.get_db_prep_value(self, value,
                                                    connection=connection,
                                                    prepared=prepared)


add_introspection_rules([], ["^ganeti_web\.fields\.PatchedEncryptedCharField"])


class PreciseDateTimeField(DecimalField):
    """
    Custom model field for dealing with timestamps requiring precision greater
    than seconds.  MySQL and other databases follow the SQL92 standard:

        TIMESTAMP - contains the datetime field's YEAR, MONTH, DAY, HOUR,
                    MINUTE, and SECOND.

    To support greater precisions this class will convert to and from a decimal
    field.  There are issues dealing with this due to timezones, different
    epochs, etc., but the alternative is using a string field to store the
    values.

    By default this field will support 6 decimal places (microsceonds), but it
    can be adjusted by adding the decimal_places kwarg.

    By default this field will support up decimal_places+12 total digits.  This
    can be adjusted by including the max_digits kwarg.  max_digits must include
    the total of both second and microsecond digits.
    """

    __metaclass__ = models.SubfieldBase

    def __init__(self, **kwargs):
        # XXX set default values.  doing this here rather than as kwargs
        # because default ordering of DecimalField.__init__ may be different
        if not 'decimal_places' in kwargs:
            kwargs['decimal_places'] = 6
        if not 'max_digits' in kwargs:
            kwargs['max_digits'] = kwargs['decimal_places'] + 12

        self.shifter = 10.0**kwargs['decimal_places']

        super(PreciseDateTimeField, self).__init__(**kwargs)

    def to_python(self, value):
        """
        convert decimal value to a datetime
        """
        if not value:
            return None
        if isinstance(value, (datetime,)):
            return value
        if isinstance(value, (Decimal, str, unicode)):
            value = float(value)
        if isinstance(value, (float,)):
            return datetime.fromtimestamp(value)

        raise ValidationError(_('Unable to convert %s to datetime.') % value)

    def get_db_prep_value(self, value, connection, prepared=False):
        if value:
            return time.mktime(value.timetuple()) + value.microsecond/(10**self.decimal_places)
        return None

    def get_db_prep_save(self, value, connection):
        if value:
            if isinstance(value, (datetime,)):
                return Decimal('%f' % (time.mktime(value.timetuple()) + value.microsecond/self.shifter))

            if isinstance(value, (float,)):
                return Decimal(float)

            if isinstance(value, (Decimal,)):
                return value

        return None

    def db_type(self, connection):
        # We used to care about which engine went here, but after some
        # testing, it turns out that it just doesn't fucking matter which
        # engine is being used; My, Pg and SQLite all respect the fuck out of
        # NUMERIC.

        return "NUMERIC(%d, %d)" % (self.max_digits, self.decimal_places)


# Migration rules for PDTField. PDTField's serialization is surprisingly
# straightforward and doesn't need any help here.
add_introspection_rules([], ["^ganeti_web\.fields\.PreciseDateTimeField"])


class DataVolumeField(CharField):
    min_value = None
    max_value = None

    def __init__(self, min_value=None, max_value=None, **kwargs):
        super(DataVolumeField, self).__init__(**kwargs)
        if min_value:
            self.validators.append(MinValueValidator(min_value))
        if max_value:
            self.validators.append(MaxValueValidator(max_value))

    def to_python(self, value):
        """
        Turn a bytecount into an integer, in megabytes.

        XXX looks like it's actually mebibytes
        XXX this should handle the SI base2 versions as well (MiB, GiB, etc.)
        XXX should round up to the next megabyte?
        """

        if value in EMPTY_VALUES:
            return None

        # Make a not-unreasonable attempt to pass through numbers which don't
        # need the formatting.
        try:
            return int(value)
        except ValueError:
            pass

        try:
            return int(float(value))
        except ValueError:
            pass

        value = str(value).upper().strip()

        if not value:
            return None

        matches = re.match(r'([0-9]+(?:\.[0-9]+)?)\s*(M|G|T|MB|GB|TB)?$', value)
        if matches == None:
            raise ValidationError(_('Invalid format.'))

        multiplier = 1
        unit = matches.group(2)
        if unit != None:
            unit = unit[0]
            if unit == 'M':
                multiplier = 1
            elif unit == 'G':
                multiplier = 1024
            elif unit == 'T':
                multiplier = 1024 * 1024

        intvalue = int(float(matches.group(1)) * multiplier)
        return intvalue


# Migration rules for DVField. DVField doesn't do anything fancy, so the
# default rules will work.
add_introspection_rules([], ["^ganeti_web\.fields\.DataVolumeField"])


class MACAddressField(RegexField):
    """
    Form field that validates MAC Addresses.
    """

    def __init__(self, *args, **kwargs):
        kwargs["regex"] = '^([0-9A-Fa-f]{2}([:-]|$)){6}$'
        super(MACAddressField, self).__init__(*args, **kwargs)


# Migration rules for MAField. MAField doesn't do anything fancy, so the
# default rules will work.
add_introspection_rules([], ["^ganeti_web\.fields\.MACAddressField"])


class SQLSumIf(models.sql.aggregates.Aggregate):
    is_ordinal = True
    sql_function = 'SUM'
    # XXX not all databases treat 1 and True the same, or have True. Use the
    # expression 1=1 which always evaluates true with a value compatible with
    # the database.
    sql_template= "%(function)s(CASE %(condition)s WHEN 1=1 THEN %(field)s ELSE NULL END)"


class SumIf(models.Aggregate):
    name = 'SUM'

    def add_to_query(self, query, alias, col, source, is_summary):
        aggregate = SQLSumIf(col, source=source, is_summary=is_summary, **self.extra)
        query.aggregates[alias] = aggregate
