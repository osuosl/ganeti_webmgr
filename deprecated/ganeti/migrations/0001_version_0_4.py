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

# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'TestModel'
        db.create_table('ganeti_testmodel', (
            ('cached', self.gf('ganeti_web.fields.PreciseDateTimeField')(null=True, max_digits=18, decimal_places=6)),
            ('ignore_cache', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('serialized_info', self.gf('django.db.models.fields.TextField')(default=None, null=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('mtime', self.gf('ganeti_web.fields.PreciseDateTimeField')(null=True, max_digits=18, decimal_places=6)),
        ))
        db.send_create_signal('ganeti', ['TestModel'])

        # Adding model 'Job'
        db.create_table('ganeti_job', (
            ('status', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('job_id', self.gf('django.db.models.fields.IntegerField')()),
            ('cluster_hash', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('cached', self.gf('ganeti_web.fields.PreciseDateTimeField')(null=True, max_digits=18, decimal_places=6)),
            ('object_id', self.gf('django.db.models.fields.IntegerField')()),
            ('cluster', self.gf('django.db.models.fields.related.ForeignKey')(related_name='jobs', to=orm['ganeti.Cluster'])),
            ('finished', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('ignore_cache', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('mtime', self.gf('ganeti_web.fields.PreciseDateTimeField')(null=True, max_digits=18, decimal_places=6)),
            ('serialized_info', self.gf('django.db.models.fields.TextField')(default=None, null=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('ganeti', ['Job'])

        # Adding model 'VirtualMachine'
        db.create_table('ganeti_virtualmachine', (
            ('status', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('ram', self.gf('django.db.models.fields.IntegerField')(default=-1)),
            ('disk_size', self.gf('django.db.models.fields.IntegerField')(default=-1)),
            ('cluster_hash', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('cached', self.gf('ganeti_web.fields.PreciseDateTimeField')(null=True, max_digits=18, decimal_places=6)),
            ('hostname', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('cluster', self.gf('django.db.models.fields.related.ForeignKey')(related_name='virtual_machines', to=orm['ganeti.Cluster'])),
            ('operating_system', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('last_job', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ganeti.Job'], null=True)),
            ('ignore_cache', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('mtime', self.gf('ganeti_web.fields.PreciseDateTimeField')(null=True, max_digits=18, decimal_places=6)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='virtual_machines', null=True, to=orm['ganeti.ClusterUser'])),
            ('virtual_cpus', self.gf('django.db.models.fields.IntegerField')(default=-1)),
            ('serialized_info', self.gf('django.db.models.fields.TextField')(default=None, null=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('ganeti', ['VirtualMachine'])

        # Adding model 'Cluster'
        db.create_table('ganeti_cluster', (
            ('username', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('disk', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('hash', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('cached', self.gf('ganeti_web.fields.PreciseDateTimeField')(null=True, max_digits=18, decimal_places=6)),
            ('hostname', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('ram', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, db_index=True)),
            ('port', self.gf('django.db.models.fields.PositiveIntegerField')(default=5080)),
            ('ignore_cache', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('mtime', self.gf('ganeti_web.fields.PreciseDateTimeField')(null=True, max_digits=18, decimal_places=6)),
            ('virtual_cpus', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('serialized_info', self.gf('django.db.models.fields.TextField')(default=None, null=True)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('ganeti', ['Cluster'])

        # Adding model 'ClusterUser'
        db.create_table('ganeti_clusteruser', (
            ('real_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal('ganeti', ['ClusterUser'])

        # Adding model 'Profile'
        db.create_table('ganeti_profile', (
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('clusteruser_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['ganeti.ClusterUser'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('ganeti', ['Profile'])

        # Adding model 'Organization'
        db.create_table('ganeti_organization', (
            ('group', self.gf('django.db.models.fields.related.OneToOneField')(related_name='organization', unique=True, to=orm['auth.Group'])),
            ('clusteruser_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['ganeti.ClusterUser'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('ganeti', ['Organization'])

        # Adding model 'Quota'
        db.create_table('ganeti_quota', (
            ('ram', self.gf('django.db.models.fields.IntegerField')(default=0, null=True)),
            ('cluster', self.gf('django.db.models.fields.related.ForeignKey')(related_name='quotas', to=orm['ganeti.Cluster'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='quotas', to=orm['ganeti.ClusterUser'])),
            ('virtual_cpus', self.gf('django.db.models.fields.IntegerField')(default=0, null=True)),
            ('disk', self.gf('django.db.models.fields.IntegerField')(default=0, null=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('ganeti', ['Quota'])

        # Adding model 'SSHKey'
        db.create_table('ganeti_sshkey', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.TextField')()),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal('ganeti', ['SSHKey'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'TestModel'
        db.delete_table('ganeti_testmodel')

        # Deleting model 'Job'
        db.delete_table('ganeti_job')

        # Deleting model 'VirtualMachine'
        db.delete_table('ganeti_virtualmachine')

        # Deleting model 'Cluster'
        db.delete_table('ganeti_cluster')

        # Deleting model 'ClusterUser'
        db.delete_table('ganeti_clusteruser')

        # Deleting model 'Profile'
        db.delete_table('ganeti_profile')

        # Deleting model 'Organization'
        db.delete_table('ganeti_organization')

        # Deleting model 'Quota'
        db.delete_table('ganeti_quota')

        # Deleting model 'SSHKey'
        db.delete_table('ganeti_sshkey')
    
    
    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'ganeti.cluster': {
            'Meta': {'object_name': 'Cluster'},
            'cached': ('ganeti_web.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'disk': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'hash': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'hostname': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore_cache': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'mtime': ('ganeti_web.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'port': ('django.db.models.fields.PositiveIntegerField', [], {'default': '5080'}),
            'ram': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'serialized_info': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'virtual_cpus': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'ganeti.clusteruser': {
            'Meta': {'object_name': 'ClusterUser'},
            'clusters': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'users'", 'symmetrical': 'False', 'through': "orm['ganeti.Quota']", 'to': "orm['ganeti.Cluster']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'real_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True'})
        },
        'ganeti.job': {
            'Meta': {'object_name': 'Job'},
            'cached': ('ganeti_web.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'cluster': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'to': "orm['ganeti.Cluster']"}),
            'cluster_hash': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'finished': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore_cache': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'job_id': ('django.db.models.fields.IntegerField', [], {}),
            'mtime': ('ganeti_web.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {}),
            'serialized_info': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'ganeti.organization': {
            'Meta': {'object_name': 'Organization', '_ormbases': ['ganeti.ClusterUser']},
            'clusteruser_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['ganeti.ClusterUser']", 'unique': 'True', 'primary_key': 'True'}),
            'group': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'organization'", 'unique': 'True', 'to': "orm['auth.Group']"})
        },
        'ganeti.profile': {
            'Meta': {'object_name': 'Profile', '_ormbases': ['ganeti.ClusterUser']},
            'clusteruser_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['ganeti.ClusterUser']", 'unique': 'True', 'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'ganeti.quota': {
            'Meta': {'object_name': 'Quota'},
            'cluster': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'quotas'", 'to': "orm['ganeti.Cluster']"}),
            'disk': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ram': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'quotas'", 'to': "orm['ganeti.ClusterUser']"}),
            'virtual_cpus': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True'})
        },
        'ganeti.sshkey': {
            'Meta': {'object_name': 'SSHKey'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.TextField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'ganeti.testmodel': {
            'Meta': {'object_name': 'TestModel'},
            'cached': ('ganeti_web.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore_cache': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'mtime': ('ganeti_web.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'serialized_info': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'})
        },
        'ganeti.virtualmachine': {
            'Meta': {'object_name': 'VirtualMachine'},
            'cached': ('ganeti_web.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'cluster': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'virtual_machines'", 'to': "orm['ganeti.Cluster']"}),
            'cluster_hash': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'disk_size': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'hostname': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore_cache': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_job': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ganeti.Job']", 'null': 'True'}),
            'mtime': ('ganeti_web.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'operating_system': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'virtual_machines'", 'null': 'True', 'to': "orm['ganeti.ClusterUser']"}),
            'ram': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'serialized_info': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'virtual_cpus': ('django.db.models.fields.IntegerField', [], {'default': '-1'})
        }
    }
    
    complete_apps = ['ganeti']
