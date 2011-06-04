# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding index on 'VirtualMachine', fields ['hostname']
        db.create_index('ganeti_virtualmachine', ['hostname'])
    
    
    def backwards(self, orm):
        
        # Removing index on 'VirtualMachine', fields ['hostname']
        db.delete_index('ganeti_virtualmachine', ['hostname'])
    
    
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
            'cached': ('ganeti.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'disk': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'hash': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'hostname': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore_cache': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_job': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'cluster_last_job'", 'null': 'True', 'to': "orm['ganeti.Job']"}),
            'mtime': ('ganeti.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'real_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True'})
        },
        'ganeti.ganetierror': {
            'Meta': {'object_name': 'GanetiError'},
            'cleared': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'cluster': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ganeti.Cluster']"}),
            'code': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'msg': ('django.db.models.fields.TextField', [], {}),
            'obj_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'obj_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ganeti_errors'", 'to': "orm['contenttypes.ContentType']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'ganeti.job': {
            'Meta': {'object_name': 'Job'},
            'cached': ('ganeti.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'cleared': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'cluster': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'to': "orm['ganeti.Cluster']"}),
            'cluster_hash': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'finished': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore_cache': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'job_id': ('django.db.models.fields.IntegerField', [], {}),
            'mtime': ('ganeti.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {}),
            'serialized_info': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'ganeti.node': {
            'Meta': {'object_name': 'Node'},
            'cached': ('ganeti.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'cluster': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'nodes'", 'to': "orm['ganeti.Cluster']"}),
            'cluster_hash': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'disk_total': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'hostname': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore_cache': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_job': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ganeti.Job']", 'null': 'True'}),
            'mtime': ('ganeti.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'offline': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'ram_total': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'serialized_info': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'})
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
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ssh_keys'", 'to': "orm['auth.User']"})
        },
        'ganeti.testmodel': {
            'Meta': {'object_name': 'TestModel'},
            'cached': ('ganeti.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'cluster': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ganeti.Cluster']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore_cache': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'mtime': ('ganeti.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'serialized_info': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'})
        },
        'ganeti.virtualmachine': {
            'Meta': {'unique_together': "(('cluster', 'hostname'),)", 'object_name': 'VirtualMachine'},
            'cached': ('ganeti.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'cluster': ('django.db.models.fields.related.ForeignKey', [], {'default': '0', 'related_name': "'virtual_machines'", 'to': "orm['ganeti.Cluster']"}),
            'cluster_hash': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'disk_size': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'hostname': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore_cache': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_job': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ganeti.Job']", 'null': 'True'}),
            'mtime': ('ganeti.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'operating_system': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'virtual_machines'", 'null': 'True', 'to': "orm['ganeti.ClusterUser']"}),
            'pending_delete': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'primary_node': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'primary_vms'", 'null': 'True', 'to': "orm['ganeti.Node']"}),
            'ram': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'secondary_node': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'secondary_vms'", 'null': 'True', 'to': "orm['ganeti.Node']"}),
            'serialized_info': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ganeti.VirtualMachineTemplate']", 'null': 'True'}),
            'virtual_cpus': ('django.db.models.fields.IntegerField', [], {'default': '-1'})
        },
        'ganeti.virtualmachinetemplate': {
            'Meta': {'object_name': 'VirtualMachineTemplate'},
            'boot_order': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'cdrom_image_path': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'cluster': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ganeti.Cluster']", 'null': 'True'}),
            'disk_size': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'disk_template': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'disk_type': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'iallocator': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'iallocator_hostname': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kernel_path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'memory': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name_check': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'nic_link': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'nic_mode': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'nic_type': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'os': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'pnode': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'root_path': ('django.db.models.fields.CharField', [], {'default': "'/'", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'serial_console': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'snode': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'template_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'vcpus': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }
    
    complete_apps = ['ganeti']
