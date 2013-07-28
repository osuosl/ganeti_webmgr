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


class ResponseMap(object):
    """
    An object that encapsulates return values based on parameters given to the
    called method.

    Return Map should be initialized with a list containing tuples all possible
    arg/kwarg combinations plus the result that should be sent for those args
    """
    def __init__(self, map):
        self.map = map

    def __getitem__(self, key):
        for k, response in self.map:
            if key == k:
                return response
