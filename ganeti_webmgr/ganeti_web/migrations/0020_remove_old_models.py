# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):
    depends_on = (
        ("authentication", "0001_initial"),
    )

    def forwards(self, orm):
        pass

    def backwards(self, orm):
        pass

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
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
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'authentication.clusteruser': {
            'Meta': {'object_name': 'ClusterUser'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'real_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"})
        },
        'clusters.cluster': {
            'Meta': {'ordering': "['hostname', 'description']", 'object_name': 'Cluster'},
            'cached': ('ganeti_webmgr.utils.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'disk': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'hash': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'hostname': ('ganeti_webmgr.utils.fields.LowerCaseCharField', [], {'unique': 'True', 'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore_cache': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_job': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'cluster_last_job'", 'null': 'True', 'to': "orm['jobs.Job']"}),
            'mtime': ('ganeti_webmgr.utils.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'password': ('ganeti_webmgr.utils.fields.PatchedEncryptedCharField', [], {'default': "''", 'max_length': '293', 'cipher': "'AES'", 'blank': 'True'}),
            'port': ('django.db.models.fields.PositiveIntegerField', [], {'default': '5080'}),
            'ram': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'serialized_info': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'virtual_cpus': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'ganeti_web.cluster_perms': {
            'Meta': {'object_name': 'Cluster_Perms'},
            'admin': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'create_vm': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'export': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Cluster_gperms'", 'null': 'True', 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'migrate': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'obj': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'operms'", 'to': "orm['clusters.Cluster']"}),
            'replace_disks': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'tags': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Cluster_uperms'", 'null': 'True', 'to': "orm['auth.User']"})
        },
        'ganeti_web.virtualmachine_perms': {
            'Meta': {'object_name': 'VirtualMachine_Perms'},
            'admin': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'VirtualMachine_gperms'", 'null': 'True', 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modify': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'obj': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'operms'", 'to': "orm['virtualmachines.VirtualMachine']"}),
            'power': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'remove': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'tags': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'VirtualMachine_uperms'", 'null': 'True', 'to': "orm['auth.User']"})
        },
        'jobs.job': {
            'Meta': {'object_name': 'Job'},
            'cached': ('ganeti_webmgr.utils.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'cluster': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'to': "orm['clusters.Cluster']"}),
            'cluster_hash': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['contenttypes.ContentType']"}),
            'finished': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore_cache': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'job_id': ('django.db.models.fields.IntegerField', [], {}),
            'mtime': ('ganeti_webmgr.utils.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {}),
            'op': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'serialized_info': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'nodes.node': {
            'Meta': {'object_name': 'Node'},
            'cached': ('ganeti_webmgr.utils.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'cluster': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'nodes'", 'to': "orm['clusters.Cluster']"}),
            'cluster_hash': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'cpus': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'disk_free': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'disk_total': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'hostname': ('ganeti_webmgr.utils.fields.LowerCaseCharField', [], {'unique': 'True', 'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore_cache': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_job': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['jobs.Job']"}),
            'mtime': ('ganeti_webmgr.utils.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'offline': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'ram_free': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'ram_total': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'serialized_info': ('django.db.models.fields.TextField', [], {'default': "''"})
        },
        'virtualmachines.virtualmachine': {
            'Meta': {'ordering': "['hostname']", 'unique_together': "(('cluster', 'hostname'),)", 'object_name': 'VirtualMachine'},
            'cached': ('ganeti_webmgr.utils.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'cluster': ('django.db.models.fields.related.ForeignKey', [], {'default': '0', 'related_name': "'virtual_machines'", 'to': "orm['clusters.Cluster']"}),
            'cluster_hash': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'disk_size': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'hostname': ('ganeti_webmgr.utils.fields.LowerCaseCharField', [], {'max_length': '128', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore_cache': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_job': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['jobs.Job']"}),
            'minram': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'mtime': ('ganeti_webmgr.utils.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'operating_system': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'virtual_machines'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['authentication.ClusterUser']"}),
            'pending_delete': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'primary_node': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'primary_vms'", 'null': 'True', 'to': "orm['nodes.Node']"}),
            'ram': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'secondary_node': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'secondary_vms'", 'null': 'True', 'to': "orm['nodes.Node']"}),
            'serialized_info': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '14'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'instances'", 'null': 'True', 'to': "orm['vm_templates.VirtualMachineTemplate']"}),
            'virtual_cpus': ('django.db.models.fields.IntegerField', [], {'default': '-1'})
        },
        'vm_templates.virtualmachinetemplate': {
            'Meta': {'unique_together': "(('cluster', 'template_name'),)", 'object_name': 'VirtualMachineTemplate'},
            'boot_order': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'cdrom2_image_path': ('django.db.models.fields.CharField', [], {'max_length': '512', 'blank': 'True'}),
            'cdrom_image_path': ('django.db.models.fields.CharField', [], {'max_length': '512', 'blank': 'True'}),
            'cluster': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'templates'", 'null': 'True', 'to': "orm['clusters.Cluster']"}),
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'disk_template': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'disk_type': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'disks': ('django_fields.fields.PickleField', [], {'null': 'True', 'blank': 'True'}),
            'iallocator': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'iallocator_hostname': ('ganeti_webmgr.utils.fields.LowerCaseCharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_check': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'kernel_path': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'memory': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'minmem': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name_check': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'nic_type': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'nics': ('django_fields.fields.PickleField', [], {'null': 'True', 'blank': 'True'}),
            'no_install': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'os': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'pnode': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'root_path': ('django.db.models.fields.CharField', [], {'default': "'/'", 'max_length': '255', 'blank': 'True'}),
            'serial_console': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'snode': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'start': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'template_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'temporary': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'vcpus': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['ganeti_web']
