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


from django.contrib import admin
from models import *


class QuotaInline(admin.TabularInline):
    model = Quota
    extra = 1

class ClusterAdmin(admin.ModelAdmin):
    inlines = [QuotaInline]

class ProfileAdmin(admin.ModelAdmin):
    inlines = [QuotaInline]

class OrganizationAdmin(admin.ModelAdmin):
    inlines = [QuotaInline]

admin.site.register(Cluster, ClusterAdmin)
admin.site.register(VirtualMachine)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Profile, ProfileAdmin)
