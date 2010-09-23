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
